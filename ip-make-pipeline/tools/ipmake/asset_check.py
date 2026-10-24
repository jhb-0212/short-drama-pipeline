#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 资产台账质检脚本（阶段① 资产绑定）
对标 asset-binding.md：校验资产台账本身 + 台账与分镜的交叉一致性。

两个子命令：
    check   校验资产台账（编号唯一、前缀合法、A/B/C 分级合规、字段齐全）
    cross   交叉校验：分镜引用的每个编号必须存在于台账，台账 A 级资产必须有面部分级

用法：
    python asset_check.py check assets.json
    python asset_check.py cross assets.json storyboard.json
"""

import json
import sys
import re

# 合法资产前缀
PREFIXES = ("P", "S", "D", "V")
# 合法分级
LEVELS = ("A", "B", "C")


def _asset_id(s):
    """从 key 提取「前缀+编号」，如 P01、S03、P01-A"""
    m = re.match(r"^([PSDV])(\d{2})(-[A-Z])?$", s)
    if m:
        return m.group(1), m.group(2), m.group(3) or ""
    return None, None, None


def check_ledger(assets):
    """校验资产台账本身，返回 (errors, warnings)"""
    errors = []
    warnings = []
    keys = [k for k in assets.keys() if _asset_id(k)[0] is not None]

    # 1. 编号唯一性
    seen = {}
    for k in keys:
        pfx, num, sub = _asset_id(k)
        base = f"{pfx}{num}"
        if base in seen:
            errors.append(f"编号重复：{k} 与 {seen[base]} 主编号冲突")
        seen[base] = k

    # 2. 前缀合法
    for k in keys:
        pfx, _, _ = _asset_id(k)
        if pfx not in PREFIXES:
            errors.append(f"非法前缀：{k}")

    # 3. 字段齐全 + 分级合规
    for k in keys:
        v = assets.get(k, {})
        if not isinstance(v, dict):
            errors.append(f"资产 {k} 值应为对象，实际 {type(v).__name__}")
            continue
        if not v.get("name"):
            errors.append(f"资产 {k} 缺 name 字段")
        level = v.get("level")
        if level is None:
            errors.append(f"资产 {k} 缺 level 分级（A/B/C）")
        elif level not in LEVELS:
            errors.append(f"资产 {k} 分级「{level}」非法，应为 A/B/C")
        # 人物资产（P 前缀）必须有人脸描述，防换脸依赖它
        pfx, _, _ = _asset_id(k)
        if pfx == "P" and not v.get("face"):
            warnings.append(f"人物资产 {k} 缺 face 面部描述（C06 防换脸依赖此字段）")

    # 4. A 级资产检查：人物必须有 face，道具必须有纹路/材质描述
    for k in keys:
        v = assets.get(k, {})
        pfx, _, _ = _asset_id(k)
        if v.get("level") == "A":
            if pfx == "P" and not v.get("face"):
                errors.append(f"A 级人物 {k} 必须有 face 面部描述（满配要求）")
            if pfx == "D" and not (v.get("texture") or v.get("detail")):
                warnings.append(f"A 级道具 {k} 建议补 texture/detail（关键道具纹路须精确）")

    # 5. style 字段检查（可选但推荐）
    if "style" in assets and assets["style"]:
        st = assets["style"]
        for f in ("visual", "tone", "light", "sound"):
            if not st.get(f):
                warnings.append(f"style 缺 {f} 字段（七段式提示词①⑥段依赖）")

    return errors, warnings


def check_cross(assets, storyboard):
    """交叉校验：分镜引用的编号必须存在于台账"""
    errors = []
    warnings = []
    ledger_ids = {k for k in assets.keys() if _asset_id(k)[0] is not None}
    shots = storyboard.get("shots", [])

    # 收集分镜引用的所有编号
    refs = set()
    for i, s in enumerate(shots):
        for field in ("characters", "scene", "props"):
            val = s.get(field, "") or ""
            for m in re.finditer(r"([PSDV]\d{2})", val):
                refs.add(m.group(1))

    # 未定义的编号
    for r in sorted(refs):
        if r not in ledger_ids and not any(r + "-" in lid for lid in ledger_ids):
            errors.append(f"分镜引用了台账中不存在的编号：{r}")

    # 台账中定义了但分镜未引用的（可能遗漏或冗余，仅提示）
    for lid in sorted(ledger_ids):
        base = re.sub(r"-[A-Z]$", "", lid)
        if base not in refs and lid not in refs:
            warnings.append(f"台账资产 {lid} 未被任何分镜引用（可能是遗漏或冗余）")

    return errors, warnings


def _print(title, items, mark):
    if items:
        print(f"\n--- {title} ({len(items)}) ---")
        for it in items:
            print(f"  {mark} {it}")


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python asset_check.py check assets.json")
        print("  python asset_check.py cross assets.json storyboard.json")
        sys.exit(2)

    cmd = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        assets = json.load(f)

    if cmd == "check":
        errors, warnings = check_ledger(assets)
        print("=" * 50)
        print("资产台账质检（阶段①）")
        print("=" * 50)
        _print("错误（必须修）", errors, "❌")
        _print("警告（建议修）", warnings, "⚠️")
        print("=" * 50)
        print("结论:", "❌ 台账不合格" if errors else "✅ 台账合格")
        sys.exit(1 if errors else 0)

    elif cmd == "cross":
        if len(sys.argv) < 4:
            print("cross 需要 storyboard.json 参数")
            sys.exit(2)
        with open(sys.argv[3], encoding="utf-8") as f:
            storyboard = json.load(f)
        errors, warnings = check_cross(assets, storyboard)
        print("=" * 50)
        print("台账 × 分镜 交叉校验（阶段①↔②）")
        print("=" * 50)
        _print("错误（必须修）", errors, "❌")
        _print("警告（建议修）", warnings, "⚠️")
        print("=" * 50)
        print("结论:", "❌ 交叉不一致" if errors else "✅ 交叉一致")
        sys.exit(1 if errors else 0)

    else:
        print(f"未知子命令：{cmd}")
        sys.exit(2)


if __name__ == "__main__":
    main()
