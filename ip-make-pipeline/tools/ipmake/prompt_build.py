#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 七段式提示词组装器
对标「提示词七段式」：把分镜表 + 资产台账 + 站位声明，组装成七段式成片提示词。

用法：
    python prompt_build.py storyboard.json assets.json staging.json -o prompts.json
"""

import json
import argparse


def build_prompt(shot, assets, staging, style, language="zh"):
    """按七段式组装单镜提示词"""
    en = (language == "en")
    segs = {}
    # ① 画风风格
    segs["画风风格"] = style.get("visual", "cinematic" if en else "写实") + "，" + style.get("tone", "natural tone" if en else "自然色调") + "，" + style.get("light", "natural light" if en else "自然光")
    # ② 场景资产
    scene = shot.get("scene", "")
    segs["场景资产"] = scene if scene else ("(carry over previous scene)" if en else "(沿用上一镜场景)")
    # ③ 核心人物
    chars = shot.get("characters", "")
    segs["核心人物"] = chars if chars else ("empty shot, no characters" if en else "空镜，无人物")
    # ④ 站位声明
    segs["站位声明"] = staging.get("declaration", "") if staging else ""
    # ⑤ 时间轴分镜
    segs["时间轴分镜"] = shot.get("description", "") + f"（{shot.get('duration', 0)}s）"
    # ⑥ 音效
    segs["音效"] = style.get("sound", "ambient sound" if en else "环境音")
    # ⑦ 强制禁止项
    segs["强制禁止项"] = (
        "soft frontal fill light, no light spots; if characters present, strictly reuse the character sheet facial features, no face swap; no absolute efficacy claims"
        if en else "柔和正面补光，无光斑；若有人物，严格复用定妆单面部特征，不换脸；无绝对化功效表述"
    )
    # 组装成顺序字符串：【段名】内容 →【段名】内容 → …
    # 七段段名始终输出（内容可为空），保证下游 gate 闸门3 能逐段核对「七段齐全」。
    # 站位声明段在无多人戏时内容为空，但段名仍保留，避免被误判为「缺段」。
    order = ["画风风格", "场景资产", "核心人物", "站位声明", "时间轴分镜", "音效", "强制禁止项"]
    return " → ".join(f"【{k}】{segs.get(k, '')}" for k in order)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("storyboard", help="分镜表 JSON")
    p.add_argument("assets", help="资产台账 JSON")
    p.add_argument("staging", help="站位声明 JSON")
    p.add_argument("-o", "--output", default="prompts.json")
    args = p.parse_args()

    with open(args.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    with open(args.assets, encoding="utf-8") as f:
        assets = json.load(f)
    with open(args.staging, encoding="utf-8") as f:
        staging = json.load(f)

    style = sb.get("style", assets.get("style", {}))
    language = sb.get("language", "zh")
    prompts = []
    for shot in sb.get("shots", []):
        prompts.append({
            "shot_id": shot.get("shot_id"),
            "prompt": build_prompt(shot, assets, staging, style, language),
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成 {len(prompts)} 条七段式提示词 → {args.output}")
    for p in prompts[:3]:
        print(f"\n--- 镜{p['shot_id']} ---\n{p['prompt']}")


if __name__ == "__main__":
    main()
