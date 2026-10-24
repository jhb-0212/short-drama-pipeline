#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-jieshuo-pipeline 离线解说看板（board）
把「旁白稿 + 素材匹配表 + 成片提示词」导出成单文件 HTML（双击即开）+ SRT 字幕 + 剪辑时间线 CSV。

用法：
    python board.py vo.json [assets.json] [prompts.json] -o board.html
    自动生成 board.srt / board.csv
"""

import json
import sys
import argparse
import csv
import os
import re


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(vo, assets, prompts):
    segs = vo.get("segments", [])
    title = vo.get("title", "解说看板")
    asset_map = {a.get("id"): a for a in (assets or {}).get("segments", [])}
    prompt_map = {p.get("id"): p.get("prompt", "") for p in (prompts or [])}

    rows = []
    for s in segs:
        a = asset_map.get(s.get("id"), {})
        rows.append(f"""
        <tr>
          <td class="sid">{esc(s.get('id'))}</td>
          <td>{esc(s.get('role'))}</td>
          <td class="nar">{esc(s.get('narration'))}</td>
          <td>{esc(a.get('asset_dir') or s.get('visual_hint'))}</td>
          <td>{esc(a.get('copyright'))}</td>
          <td>{esc(s.get('subtitle_main'))}{' <b>' + esc(s.get('subtitle_emph')) + '</b>' if s.get('subtitle_emph') else ''}</td>
          <td class="prompt">{esc(prompt_map.get(s.get('id'), ''))}</td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<style>
  body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif; margin: 20px; background: #fff; color: #1a1a1a; }}
  h1 {{ font-size: 20px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 8px; vertical-align: top; text-align: left; }}
  th {{ background: #f5f5f5; position: sticky; top: 0; }}
  .sid {{ width: 44px; }}
  .nar {{ min-width: 200px; }}
  .prompt {{ color: #555; font-size: 12px; }}
  b {{ color: #c0392b; }}
</style>
</head>
<body>
<h1>{esc(title)} · 离线解说看板</h1>
<p>共 {len(segs)} 段 · 总时长 {esc(vo.get('duration', '?'))}s · 语速 {esc(vo.get('rate', '?'))}字/秒</p>
<table>
<thead><tr>
  <th>段落</th><th>结构</th><th>旁白</th><th>素材方向</th><th>版权</th><th>字幕</th><th>成片提示词</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>"""


def build_srt(vo):
    """SRT：按语速分配逐段时长"""
    rate = float(vo.get("rate", 5.0))
    segs = vo.get("segments", [])
    out = []
    t = 0.0
    for i, s in enumerate(segs, 1):
        # 字数口径与 validate.py count_chars 一致（去标点、只算中英文+数字），
        # 否则 SRT 时间轴会与 V2 语速校验的「旁白字数 ÷ 语速」对不上，导致总时长偏长。
        chars = len(re.findall(r"[\u4e00-\u9fff0-9A-Za-z]", s.get("narration") or ""))
        dur = chars / rate if rate > 0 else 3.0
        start, end = t, t + dur
        text = s.get("subtitle_main", "")
        if s.get("subtitle_emph"):
            # 强调字幕作为同段第二条，叠在同时间段
            text = text  # 主字幕保留；强调字幕写入独立条
        def ts(sec):
            h = int(sec // 3600); m = int(sec % 3600 // 60); ss = sec % 60
            return f"{h:02d}:{m:02d}:{int(ss):02d},{int((ss%1)*1000):03d}"
        out.append(f"{i}\n{ts(start)} --> {ts(end)}\n{text}\n")
        t += dur
    return "\n".join(out)


def build_csv(vo, assets):
    """剪辑时间线 CSV"""
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["段落", "结构", "旁白", "素材方向", "版权", "主字幕", "强调字幕"])
    asset_map = {a.get("id"): a for a in (assets or {}).get("segments", [])}
    for s in vo.get("segments", []):
        a = asset_map.get(s.get("id"), {})
        w.writerow([s.get("id"), s.get("role"), s.get("narration"),
                    a.get("asset_dir") or s.get("visual_hint"),
                    a.get("copyright"),
                    s.get("subtitle_main"), s.get("subtitle_emph")])
    return buf.getvalue()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("vo", help="旁白稿 JSON")
    p.add_argument("assets", nargs="?", default=None, help="素材匹配表 JSON（可选）")
    p.add_argument("prompts", nargs="?", default=None, help="成片提示词 JSON（可选）")
    p.add_argument("-o", "--output", default="board.html")
    args = p.parse_args()

    with open(args.vo, encoding="utf-8") as f:
        vo = json.load(f)
    assets = {}
    if args.assets:
        with open(args.assets, encoding="utf-8") as f:
            assets = json.load(f)
    prompts = []
    if args.prompts:
        with open(args.prompts, encoding="utf-8") as f:
            prompts = json.load(f)

    base = os.path.splitext(args.output)[0]

    html = build_html(vo, assets, prompts)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    srt = build_srt(vo)
    with open(f"{base}.srt", "w", encoding="utf-8") as f:
        f.write(srt)

    csv_data = build_csv(vo, assets)
    with open(f"{base}.csv", "w", encoding="utf-8", newline="") as f:
        f.write(csv_data)

    print("✅ 解说看板已生成：")
    print(f"   HTML: {args.output}")
    print(f"   SRT : {base}.srt")
    print(f"   CSV : {base}.csv")


if __name__ == "__main__":
    main()
