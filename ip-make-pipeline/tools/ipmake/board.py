#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 离线分镜看板
对标「离线分镜看板」：把分镜表导出成单文件 HTML（双击即开）+ SRT 字幕 + 剪辑时间线 CSV + API 载荷 JSON。

用法：
    python board.py storyboard.json [prompts.json] -o board.html
    会自动在同目录生成 board.srt / timeline.csv / api_payload.json
"""

import json
import sys
import argparse
import csv
import os


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(storyboard, prompts):
    shots = storyboard.get("shots", [])
    title = storyboard.get("title", "分镜看板")
    prompt_map = {p.get("shot_id"): p.get("prompt", "") for p in (prompts or [])}

    rows = []
    for s in shots:
        rows.append(f"""
        <tr>
          <td class="sid">{esc(s.get('shot_id'))}</td>
          <td class="dur">{esc(s.get('duration'))}</td>
          <td class="desc">{esc(s.get('description'))}</td>
          <td>{esc(s.get('characters'))}</td>
          <td>{esc(s.get('dialogue'))}</td>
          <td>{esc(s.get('camera'))}</td>
          <td>{esc(s.get('composition'))}</td>
          <td>{esc(s.get('shot_size'))}</td>
          <td class="prompt">{esc(prompt_map.get(s.get('shot_id'), ''))}</td>
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
  .sid {{ width: 40px; }}
  .dur {{ width: 50px; }}
  .desc {{ min-width: 180px; }}
  .prompt {{ color: #555; font-size: 12px; }}
</style>
</head>
<body>
<h1>{esc(title)} · 离线分镜看板</h1>
<p>共 {len(shots)} 镜 · 总时长 {storyboard.get('target_duration', '?')}s</p>
<table>
<thead><tr>
  <th>分镜号</th><th>时长</th><th>画面描述</th><th>人物</th><th>台词</th><th>运镜</th><th>构图</th><th>景别</th><th>提示词</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>"""


def build_srt(storyboard):
    """SRT 字幕：只提取有台词的镜"""
    subs = []
    t = 0.0
    idx = 1
    for s in storyboard.get("shots", []):
        dur = float(s.get("duration", 0))
        lines = s.get("dialogue", "")
        if lines:
            start = t
            end = t + dur
            subs.append((idx, start, end, lines))
            idx += 1
        t += dur
    def ts(sec):
        h = int(sec // 3600); m = int(sec % 3600 // 60); ss = sec % 60
        return f"{h:02d}:{m:02d}:{int(ss):02d},{int((ss%1)*1000):03d}"
    out = []
    for i, start, end, lines in subs:
        out.append(f"{i}\n{ts(start)} --> {ts(end)}\n{lines}\n")
    return "\n".join(out)


def build_csv(storyboard):
    """剪辑时间线 CSV"""
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["分镜号", "时长", "起始时间", "画面描述", "人物", "台词", "运镜", "构图", "景别"])
    t = 0.0
    for s in storyboard.get("shots", []):
        dur = float(s.get("duration", 0))
        w.writerow([s.get("shot_id"), dur, f"{t:.1f}", s.get("description"),
                    s.get("characters"), s.get("dialogue"), s.get("camera"),
                    s.get("composition"), s.get("shot_size")])
        t += dur
    return buf.getvalue()


def build_api_payload(storyboard, prompts):
    """API 载荷 JSON"""
    return {
        "title": storyboard.get("title"),
        "target_duration": storyboard.get("target_duration"),
        "shots": [
            {"shot_id": s.get("shot_id"), "duration": s.get("duration"),
             "prompt": (prompts[i].get("prompt") if i < len(prompts) else "")}
            for i, s in enumerate(storyboard.get("shots", []))
        ]
    }


def build_feed_text(storyboard, prompts):
    """投喂文本：把所有镜的七段式提示词拼成可直接复制的纯文本"""
    if not prompts:
        return ""
    lines = []
    lines.append(f"# {storyboard.get('title', '分镜表')} · 投喂文本")
    lines.append(f"# 共 {len(prompts)} 镜，整组复制即可投喂视频模型")
    lines.append("")
    for p in prompts:
        sid = p.get("shot_id")
        prompt = p.get("prompt", "")
        lines.append(f"--- 镜{sid} ---")
        lines.append(prompt)
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("storyboard")
    p.add_argument("prompts", nargs="?", default=None)
    p.add_argument("-o", "--output", default="board.html")
    args = p.parse_args()

    with open(args.storyboard, encoding="utf-8") as f:
        storyboard = json.load(f)
    prompts = []
    if args.prompts:
        with open(args.prompts, encoding="utf-8") as f:
            prompts = json.load(f)

    base = os.path.splitext(args.output)[0]

    # HTML 看板
    html = build_html(storyboard, prompts)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    # SRT
    srt = build_srt(storyboard)
    with open(f"{base}.srt", "w", encoding="utf-8") as f:
        f.write(srt)

    # CSV
    csv_data = build_csv(storyboard)
    with open(f"{base}.csv", "w", encoding="utf-8", newline="") as f:
        f.write(csv_data)

    # API payload
    payload = build_api_payload(storyboard, prompts)
    with open(f"{base}.payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 投喂文本（整组可复制）
    feed = build_feed_text(storyboard, prompts)
    if feed:
        with open(f"{base}.feed.txt", "w", encoding="utf-8") as f:
            f.write(feed)

    print(f"✅ 看板已生成：")
    print(f"   HTML: {args.output}")
    print(f"   SRT : {base}.srt")
    print(f"   CSV : {base}.csv")
    print(f"   API : {base}.payload.json")
    if feed:
        print(f"   FEED: {base}.feed.txt (整组复制投喂)")


if __name__ == "__main__":
    main()
