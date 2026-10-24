#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-jieshuo-pipeline 统一 CLI 入口

子命令：
    validate 旁白稿质检
    build    成片提示词组装
    gate     投喂层三道闸门
    board    离线解说看板导出
    pipeline 一键编排（validate → build → gate → board）

用法：
    python cli.py validate vo.json [assets.json] [--json]
    python cli.py build vo.json assets.json -o prompts.json
    python cli.py gate vo.json assets.json prompts.json [validate_report.json]
    python cli.py board vo.json [assets.json] [prompts.json] -o board.html
    python cli.py pipeline vo.json assets.json -o board.html
"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))

MODULES = {
    "validate": "validate",
    "build": "prompt_build",
    "gate": "gate",
    "board": "board",
}


def _run(module_name, args):
    import subprocess
    target = os.path.join(HERE, module_name + ".py")
    return subprocess.call([sys.executable, target] + args)


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

    p = argparse.ArgumentParser(prog="pipeline", description="一键编排四阶段")
    p.add_argument("vo")
    p.add_argument("assets")
    p.add_argument("-o", "--output", default="board.html")
    pa = p.parse_args(args)

    base_dir = os.path.dirname(os.path.abspath(pa.vo)) or "."
    report_path = os.path.join(base_dir, "validate_report.json")
    prompts_path = os.path.join(base_dir, "prompts.json")

    steps = [
        ("① 质检旁白稿", "validate", [pa.vo, pa.assets, "--json"], report_path),
        ("② 组装提示词", "prompt_build", [pa.vo, pa.assets, "-o", prompts_path], None),
        ("③ 三道闸门", "gate", [pa.vo, pa.assets, prompts_path, report_path], None),
        ("④ 导出看板", "board", [pa.vo, pa.assets, prompts_path, "-o", pa.output], None),
    ]

    print("=" * 50)
    print("ip-jieshuo-pipeline 一键编排")
    print("=" * 50)

    for i, (label, mod, args, out_redirect) in enumerate(steps, 1):
        print(f"\n>>> 步骤{i} {label}")
        target = os.path.join(HERE, mod + ".py")
        if out_redirect:
            with open(out_redirect, "w", encoding="utf-8") as f:
                code = subprocess.call([sys.executable, target] + args, stdout=f)
        else:
            code = subprocess.call([sys.executable, target] + args)
        if code != 0:
            print(f"\n❌ 步骤{i}「{label}」失败（退出码 {code}），中止后续步骤")
            sys.exit(code)

    print("\n" + "=" * 50)
    print("✅ 全流程完成：")
    print(f"   旁白稿: {pa.vo}")
    print(f"   提示词: {prompts_path}")
    print(f"   质检报告: {report_path}")
    print(f"   看板: {pa.output}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
