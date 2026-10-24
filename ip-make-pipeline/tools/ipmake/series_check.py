#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 跨集一致性质检（series_check）
对标「跨集一致性」承诺：防换脸不止单集内跨镜，更要跨集回锚定妆单。

背景：原 C06 防换脸只在「单集分镜表内」比对首镜 vs 后续镜的 face_anchor，
不知道上一集这个角色长什么样。跨集时各集 face_anchor 各自漂移，无人比对。
本脚本把「防换脸」升级为「回锚定妆单」：face_anchor 必须等于 assets.json[Pxx].face。

三个子命令：
    check   单集回锚：校验单集分镜表的 face_anchor / 编号 name 是否与台账一致
    series  多集一致性：校验多集分镜表共享同一台账，跨集 face/name 不漂移

用法：
    python series_check.py check assets.json storyboard_ep01.json
    python series_check.py series assets.json storyboard_ep01.json storyboard_ep02.json ...
"""

import json
import sys
import re


def _asset_id(s):
    """提取「前缀+编号」，如 P01、S03、P01-A"""
    m = re.match(r"^([PSDV])(\d{2})(-[A-Z])?$", s)
    if m:
        return m.group(1), m.group(2), m.group(3) or ""
    return None, None, None


def _ledger(assets):
    """返回 {编号: 资产对象}，只保留合法资产编号 key（排除 style 等）"""
    out = {}
    for k, v in assets.items():
        pfx, num, sub = _asset_id(k)
        if pfx is not None:
            out[k] = v
    return out


def _parse_face_anchor(anchor):
    """解析 face_anchor 字符串 -> {Pxx: desc}

    支持：
    - 单角色："P01：圆脸、细长眼、黑色短发"
    - 多角色："P01：…；P02：…"（分号分隔）
    - 英文冒号/分号兼容
    """
    result = {}
    for part in re.split(r"[；;]", anchor or ""):
        m = re.match(r"\s*(P\d{2})\s*[:：]\s*(.+)$", part)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def _ref_name_pairs(text):
    """从单个字段文本里精确提取「编号 + 名字」对。

    处理 "P01 林梓泳 P02 沈青梧"（多编号连写）→ [(P01, 林梓泳), (P02, 沈青梧)]
    支持子编号（换装不换脸）："P01-A 林梓泳" → [(P01-A, 林梓泳)]
    名字取编号后的连续非空白、非编号前缀的 token（中文名或英文名）。
    """
    pairs = []
    # 编号含可选子编号后缀（-A/-B），如 P01、P01-A、S03-B
    for m in re.finditer(r"([PSDV]\d{2}(?:-[A-Z])?)\s+([^\s,，;；、]+)", text):
        ref, name = m.group(1), m.group(2)
        # 排除名字本身就是另一个编号的情况（如 "P01 P02" 罕见但防御）
        if re.fullmatch(r"[PSDV]\d{2}(?:-[A-Z])?", name):
            continue
        pairs.append((ref, name))
    return pairs


def check_single(assets, storyboard):
    """单集回锚：face_anchor 是否等于定妆单 face，编号 name 是否一致。

    返回 (errors, warnings)
    """
    errors = []
    warnings = []
    ledger = _ledger(assets)
    title = storyboard.get("title", "(未命名)")
    shots = storyboard.get("shots", [])

    for i, s in enumerate(shots):
        sid = s.get("shot_id", i + 1)

        # 1. face_anchor 回锚：每个 Pxx 的描述必须 == 台账 face（跨集防换脸地基）
        anchor = s.get("face_anchor", "") or ""
        faces = _parse_face_anchor(anchor)
        for pid, desc in faces.items():
            entry = ledger.get(pid)
            if not entry:
                errors.append(f"[{title}] 镜{sid} face_anchor 引用了台账不存在的角色 {pid}")
                continue
            truth = entry.get("face", "")
            if not truth:
                warnings.append(f"[{title}] 镜{sid} 角色 {pid} 台账缺 face（无法回锚，建议补全定妆单）")
                continue
            if desc != truth:
                errors.append(
                    f"[{title}] 镜{sid} {pid} 面部漂移（跨集防换脸）：分镜写「{desc}」≠ 定妆单「{truth}」"
                )

        # 2. 编号 name 一致性：逐字段精确解析「编号+名字」，比对台账 name
        for field in ("characters", "scene", "props"):
            text = s.get(field, "") or ""
            for ref, name in _ref_name_pairs(text):
                entry = ledger.get(ref)
                if not entry:
                    errors.append(f"[{title}] 镜{sid} 引用了台账不存在的编号 {ref}")
                    continue
                truth_name = entry.get("name", "")
                if truth_name and name != truth_name:
                    errors.append(
                        f"[{title}] 镜{sid} {ref} 名字漂移：分镜写「{name}」≠ 台账「{truth_name}」"
                    )

        # 3. 人物集合双向对齐：face_anchor 里的人物 与 characters 里的人物，必须是同一集合
        #    （跨集防换脸的关键补丁：任一方向漏了，该镜人物就脱锚/漏登记）
        chars_text = s.get("characters", "") or ""
        # characters 里的 P 编号集合（含子编号，但取主编号用于人脸对齐）
        chars_p = set()
        for ref, name in _ref_name_pairs(chars_text):
            if ref.startswith("P"):
                chars_p.add(ref.split("-")[0])
        # face_anchor 里的 P 编号集合
        anchor_p = set(faces.keys())
        # characters 有但 face_anchor 没锚 → 本镜脱锚，换脸没人查
        for pid in chars_p - anchor_p:
            # 台账 A 级人物必须有 face，脱锚即漏防换脸；B/C 级可宽松（群演可只写编号不锚脸）
            entry = ledger.get(pid)
            if entry and entry.get("level") == "A":
                errors.append(f"[{title}] 镜{sid} 人物 {pid} 出现在 characters 但未进 face_anchor（本镜脱锚，防换脸失效）")
        # face_anchor 有但 characters 没写 → 漏登记（人物在镜头里却没记）
        for pid in anchor_p - chars_p:
            errors.append(f"[{title}] 镜{sid} 人物 {pid} 进了 face_anchor 但未写进 characters（漏登记）")

    return errors, warnings


def check_series(assets, storyboards):
    """多集一致性：所有集共享同一台账，跨集 face/name 不漂移。

    storyboards: list of (path, storyboard_dict)
    返回 (errors, warnings)
    """
    errors = []
    warnings = []
    ledger = _ledger(assets)

    # 对每集跑单集回锚
    for path, sb in storyboards:
        e, w = check_single(assets, sb)
        errors.extend(e)
        warnings.extend(w)

    # 跨集汇总：每集的 face_anchor 描述集合，若同一 Pxx 在不同集出现不同描述（即使都≠台账）也要报
    # （check_single 已比对台账，这里主要报「台账缺失 face」导致的跨集无法锚定）
    face_seen = {}  # pid -> {desc: [titles]}
    for path, sb in storyboards:
        title = sb.get("title", "(未命名)")
        for s in sb.get("shots", []):
            anchor = s.get("face_anchor", "") or ""
            for pid, desc in _parse_face_anchor(anchor).items():
                face_seen.setdefault(pid, {}).setdefault(desc, []).append(title)

    for pid, descs in face_seen.items():
        if len(descs) > 1:
            # 同一角色跨集出现不同描述 → 漂移（去重标题，避免堆叠）
            detail = "；".join(
                f"「{d}」见于 {', '.join(sorted(set(ts)))}"
                for d, ts in descs.items()
            )
            errors.append(f"跨集换脸：角色 {pid} 在不同集有 {len(descs)} 套面部描述 —— {detail}")

    # 台账完整性：A 级人物必须有 face（跨集回锚的前提）
    for pid, entry in ledger.items():
        if entry.get("level") == "A" and _asset_id(pid)[0] == "P" and not entry.get("face"):
            errors.append(f"台账 A 级人物 {pid}（{entry.get('name','')}）缺 face，跨集无法回锚")

    # 跨集出场连续性：A 级人物应在全季至少出现一次（防漏戏/漏分镜导致主角凭空消失）
    appeared = set()
    for path, sb in storyboards:
        for s in sb.get("shots", []):
            for ref, name in _ref_name_pairs(s.get("characters", "") or ""):
                if ref.startswith("P"):
                    appeared.add(ref.split("-")[0])
    for pid, entry in ledger.items():
        if entry.get("level") == "A" and _asset_id(pid)[0] == "P" and pid not in appeared:
            errors.append(
                f"台账 A 级人物 {pid}（{entry.get('name','')}）在全季任何一集都未出场，疑似漏戏/漏分镜"
            )

    return errors, warnings


def _print(title, items, mark):
    if items:
        print(f"\n--- {title} ({len(items)}) ---")
        for it in items:
            print(f"  {mark} {it}")


def main():
    if len(sys.argv) < 4:
        print("用法:")
        print("  python series_check.py check assets.json storyboard.json")
        print("  python series_check.py series assets.json storyboard_ep01.json [ep02.json ...]")
        sys.exit(2)

    cmd = sys.argv[1]
    with open(sys.argv[2], encoding="utf-8") as f:
        assets = json.load(f)

    if cmd == "check":
        with open(sys.argv[3], encoding="utf-8") as f:
            sb = json.load(f)
        errors, warnings = check_single(assets, sb)
        print("=" * 50)
        print("跨集一致性 · 单集回锚")
        print("=" * 50)
        _print("错误（必须修）", errors, "❌")
        _print("警告（建议修）", warnings, "⚠️")
        print("=" * 50)
        print("结论:", "❌ 回锚失败，存在漂移" if errors else "✅ 回锚通过，人脸/名字与定妆单一致")
        sys.exit(1 if errors else 0)

    elif cmd == "series":
        paths = sys.argv[3:]
        storyboards = []
        for p in paths:
            with open(p, encoding="utf-8") as f:
                storyboards.append((p, json.load(f)))
        errors, warnings = check_series(assets, storyboards)
        print("=" * 50)
        print(f"跨集一致性 · 全季回锚（{len(storyboards)} 集）")
        print("=" * 50)
        _print("错误（必须修）", errors, "❌")
        _print("警告（建议修）", warnings, "⚠️")
        print("=" * 50)
        print("结论:", "❌ 跨集漂移，禁止合片" if errors else "✅ 全季一致，可合片")
        sys.exit(1 if errors else 0)

    else:
        print(f"未知子命令：{cmd}")
        sys.exit(2)


if __name__ == "__main__":
    main()
