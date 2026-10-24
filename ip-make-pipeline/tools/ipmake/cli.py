#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 统一 CLI 入口

子命令：
    asset   资产台账质检（check / cross）
    series  跨集一致性质检（check / series）
    validate 分镜表质检
    build   七段式提示词组装
    gate    投喂层六道闸门
    board   离线看板导出
    pipeline 一键编排（validate → build → gate → board）

用法：
    python cli.py asset check assets.json
    python cli.py asset cross assets.json storyboard.json
    python cli.py series check assets.json storyboard.json
    python cli.py series series assets.json ep01.json ep02.json ...
    python cli.py validate storyboard.json [--json]
    python cli.py build storyboard.json assets.json staging.json -o prompts.json
    python cli.py gate storyboard.json prompts.json [validate_report.json]
    python cli.py board storyboard.json [prompts.json] -o board.html
    python cli.py pipeline storyboard.json assets.json staging.json -o board.html
"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# 子命令 -> 对应脚本文件（不含 .py）
MODULES = {
    "validate": "validate",
    "gate": "gate",
    "build": "prompt_build",
    "board": "board",
    "asset": "asset_check",
    "series": "series_check",
}


def _run(module_name, args):
    """调用对应脚本的 main（通过子进程，保持各脚本独立可运行）"""
    import subprocess
    target = os.path.join(HERE, module_name + ".py")
    code = subprocess.call([sys.executable, target] + args)
    return code


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "pipeline":
        return _pipeline(rest)

    if cmd not in MODULES:
        print(f"未知子命令：{cmd}\n")
        print(__doc__)
        sys.exit(2)

    sys.exit(_run(MODULES[cmd], rest))


def _pipeline(args):
    """一键编排：validate → build → gate → board"""
    import subprocess
    import argparse
    import json

    p = argparse.ArgumentParser(prog="pipeline", description="一键编排四阶段")
    p.add_argument("storyboard")
    p.add_argument("assets")
    p.add_argument("staging")
    p.add_argument("-o", "--output", default="board.html")
    pa = p.parse_args(args)

    base_dir = os.path.dirname(os.path.abspath(pa.storyboard)) or "."
    report_path = os.path.join(base_dir, "validate_report.json")
    prompts_path = os.path.join(base_dir, "prompts.json")

    steps = [
        ("① 质检分镜表", "validate", [pa.storyboard, "--json"], report_path),
        ("② 组装提示词", "prompt_build", [pa.storyboard, pa.assets, pa.staging, "-o", prompts_path], None),
        ("③ 六道闸门", "gate", [pa.storyboard, prompts_path, report_path], None),
        ("④ 导出看板", "board", [pa.storyboard, prompts_path, "-o", pa.output], None),
    ]

    print("=" * 50)
    print("ip-make-pipeline 一键编排")
    print("=" * 50)

    for i, (label, mod, args, out_redirect) in enumerate(steps, 1):
        print(f"\n>>> 步骤{i} {label}")
        target = os.path.join(HERE, mod + ".py")
        if out_redirect:
            # 把 --json 输出重定向到报告文件，供后续 gate 读取
            with open(out_redirect, "w", encoding="utf-8") as f:
                code = subprocess.call([sys.executable, target] + args, stdout=f)
        else:
            code = subprocess.call([sys.executable, target] + args)
        if code != 0:
            print(f"\n❌ 步骤{i}「{label}」失败（退出码 {code}），中止后续步骤")
            sys.exit(code)

    print("\n" + "=" * 50)
    print("✅ 全流程完成：")
    print(f"   分镜表: {pa.storyboard}")
    print(f"   提示词: {prompts_path}")
    print(f"   质检报告: {report_path}")
    print(f"   看板: {pa.output}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
