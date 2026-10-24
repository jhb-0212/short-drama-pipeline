# 跨集一致性（Series Consistency）

> 定位：防换脸不能只做「单集内跨镜」，更要「跨集回锚定妆单」。本文件定义跨集一致性的规则与工具用法。
> 背景：原 C06 防换脸只在**单集分镜表内**比对首镜 vs 后续镜的 `face_anchor`，不知道上一集这个角色长什么样。跨集时各集 `face_anchor` 各自漂移（第 1 集写「圆脸」，第 10 集写「瓜子脸」），脚本都判「通过」。本文件补上这个缺口。

---

## 一、核心原则：face_anchor 不是「现场自由描述」，是「回锚定妆单」

定妆单（`assets.json` 里 `Pxx.face`）是唯一真源。分镜表里的 `face_anchor` 必须**逐字等于**定妆单的 `face`，不是「意思相近」。

| 做法 | 结果 |
|---|---|
| ✅ 回锚：`face_anchor: "P01：圆脸、细长眼、黑色短发、浅麦色皮肤"`（= 定妆单） | 跨集一致，可合片 |
| ❌ 现场重写：`face_anchor: "P01：瓜子脸、丹凤眼、棕色长发"`（≠ 定妆单） | 跨集换脸，报错 |

**纪律**：分镜时**不要自己发挥写 face_anchor**，而是**从定妆单复制** `Pxx.face` 粘贴进来。发现分镜与定妆单打架 → 回改定妆单（或剧本），不在分镜里硬改。

---

## 二、跨集一致性的五个层面

| 层面 | 检查什么 | 工具 |
|---|---|---|
| 1. 人脸回锚 | 每集 `face_anchor` 是否 = 台账 `face` | `series_check.py check/series` |
| 2. 编号 name 一致 | 分镜引用的 `Pxx 名字` 是否 = 台账 `name` | `series_check.py check/series` |
| 3. 人物集合对齐 | `characters` 里的人物 与 `face_anchor` 里的人物必须是同一集合（防本镜脱锚/漏登记） | `series_check.py check/series` |
| 4. 跨集出场连续 | A 级人物在全季至少出场一次（防漏戏/漏分镜） | `series_check.py series` |
| 5. 全季共享台账 | 所有集共用同一份 `assets.json`，不私自新增/改名编号 | `series_check.py series` |

---

## 三、工具用法

### 单集回锚（每集写完后跑）

```bash
python series_check.py check assets.json storyboard_ep01.json
```

校验这一集的 `face_anchor` 是否回锚定妆单、编号 name 是否一致。

### 全季回锚（全季收尾合片前跑）

```bash
python series_check.py series assets.json storyboard_ep01.json storyboard_ep02.json ... storyboard_ep24.json
```

校验：①每集都回锚定妆单 ②跨集同一角色无多套面部描述 ③A 级人物台账都有 `face`（回锚的前提）④人物集合双向对齐 ⑤A 级人物全季出场连续性。

### 通过 cli 统一入口

```bash
python cli.py series check assets.json storyboard_ep01.json
python cli.py series series assets.json ep01.json ep02.json ...
```

---

## 四、跨集一致性 vs 单集 C06 的分工

| 检查 | 范围 | 工具 | 查什么 |
|---|---|---|---|
| C06 防换脸 | 单集内跨镜 | `validate.py` | 首镜 vs 后续镜 `face_anchor` 一致 |
| 跨集回锚 | 多集之间 | `series_check.py` | 各集 `face_anchor` 都 = 定妆单 `face` |

两者**互补不重复**：C06 保证「单集内不换脸」，series_check 保证「跨集不换脸」。真正的防换脸 = 两把锁都上。

---

## 五、台账的跨集前提（回锚能做的地基）

- **A 级人物必须有 `face`**：主角/反派是跨集出现最多的，必须写死面部，否则无法回锚（series_check 会报「A 级人物缺 face」）。
- **全季共享一份 `assets.json`**：不按集拆台账。新角色/新场景/新道具在**首次出场前**加进同一份台账（对应 asset-binding.md 的 A1 按需补充），而不是各集自建小台账。
- **编号全程唯一、不换主编号**：同一人物换装用 `P01-A/P01-B` 子编号，不换 `P01`（主编号=人脸）。

---

## 六、边界

1. **不替代 C06**：跨集回锚查的是「集与集、集与台账」之间，C06 查的是「单集内镜与镜」，都要跑。
2. **face_anchor 逐字相等**：不是模糊匹配，是精确相等。定妆单写「圆脸」，分镜写「圆脸蛋」也算漂移（会让 AI 生成时产生细微差异累积成大偏差）。
3. **名字也精确**：`P01 林梓泳` 里的「林梓泳」必须 = 台账 `name`，防跨集把角色名写错（「林梓泳」→「林梓永」这种错字）。
4. **人物集合对齐的宽松度**：`characters` 有但 `face_anchor` 漏锚时，只有 **A 级人物**报错（主角/反派脱锚=防换脸失效）；B/C 级（群演）可只写编号不锚脸。反过来 `face_anchor` 有但 `characters` 漏写，任何等级都报（人物在镜头里却没登记，属于分镜漏写）。
