# short-drama-pipeline 短剧流水线

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org/)
[![零依赖](https://img.shields.io/badge/依赖-纯标准库-brightgreen.svg)](#技术栈)
[![Skill 数](https://img.shields.io/badge/Skills-3-orange.svg)](#三个-skill-的关系)

一套**规则库驱动的短剧/影视内容生产流水线**，把「存量 IP 改编 → 剧本 → 分镜 → 成片」的完整链路工程化。三层 skill 各司其职、接口对齐，全部遵循「规则库 + 可执行工具链 + 开源三件套」的同一套设计规范。

## 三个 skill 的关系

```
                    ┌─────────────────────────────┐
                    │   ip-script-pipeline（剧本层）│
                    │   六阶段编剧链 + 三赛道硬分流   │
                    │   产出：三件套 / 剧本 / 解说稿   │
                    └──────────────┬──────────────┘
                                   │ 赛道①国内剧 / ②海外剧 → 三件套 + 剧本
                                   │ 赛道③解说叙事 → 解说稿 package
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
   ┌──────────────────────────┐        ┌──────────────────────────┐
   │  ip-make-pipeline（制作层）│        │ ip-jieshuo-pipeline（成片）│
   │  分镜 → 成片（七段式提示词） │        │ 旁白稿 → 成片（两段式提示词）│
   │  防换脸 + 跨集一致性       │        │ 素材匹配 + 段落对齐        │
   └──────────────────────────┘        └──────────────────────────┘
```

| Skill | 层 | 一句话定位 | 消费 | 产出 |
|---|---|---|---|---|
| `ip-script-pipeline` | 剧本层 | 「讲什么」——存量 IP → 能过审的剧本 | 存量网文 IP | 三件套（简介单/定妆单/资产清单）+ 剧本 + 解说稿 |
| `ip-make-pipeline` | 制作层 | 「怎么拍」——剧本 → 分镜 → 成片提示词 | 三件套 + 剧本 | 分镜表 + 七段式提示词 + 离线看板 |
| `ip-jieshuo-pipeline` | 成片层 | 「怎么说」——解说稿 → 素材剪辑成片 | 解说稿 package | 素材匹配表 + 两段式提示词 + SRT + 解说看板 |

## 三赛道如何分流

| 赛道 | 剧本层 | 制作层 |
|---|---|---|
| ① 国内剧 | 六阶段编剧链（中文） | `ip-make-pipeline` 完整四阶段 |
| ② 海外剧 | 六阶段编剧链（中文写）+ 英文对白适配层 | `ip-make-pipeline` 完整四阶段 + 英文契约 |
| ③ 解说叙事 | 解说剧本链（旁白稿 VO Script） | `ip-jieshuo-pipeline`（不走分镜） |

## 三条共同承诺（每个 skill 都有脚本落地）

- **不漂移**：角色/场景/道具先锁定再进分镜，跨镜 + 跨集一致性有据可依
- **不返工**：错误拦在生成之前（前置锁 + 必查清单 + 质检门禁 + 闸门）
- **能直接投喂**：输出结构化提示词，整组复制即可喂 AI 生成

## 目录结构

```
short-drama-pipeline/
├── ip-script-pipeline/   # 剧本层：六阶段编剧链 + 三赛道分流
├── ip-make-pipeline/     # 制作层：分镜 + 资产 + 跨集一致性 + 七段式提示词 + 看板
├── ip-jieshuo-pipeline/  # 成片层：解说稿 → 素材匹配 → 两段式提示词 → 字幕/看板
└── README.md             # 本文件（总览）
```

## 快速上手

每个 skill 都有自己的 README，含完整的安装与命令行说明：

- 剧本层：[`ip-script-pipeline/README.md`](ip-script-pipeline/README.md)
- 制作层：[`ip-make-pipeline/README.md`](ip-make-pipeline/README.md)
- 成片层：[`ip-jieshuo-pipeline/README.md`](ip-jieshuo-pipeline/README.md)

**典型完整链路**（国内剧）：

```bash
# 1. 剧本层：存量 IP → 三件套 + 剧本（按 ip-script-pipeline/SKILL.md 六阶段走）
# 2. 制作层：三件套 + 剧本 → 分镜 → 成片
cd ip-make-pipeline/tools/ipmake
python cli.py pipeline storyboard.json assets.json staging.json -o board.html
```

**解说成片**（赛道③）：

```bash
cd ip-jieshuo-pipeline/tools/jieshuo
python cli.py pipeline examples/vo.json examples/assets.json -o board.html
```

## 技术栈

- 全部工具链为 **Python 3 标准库**，零第三方依赖
- 规则文件为 Markdown，脚本为纯 Python，可直接运行
- 每个 skill 均为独立 WorkBuddy skill（含 `SKILL.md`），也可作为纯文档/工具库使用

## License

[MIT](LICENSE)
