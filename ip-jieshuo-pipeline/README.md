# ip-jieshuo-pipeline

解说叙事「旁白稿 → 成片」制作层流水线（赛道③·解说，与 ip-make-pipeline 平行）。

> 消费 `ip-script-pipeline`（剧本层）赛道③「解说叙事」产出的**解说稿 package**（旁白稿 VO Script / 画面提示表 / 字幕稿 / 考据来源），产出可剪辑/可生成的**素材匹配表 + 成片提示词 + 字幕 SRT + 离线解说看板**。

## 定位

解说类**不做分镜**（没有站位/轴线/运镜/景别），它的成片是「一段旁白配一段素材」。本流水线与 `ip-make-pipeline`（分镜流水线）是**两条平行线**：

| 维度 | ip-make-pipeline（分镜） | ip-jieshuo-pipeline（解说） |
|---|---|---|
| 输入 | 三件套 + 完整剧本 | 解说稿 package（旁白稿 + 画面提示表 + 字幕稿） |
| 核心产物 | 11 字段分镜表 + 七段式提示词 | 素材匹配表 + 两段式提示词 |
| 一致性问题 | 防换脸（同角色跨镜） | 段落对齐（旁白/素材/字幕/提示词四份对齐） |
| 版权关注 | 角色资产 | 素材版权（历史影像/图片） |

## 三条核心承诺

- **不漂移**：旁白 → 素材 → 字幕 → 提示词四份文件按段落号（`V01/V02/…`）对齐，素材方向锚定画面提示表 → `validate.py` V3 对齐检查
- **不返工**：语速/时长/版权/违禁词拦在剪辑之前 → 🔒 前置锁 + V1~V8 检查码 + 三道闸门
- **能直接投喂**：输出成片提示词 + SRT 字幕，整组复制即可进剪辑/图文生成工具 → `prompt_build.py` + `board.py`

## 快速开始

```bash
# 一键编排（质检 → 提示词 → 闸门 → 看板）
python tools/jieshuo/cli.py pipeline examples/vo.json examples/assets.json -o board.html

# 分步
python tools/jieshuo/validate.py examples/vo.json examples/assets.json
python tools/jieshuo/prompt_build.py examples/vo.json examples/assets.json -o prompts.json
python tools/jieshuo/gate.py examples/vo.json examples/assets.json prompts.json validate_report.json
python tools/jieshuo/board.py examples/vo.json examples/assets.json prompts.json -o board.html
```

## 目录结构

```
├── SKILL.md               # 前置锁（7道）+ 四阶段 + 三条承诺
├── README.md / LICENSE(MIT)   # 变更记录见顶层 CHANGELOG.md
├── references/            # 4 个规则文件
│   ├── vo-format.md        # 旁白稿字段规范 + 语速校验
│   ├── asset-match.md      # 素材匹配表 + 版权分级
│   ├── prompt-guide.md     # 成片提示词（两段式）
│   └── subtitle-format.md  # 字幕稿 + SRT 规范
├── examples/              # 真实案例（历史人物志）
└── tools/jieshuo/         # 5 个 Python 脚本（纯标准库）
    ├── validate.py         # V1~V8 检查码
    ├── prompt_build.py     # 两段式提示词
    ├── gate.py             # 三道闸门
    ├── board.py            # HTML/SRT/CSV 导出
    └── cli.py              # 统一入口 + pipeline 编排
```

## 依赖

纯 Python 标准库，无第三方依赖。

## License

MIT
