#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-jieshuo-pipeline 旁白稿质检（validate）
对标「机械检查优先」：把旁白稿过 V1~V8 检查码，拦下超时/违禁词/段落不对齐/版权缺失等低级错误。

检查码：
    V1 结构完整（title/type/duration/rate/segments 齐全）
    V2 语速超时（总字数 ÷ 语速 ≤ 总时长）
    V3 段落对齐（id 唯一且为 Vxx 格式，逐段连续）
    V4 字段完整（每段 narration/visual_hint/subtitle_main 非空；版权字段归素材匹配表，不在此校验）
    V5 字数准确（chars 与 narration 实际字数一致）
    V6 违禁词（绝对化/虚假功效/迷信伪科学）
    V7 版权缺失（需授权素材缺 license_note）
    V8 字幕漂移（subtitle_main 与 narration 不一致 / emph 不是子串）

用法：
    python validate.py vo.json [--json] [--lang zh]
"""

import json
import re
import sys
import argparse

# 违禁词（绝对化 + 虚假功效 + 迷信伪科学），解说场景裁剪
BANNED = [
    "最好", "第一", "顶级", "唯一", "100%", "国家级", "世界之最", "史上最强",
    "根治", "包治", "特效药", "长生不老", "百病不侵",
    "转运", "改命", "灵丹", "开光",
]


def count_chars(text):
    """按中文字数统计（去空白、去标点）"""
    text = re.sub(r"\s+", "", text or "")
    # 只统计中文字符 + 数字 + 英文字母（旁白主要是中文，兼容数字/英文词）
    return len(re.findall(r"[\u4e00-\u9fff0-9A-Za-z]", text))


def v1_structure(vo):
    errors = []
    for field in ("title", "type", "duration", "rate", "segments"):
        if not vo.get(field):
            errors.append(f"顶层缺字段 {field}")
    if not isinstance(vo.get("segments"), list) or not vo["segments"]:
        errors.append("segments 为空或非列表")
    return errors


def v2_rate_timeout(vo):
    errors = []
    total = sum(count_chars(s.get("narration", "")) for s in vo.get("segments", []))
    rate = float(vo.get("rate", 5.0))
    duration = float(vo.get("duration", 0))
    if rate <= 0 or duration <= 0:
        return ["rate 或 duration 非法"]
    need = total / rate
    if need > duration:
        errors.append(f"语速超时：总字数 {total} ÷ 语速 {rate} = {need:.1f}s > 时长 {duration}s，需删 {total - int(rate * duration)} 字或加时长")
    return errors


def v3_segment_align(vo):
    errors = []
    ids = [s.get("id", "") for s in vo.get("segments", [])]
    if len(ids) != len(set(ids)):
        errors.append("段落号 id 重复")
    for i, sid in enumerate(ids):
        expect = f"V{i+1:02d}"
        if not re.fullmatch(r"V\d{2}", sid or ""):
            errors.append(f"第{i+1}段 id「{sid}」格式错误（应为 Vxx）")
        elif sid != expect:
            errors.append(f"第{i+1}段 id「{sid}」应为「{expect}」")
    return errors


def v4_field_complete(vo):
    errors = []
    for s in vo.get("segments", []):
        for field in ("narration", "visual_hint", "subtitle_main"):
            if not (s.get(field) or "").strip():
                errors.append(f"{s.get('id')} 缺字段 {field}")
    return errors


def v5_char_count(vo):
    errors = []
    for s in vo.get("segments", []):
        actual = count_chars(s.get("narration", ""))
        declared = s.get("chars")
        if declared is not None and int(declared) != actual:
            errors.append(f"{s.get('id')} 字数不符：声明 {declared}，实际 {actual}")
    return errors


def v6_banned_words(vo):
    errors = []
    for s in vo.get("segments", []):
        text = s.get("narration", "") + (s.get("subtitle_main", "") or "")
        for w in BANNED:
            if w in text:
                errors.append(f"{s.get('id')} 含违禁词「{w}」")
    return errors


def v7_copyright(vo, assets):
    errors = []
    asset_map = {a.get("id"): a for a in (assets or {}).get("segments", [])}
    for s in vo.get("segments", []):
        a = asset_map.get(s.get("id"))
        if a and a.get("copyright") == "需授权" and not (a.get("license_note") or "").strip():
            errors.append(f"{s.get('id')} 素材「需授权」但缺 license_note")
    return errors


def v8_subtitle_drift(vo):
    errors = []
    for s in vo.get("segments", []):
        main = (s.get("subtitle_main") or "").strip()
        nar = (s.get("narration") or "").strip()
        # 主字幕应与旁白一致（去标点/空白后比对核心文字）
        if main and nar and re.sub(r"[，。！？、：；,.!?:\s]", "", main) != re.sub(r"[，。！？、：；,.!?:\s]", "", nar):
            errors.append(f"{s.get('id')} 主字幕与旁白不一致")
        emph = (s.get("subtitle_emph") or "").strip()
        if emph and emph not in nar:
            errors.append(f"{s.get('id')} 强调字幕「{emph}」不是旁白子串")
    return errors


def run_validate(vo, assets=None):
    """返回 (报告 dict)"""
    checks = [
        ("V1 结构完整", v1_structure(vo)),
        ("V2 语速超时", v2_rate_timeout(vo)),
        ("V3 段落对齐", v3_segment_align(vo)),
        ("V4 字段完整", v4_field_complete(vo)),
        ("V5 字数准确", v5_char_count(vo)),
        ("V6 违禁词", v6_banned_words(vo)),
        ("V7 版权缺失", v7_copyright(vo, assets)),
        ("V8 字幕漂移", v8_subtitle_drift(vo)),
    ]
    report = {"checks": [], "P0": [], "P1": [], "P2": []}
    for name, errors in checks:
        report["checks"].append({"check": name, "errors": errors})
        if errors:
            # V1~V6 为 P0（硬错误），V7/V8 为 P1（警告级）
            if name.startswith(("V1", "V2", "V3", "V4", "V5", "V6")):
                report["P0"].extend([f"{name}: {e}" for e in errors])
            else:
                report["P1"].extend([f"{name}: {e}" for e in errors])
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("vo", help="旁白稿 JSON")
    p.add_argument("assets", nargs="?", default=None, help="素材匹配表 JSON（可选，V7 用）")
    p.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = p.parse_args()

    with open(args.vo, encoding="utf-8") as f:
        vo = json.load(f)
    assets = None
    if args.assets:
        with open(args.assets, encoding="utf-8") as f:
            assets = json.load(f)

    report = run_validate(vo, assets)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=" * 50)
    print("旁白稿质检（V1~V8）")
    print("=" * 50)
    for c in report["checks"]:
        mark = "✅" if not c["errors"] else "❌"
        print(f"{mark} {c['check']}")
        for e in c["errors"]:
            print(f"     - {e}")
    print("=" * 50)
    print(f"P0（硬错误）: {len(report['P0'])} 条")
    print(f"P1（警告）: {len(report['P1'])} 条")
    if report["P0"]:
        print("结论: ❌ P0 未清零，禁止进入素材匹配")
        sys.exit(1)
    print("结论: ✅ P0 通过")


if __name__ == "__main__":
    main()
