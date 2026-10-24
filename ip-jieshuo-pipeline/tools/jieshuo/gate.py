#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-jieshuo-pipeline 投喂层闸门（gate）
对标「投喂层闸门」：在把旁白稿/素材匹配表喂给剪辑工具之前，过三道闸门，
防止把「未对齐、缺素材、缺提示词」的半成品投进去。

用法：
    python gate.py vo.json assets.json prompts.json [validate_report.json]
"""

import json
import sys


def gate_1_aligned(vo, assets):
    """闸门1：四份文件段落对齐（旁白稿/素材匹配表 id 一致）"""
    vo_ids = {s.get("id") for s in vo.get("segments", [])}
    asset_ids = {a.get("id") for a in assets.get("segments", [])}
    if vo_ids != asset_ids:
        missing = vo_ids - asset_ids
        extra = asset_ids - vo_ids
        msg = []
        if missing:
            msg.append(f"素材匹配表缺段落 {', '.join(sorted(missing))}")
        if extra:
            msg.append(f"素材匹配表多出段落 {', '.join(sorted(extra))}")
        return False, "；".join(msg)
    return True, ""


def gate_2_prompt_built(prompts):
    """闸门2：成片提示词已组装（每段两段式齐全）"""
    if not prompts:
        return False, "缺成片提示词"
    for p in prompts:
        # 精确读 prompt 字段（而非 str(p) 隐式序列化），避免误判
        txt = p.get("prompt", "") if isinstance(p, dict) else str(p)
        if "【画面】" not in txt or "【字幕】" not in txt:
            return False, f"提示词 {p.get('id')} 缺【画面】或【字幕】段"
    return True, ""


def gate_3_validate_passed(report):
    """闸门3：质检已过（P0 无错误）"""
    if report.get("P0"):
        return False, f"质检 P0 未过，{len(report['P0'])} 个错误"
    return True, ""


GATES = [
    ("闸门1·段落对齐", gate_1_aligned),
    ("闸门2·提示词组装", gate_2_prompt_built),
    ("闸门3·质检通过", gate_3_validate_passed),
]


def run_gates(vo, assets, prompts, report):
    results = []
    all_pass = True
    for name, func in GATES:
        if name == "闸门1·段落对齐":
            ok, msg = func(vo, assets)
        elif name == "闸门2·提示词组装":
            ok, msg = func(prompts)
        else:
            ok, msg = func(report)
        results.append({"gate": name, "pass": ok, "msg": msg})
        if not ok:
            all_pass = False
    return all_pass, results


def main():
    if len(sys.argv) < 4:
        print("用法: python gate.py vo.json assets.json prompts.json [validate_report.json]")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        vo = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        assets = json.load(f)
    with open(sys.argv[3], encoding="utf-8") as f:
        prompts = json.load(f)
    report = {"P0": []}
    if len(sys.argv) >= 5:
        with open(sys.argv[4], encoding="utf-8") as f:
            report = json.load(f)

    all_pass, results = run_gates(vo, assets, prompts, report)
    print("=" * 50)
    print("投喂层三道闸门")
    print("=" * 50)
    for r in results:
        mark = "✅" if r["pass"] else "❌"
        print(f"{mark} {r['gate']}: {r['msg'] or '通过'}")
    print("=" * 50)
    print("结论:", "✅ 全部闸门通过，可投喂" if all_pass else "❌ 有闸门未过，禁止投喂")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
