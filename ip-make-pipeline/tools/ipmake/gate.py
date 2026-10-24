#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 投喂层闸门（gate）
对标「投喂层六道闸门」：在把剧本/三件套喂给生成工具之前，先过六道闸门，
防止把「未绑定资产、未锁站位、缺提示词」的半成品投进去浪费算力。

用法：
    python gate.py storyboard.json prompt.json [validate_report.json]
"""

import json
import sys
import re


def gate_1_asset_bound(storyboard):
    """闸门1：资产已绑定（分镜人物/场景/道具都有编号）"""
    shots = storyboard.get("shots", [])
    for s in shots:
        for field in ("characters", "scene", "props"):
            val = s.get(field, "") or ""
            if val and not any(p in val for p in ("P", "S", "D", "V")):
                return False, f"镜{s.get('shot_id')} 的 {field} 未绑定资产编号"
    return True, ""


def gate_2_staging_locked(storyboard):
    """闸门2：站位已锁（分镜表有站位声明）"""
    if not storyboard.get("staging"):
        return False, "缺站位声明（多人戏必填）"
    return True, ""


def gate_3_prompt_built(prompts):
    """闸门3：提示词已组装（七段式齐全）

    七段（对齐 prompt_build.py 的 order）：画风风格/场景资产/核心人物/站位声明/时间轴分镜/音效/强制禁止项。
    站位声明段在无多人戏时可空、音效段恒有默认值，但七段段名都应出现（即便内容为空也保留段名，便于下游核对）。
    """
    if not prompts:
        return False, "缺成片提示词"
    SEGS = ("画风风格", "场景资产", "核心人物", "站位声明", "时间轴分镜", "音效", "强制禁止项")
    for p in prompts:
        # 精确读 prompt 字段（而非 str(p) 隐式序列化），避免误判
        txt = p.get("prompt", "") if isinstance(p, dict) else str(p)
        for seg in SEGS:
            if seg not in txt:
                return False, f"提示词 {p.get('shot_id') if isinstance(p, dict) else ''} 缺【{seg}】段"
    return True, ""


def gate_4_face_anchored(storyboard):
    """闸门4：人脸已锚定（每个出场角色编号都在分镜表里有 face_anchor）

    检查逻辑：扫分镜表所有镜头，凡 characters 里出现的 Pxx 编号，
    必须至少在某镜的 face_anchor 里有对应锚定描述（防换脸的地基）。
    """
    shots = storyboard.get("shots", [])
    referenced = set()   # 所有被引用的角色编号
    anchored = set()     # 所有在 face_anchor 里出现过的角色编号
    for s in shots:
        chars = s.get("characters", "") or ""
        for m in re.findall(r"(P\d{2})", chars):
            referenced.add(m)
        anchor = s.get("face_anchor", "") or ""
        for m in re.findall(r"(P\d{2})", anchor):
            anchored.add(m)
    missing = referenced - anchored
    if missing:
        return False, f"角色 {', '.join(sorted(missing))} 出场但未在 face_anchor 锚定定妆单"
    return True, ""


def gate_5_compliance_checked(storyboard):
    """闸门5：合规已查（无违禁词/绝对化，中英双语）"""
    banned = ["最好", "第一", "顶级", "神器", "根治", "100%", "秒杀", "国家级",
              "best in the world", "number one", "miracle cure", "guaranteed cure", "100% cure"]
    text = json.dumps(storyboard, ensure_ascii=False)
    for w in banned:
        if w in text:
            return False, f"含违禁词：{w}"
    return True, ""


def gate_6_validate_passed(report):
    """闸门6：质检已过（P0 无错误）"""
    if report.get("P0"):
        return False, f"质检 P0 未过，{len(report['P0'])} 个错误"
    return True, ""


GATES = [
    ("闸门1·资产绑定", gate_1_asset_bound),
    ("闸门2·站位锁定", gate_2_staging_locked),
    ("闸门3·提示词组装", gate_3_prompt_built),
    ("闸门4·人脸锚定", gate_4_face_anchored),
    ("闸门5·合规检查", gate_5_compliance_checked),
    ("闸门6·质检通过", gate_6_validate_passed),
]


def run_gates(storyboard, prompts, report):
    results = []
    all_pass = True
    for name, func in GATES:
        if name == "闸门3·提示词组装":
            ok, msg = func(prompts)
        elif name == "闸门4·人脸锚定":
            ok, msg = func(storyboard)
        elif name == "闸门6·质检通过":
            ok, msg = func(report)
        else:
            ok, msg = func(storyboard)
        results.append({"gate": name, "pass": ok, "msg": msg})
        if not ok:
            all_pass = False
    return all_pass, results


def main():
    if len(sys.argv) < 3:
        print("用法: python gate.py storyboard.json prompt.json [validate_report.json]")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        storyboard = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        prompts = json.load(f)
    report = {"P0": []}
    if len(sys.argv) >= 4:
        with open(sys.argv[3], encoding="utf-8") as f:
            report = json.load(f)
    all_pass, results = run_gates(storyboard, prompts, report)
    print("=" * 50)
    print("投喂层六道闸门")
    print("=" * 50)
    for r in results:
        mark = "✅" if r["pass"] else "❌"
        print(f"{mark} {r['gate']}: {r['msg'] or '通过'}")
    print("=" * 50)
    print("结论:", "✅ 全部闸门通过，可投喂" if all_pass else "❌ 有闸门未过，禁止投喂")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
