# ip-make-pipeline 工具链使用说明

## 简介

独立 Python CLI 工具链，配套 `ip-make-pipeline` skill 使用。子命令对应四阶段 + 交付看板：

| 命令 | 对应阶段 | 作用 |
|---|---|---|
| `asset` | ① 资产绑定 | 资产台账质检（`check` 台账本身 / `cross` 台账×分镜交叉） |
| `series` | ①.5 跨集一致性 | 跨集回锚质检（`check` 单集回锚 / `series` 多集回锚） |
| `validate` | ② 分镜表 / ③ 构图运镜 | 质检（C1~C12 检查码 + P0~P2 分级） |
| `gate` | 投喂前 | 六道闸门（防止半成品投喂） |
| `build` | ④ 成片提示词 | 七段式提示词组装 |
| `board` | 交付 | 离线看板（HTML + SRT + CSV + JSON） |
| `pipeline` | 全流程 | 一键编排 validate → build → gate → board |

## 检查码清单（validate.py）

| 码 | 级别 | 检查项 |
|---|---|---|
| C01 | P0 | 分镜号连续无跳号 |
| C02 | P0 | 字段齐全（硬字段非空，软字段允许空镜） |
| C03 | P0 | 总时长对齐目标 + 合计行（total）校验 |
| C04 | P0 | 台词字数 ÷ 语速 ≤ 镜时长 |
| C05 | P0 | 人物/场景/道具均用资产编号 |
| C06 | P0 | 同角色跨镜面部描述一致（防换脸） |
| C07 | P1 | 景别跳变 ≤2 级 |
| C08 | P1 | 运镜/构图取值在词典内 |
| C09 | P1 | 武戏关键动作拆相位 |
| C10 | P1 | 越轴检测（机位方向跳变） |
| C11 | P1 | 安全转译检测（血腥/断肢敏感词 → 气浪/火花/定格） |
| C12 | P2 | 情绪峰值校验（tension 峰值应落在第 9 节拍附近且 ≥8） |

> C11 对接 `references/compliance-translate.md` 的安全转译词典，命中敏感词会提示合规改写。
> C12 对接 `references/emotion-curve.md`，仅当分镜标注了 `tension` 字段时生效。

## 资产台账检查（asset_check.py）

`asset check` 校验台账本身：编号唯一、P/S/D/V 前缀合法、A/B/C 分级合规、字段齐全（A 级人物必须有 face，人物建议有 face 供 C06 防换脸）。

`asset cross` 交叉校验台账 × 分镜：分镜引用的每个编号必须存在于台账，台账中未引用的资产会提示（遗漏或冗余）。

## 跨集一致性质检（series_check.py）

`series check` 单集回锚：校验单集分镜表的 `face_anchor` 是否等于台账 `face`、编号 name 是否一致（跨集防换脸的地基）。

`series series` 多集回锚：校验多集分镜表共享同一台账，跨集同一角色无多套面部描述、A 级人物台账都有 `face`。

> 详见 `references/series-consistency.md`。与 `validate.py` 的 C06（单集内跨镜）互补：C06 查「单集内不换脸」，series_check 查「跨集不换脸」。

## 环境要求

- Python 3.8+，无第三方依赖（纯标准库）。

## 输入格式

所有脚本的输入都是 JSON。核心是 **分镜表 JSON**（`storyboard.json`），schema 如下：

```json
{
  "title": "《跨界追夫》第1集 分镜表",
  "target_duration": 53,
  "total": { "shots": 12, "duration": 53 },
  "staging": "S03 营地，梁大背对冰湖站中央，梁小在其右手",
  "style": {
    "visual": "写实",
    "tone": "冷色调",
    "light": "自然光",
    "sound": "环境音 + 弦乐"
  },
  "shots": [
    {
      "shot_id": 1,
      "duration": 3,
      "description": "夜幕下，林梓泳撬开古董店后门",
      "characters": "P01 林梓泳",
      "scene": "S01 古董店后巷",
      "props": "D01 撬棍",
      "dialogue": "独白【林梓泳：\"手艺人，不问来路。\"】",
      "camera": "固定",
      "composition": "三分线",
      "shot_size": "中景",
      "face_anchor": "P01：圆脸、细眼、短发、浅麦色皮肤",
      "camera_side": "左",
      "is_action": false
    }
  ]
}
```

## 使用示例

```bash
# 0. 资产台账质检（阶段①）
python asset_check.py check assets.json
python asset_check.py cross assets.json storyboard.json

# 1. 质检分镜表
python validate.py storyboard.json

# 2. 组装七段式提示词
python prompt_build.py storyboard.json assets.json staging.json -o prompts.json

# 3. 六道闸门（投喂前）
python gate.py storyboard.json prompts.json validate_report.json

# 4. 生成离线看板
python board.py storyboard.json prompts.json -o board.html
```

## 统一入口（推荐）

```bash
# 一键编排四阶段（validate → build → gate → board）
python cli.py pipeline storyboard.json assets.json staging.json -o board.html

# 或逐条调用
python cli.py asset check assets.json
python cli.py asset cross assets.json storyboard.json
python cli.py series check assets.json storyboard.json
python cli.py series series assets.json storyboard_ep01.json storyboard_ep02.json
python cli.py validate storyboard.json
python cli.py board storyboard.json prompts.json -o board.html
```

## 资产台账 / 站位声明的 JSON 格式

`assets.json`（资产台账）：
```json
{
  "P01": {"name": "林梓泳", "level": "A", "face": "圆脸、细眼、短发、浅麦色皮肤"},
  "S01": {"name": "古董店后巷", "level": "B"},
  "D01": {"name": "撬棍", "level": "C"},
  "style": {"visual": "写实", "tone": "冷色调", "light": "自然光", "sound": "环境音"}
}
```

`staging.json`（站位声明）：
```json
{
  "declaration": "S03 营地，梁大背对冰湖站中央，梁小在其右手，邓总在对面"
}
```
