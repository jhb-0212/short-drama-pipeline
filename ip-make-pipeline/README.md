# ip-make-pipeline · 短剧「分镜 → 成片」制作层流水线

一套**规则库 + 可执行工具链**的短剧/影视制作层 skill，把「分镜 → 成片」的关键工序工程化：消费剧本层产出的三件套与完整剧本，产出逐镜分镜表、站位/构图/运镜方案、七段式成片提示词，并导出离线分镜看板。

> 配套上游：`ip-script-pipeline`（剧本层）。本 skill 只负责「怎么拍」，不管「讲什么」。

---

## 一句话定位

**分镜只引用资产编号，不重述资产描述；三件套是唯一真源，分镜与提示词都锚定它，防止两处描述打架。**

---

## 三条核心承诺

| 承诺 | 含义 | 靠什么兑现 |
|---|---|---|
| **不漂移** | 角色/场景/道具先锁定再进分镜（Asset-First），跨镜一致性有据可依 | 资产台账 A/B/C 分级 + `asset_check.py`（台账质检 + 台账×分镜交叉）+ `validate.py` C06 防换脸 |
| **不返工** | 错误拦在生成之前，不投喂半成品 | 🔒 前置锁（7 道强制勾选）+ 投喂必查清单 + `validate.py` P0~P2 分级门禁 + 六道闸门 `gate.py` |
| **能直接投喂** | 输出七段式结构化提示词，整组复制即可喂给视频模型 | `prompt_build.py` 七段式组装 + `board.py` 导出 `feed.txt` 投喂文本 |

> 三条承诺都有**脚本落地**，不是口号：不漂移 → `asset_check.py`；不返工 → `validate.py` + `gate.py`；能直接投喂 → `prompt_build.py` + `feed.txt`。

---

## 能解决什么问题

AI 短剧/影视生成最常见的几类翻车，本 skill 用「规则 + 机械检查」提前拦住：

| 翻车 | 对应防线 |
|---|---|
| 同一角色换镜头就变脸 | 防换脸锚定 + `validate.py` C06 检查 |
| 台词读不完（时长超标） | 语速硬校验 + C04 检查 |
| 场景/道具/人物对不上号 | 资产编号引用 + C05 检查 |
| 打戏血腥过审风险 | 安全转译词典 + C11 检查 |
| 用户没说清参数 agent 瞎猜 | 🔒 前置锁（强制勾选） |
| 半成品投喂浪费算力 | 六道闸门 `gate.py` |

---

## 目录结构

```
ip-make-pipeline/
├── SKILL.md                      # 主入口：前置锁 + 四阶段流程 + 三条铁律
├── references/                   # 规则库（agent 按需加载，不全部展开）
│   ├── storyboard-format.md      #   分镜表 11 字段规范
│   ├── asset-binding.md          #   资产绑定 + A/B/C 分级
│   ├── staging.md                #   站位声明 + 180° 轴线 + 位移链
│   ├── shot-language.md          #   文武双模 + 运镜 5 模式 + 景别词典
│   ├── prompt-engine.md          #   七段式提示词 + 禁令三改法
│   ├── compliance-translate.md   #   动作戏安全转译词典（合规）
│   ├── emotion-curve.md          #   情绪 12 节拍曲线 + 峰值校验
│   ├── feed-checklist.md         #   投喂必查清单（六道闸门人工版）
│   ├── overseas-shots.md         #   海外剧分镜适配（赛道②：英文语言契约）
│   └── economy.md                #   经济性 + 机械检查分级
└── tools/                        # 可执行工具链（Python 纯标准库）
    ├── ipmake/
    │   ├── asset_check.py        #   资产台账质检（check + cross）
    │   ├── series_check.py       #   跨集一致性质检（check + series）
    │   ├── validate.py           #   分镜质检（C1~C12 检查码 + P0~P2 分级）
    │   ├── gate.py               #   投喂层六道闸门
    │   ├── prompt_build.py       #   七段式提示词组装器
    │   ├── board.py              #   离线看板（HTML + SRT + CSV + JSON + feed.txt）
    │   └── cli.py                #   统一入口 + pipeline 一键编排
    └── README.md                 #   工具链使用说明
```

---

## 安装

本 skill 是 WorkBuddy skill，安装到用户级目录即可全局可用：

```bash
# 复制到用户级 skills 目录
cp -r ip-make-pipeline ~/.workbuddy/skills/
```

### 工具链环境要求

脚本为 **Python 3.8+ 纯标准库**，无第三方依赖，无需 `pip install`。

```bash
python --version   # 确认 ≥ 3.8
```

---

## 快速上手

### 1. 前置锁（动手前强制勾选）

任何一道未指定，停下询问：**赛道 / 模型版本 / 画幅 / 交付形态 / 段缝衔接 / 单镜时长 / 画风锁**。详见 `SKILL.md`。

### 2. 四阶段流水线

```
① 资产绑定 → ② 分镜表 → ③ 构图/运镜 → ④ 成片提示词 → 交付看板
```

| 阶段 | 产出 | 工具 |
|---|---|---|
| ① 资产绑定 | 资产台账（A/B/C 分级 + 编号映射） | 人工/agent |
| ② 分镜表 | 逐镜分镜表（11 字段 JSON） | `validate.py` |
| ③ 构图/运镜 | 站位声明 + 构图方案 + 运镜标注 | `validate.py` |
| ④ 成片提示词 | 七段式提示词 | `prompt_build.py` |
| 交付 | 离线分镜看板 | `board.py` |

### 3. 工具链命令行

```bash
cd tools/ipmake

# ⓪ 资产台账质检（阶段①）
python asset_check.py check assets.json
python asset_check.py cross assets.json storyboard.json

# ①.5 跨集一致性（多集防换脸，全季共用一份台账）
python series_check.py check assets.json storyboard.json
python series_check.py series assets.json storyboard_ep01.json storyboard_ep02.json

# ① 质检分镜表（P0 硬错误必须清零）
python validate.py storyboard.json --json

# ② 组装七段式提示词
python prompt_build.py storyboard.json assets.json staging.json -o prompts.json

# ③ 投喂前六道闸门
python gate.py storyboard.json prompts.json validate_report.json

# ④ 导出离线看板（HTML + SRT + CSV + JSON）
python board.py storyboard.json prompts.json -o board.html

# 一键编排（validate → build → gate → board）
python cli.py pipeline storyboard.json assets.json staging.json -o board.html
```

### 4. 分镜表 JSON schema（核心输入）

```json
{
  "title": "《剧名》第1集 分镜表",
  "target_duration": 90,
  "total": { "shots": 12, "duration": 53 },
  "staging": "S03 营地，梁大背对冰湖站中央，梁小在其右手",
  "style": { "visual": "写实", "tone": "冷色调", "light": "自然光", "sound": "环境音+弦乐" },
  "shots": [
    {
      "shot_id": 1,
      "duration": 3,
      "description": "夜幕下，林梓泳撬开古董店后门",
      "characters": "P01 林梓泳",
      "scene": "S01 古董店后巷",
      "props": "D01 撬棍",
      "dialogue": "对白【林梓泳：\"手艺人，不问来路。\"】",
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

完整 schema 与检查码说明见 `tools/README.md`。

---

## 三条核心铁律

1. **分镜只引资产编号，不重述**——长相/造型/材质一律回查三件套。
2. **防换脸是头号难题**——逐镜锚定定妆单编号，重复锚定「一人一版、面部干净、无光斑」。
3. **时长与语速硬校验**——台词字数 ÷ 语速（中文 4.5~6.5 字/秒）≤ 镜时长。

---

## License

[MIT](./LICENSE)
