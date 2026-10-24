#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-jieshuo-pipeline 成片提示词组装器（prompt_build）
把「素材匹配表 + 旁白稿」组装成逐段两段式成片提示词【画面】→【字幕】。

用法：
    python prompt_build.py vo.json assets.json -o prompts.json
"""

import json
import argparse

# 三类解说的画面氛围默认值
TYPE_TONE = {
    "历史人物志": "暖黄做旧色调，历史感",
    "事件战役": "纪实质感，冷峻真实",
    "科普知识": "简洁现代，科技感",
}


def build_prompt(seg, asset, vo):
    """组装单段两段式提示词"""
    typ = vo.get("type", "科普知识")
    aspect = vo.get("aspect", "16:9")  # 前置锁 F 画幅
    tone = TYPE_TONE.get(typ, "自然色调")
    # 画面：素材方向 + 氛围 + 画幅
    asset_dir = (asset or {}).get("asset_dir", "") or seg.get("visual_hint", "")
    scene = f"{asset_dir}，{tone}，{aspect}"
    # 字幕：主字幕 + 强调字幕样式
    main = seg.get("subtitle_main", "")
    emph = seg.get("subtitle_emph", "")
    sub = f"主字幕\"{main}\"底部居中"
    if emph:
        sub += f"，强调字\"{emph}\"放大加粗定格"
    return f"【画面】{scene} → 【字幕】{sub}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("vo", help="旁白稿 JSON")
    p.add_argument("assets", help="素材匹配表 JSON")
    p.add_argument("-o", "--output", default="prompts.json")
    args = p.parse_args()

    with open(args.vo, encoding="utf-8") as f:
        vo = json.load(f)
    with open(args.assets, encoding="utf-8") as f:
        assets = json.load(f)

    asset_map = {a.get("id"): a for a in assets.get("segments", [])}
    prompts = []
    for seg in vo.get("segments", []):
        asset = asset_map.get(seg.get("id"))
        prompts.append({
            "id": seg.get("id"),
            "prompt": build_prompt(seg, asset, vo),
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成 {len(prompts)} 条成片提示词 → {args.output}")
    for pr in prompts[:3]:
        print(f"\n--- {pr['id']} ---\n{pr['prompt']}")


if __name__ == "__main__":
    main()
