# Changelog

本文件记录 `short-drama-pipeline`（含三个子 skill）的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

> 说明：变更按「子 skill」分区记录（跨层改动往往同时触及多层，统一在此汇总，避免散落）。三个子 skill 可独立 `cp -r` 安装（见各自 README），故各自保留独立 LICENSE；CHANGELOG 则统一在本文件维护。

---

## [Unreleased]

### 顶层（跨层）

#### Added（新增）

- **对标情报搜集（`ip-script-pipeline/references/benchmark.md`）**：补齐流水线「只从 IP 出发、不看市场对标」的缺口。新增对标情报搜集规范——对标作品池 / 结构拆解表（钩子秒位、单集时长、付费卡点、反转频率、情绪节拍、开场信息密度）/ 赛道趋势表（题材 × 三赛道热度矩阵 + 生命周期）/ 数据基准（可选，采不到标「无公开数据」）。校准阶段 0「题材热度 / 平台匹配 / 商业潜力」打点与赛道硬分流，校准 A4 分集规划的钩子/付费点。接线 5 处：`SKILL.md`（阶段 0 前置 + 赛道分流纪律第 4 条）、`packages.md`（对标情报门禁）、`economy.md`（上下文隔离清单）、`stage-a.md`（A4 钩子/付费点接结构拆解表）。

#### Fixed（修复）

- **阶段 0 打点字段口径**：明确「题材热度 / 平台匹配 / 商业潜力」三项依赖对标情报，「改编适配度」为纯文本判断不依赖情报；「赛道」为分流结论而非打点字段；结构拆解表「单集时长」落点校准 A3 平台节奏矩阵（原误指阶段 0）。
- **对标样本选择逻辑环**：无赛道意向时「先定赛道才能选样本、先选样本才能定赛道」的死循环，补「三赛道各采 1~2 部初筛 → 定赛道 → 补足该赛道样本」的打破规则。

#### Changed（变更）

- **CHANGELOG 合并**：4 份 CHANGELOG（顶层 + 3 子 skill）合并为顶层 1 份，按子 skill 分区维护，便于跨层改动统一追踪。

### ip-script-pipeline（剧本层）

#### Fixed（修复）

- **英文语速数字矛盾（硬错误，跨层）**：本层 `overseas-adapter.md` 原写「英文 2.5~3.5 词/秒」，与制作层 `ip-make-pipeline` 校验脚本的「2.0~2.8 词/秒」打架——同样一句台词，本层说读得完、制作层判超时。统一为 **2.0~2.8 词/秒**（以制作层校验脚本为最终口径），改了 `overseas-adapter.md` 两处（转译铁律 + 节奏重排表）。
- **`SKILL.md` 阶段0赛道表海外剧语速格为空**：赛道①写了「中文字/秒」、赛道③写了「4.5~6.5 字/秒」，赛道②（海外剧）语速格缺失。补「英文 2.0~2.8 词/秒」，三条赛道语速齐全且口径统一。

#### Added（新增）

- **赛道硬分流（阶段0）**：`SKILL.md` 新增「🔒 赛道硬分流」——① 国内剧走六阶段编剧链；② 海外剧走六阶段链 + 英文对白适配层；③ 解说叙事走解说剧本链（旁白稿 VO Script，非分集对白剧本）。
- **`references/overseas-adapter.md`**：海外剧英文对白适配层（中文写→英文适配、词/秒语速 2.0~2.8、海外节奏重排）。
- **`references/jieshuo-script.md`**：解说剧本链（选题→考据→结构→旁白→画面匹配），产出旁白稿 + 画面提示表 + 字幕稿 + 考据来源。交付物现转交 `ip-jieshuo-pipeline`（解说成片流水线）。

#### Changed（变更）

- `jieshuo-script.md` 交付物说明：从「解说类直接进素材剪辑（无承接）」改为「转交 `ip-jieshuo-pipeline`」，消除成片环节的断档。

### ip-make-pipeline（制作层）

#### Added（新增）

- **跨集一致性（兑现「不漂移」承诺的最后一公里）**：防换脸从「单集内跨镜」升级到「跨集回锚定妆单」。
  - 新增 `tools/ipmake/series_check.py`：跨集一致性质检。两个子命令——`check`（单集回锚：face_anchor 是否 = 台账 face、编号 name 是否一致、**人物集合双向对齐**）、`series`（多集回锚：跨集同一角色无多套面部描述、A 级人物台账都有 face、**A 级人物全季出场连续性**）。
  - 新增 `references/series-consistency.md`：跨集一致性规则（face_anchor 是「回锚定妆单」不是「现场自由描述」+ 三个层面 + 与 C06 分工）。
  - `cli.py` 新增 `series` 子命令；`SKILL.md` 补「①.5 跨集一致性」阶段 + 承诺标注 + 铁律 2 补跨集回锚；`tools/README.md` 补 series_check 说明。
  - 根因：原 C06 只在单集内比对首镜 vs 后续镜，跨集时各集 face_anchor 各自漂移无人比对。定妆单 `assets.json[Pxx].face` 才是唯一真源，face_anchor 应逐字等于它。
- **赛道对齐（制作层）**：打通剧本层三赛道，制作层不再「只认国内剧」。
  - 新增 `references/overseas-shots.md`：海外剧分镜适配——语言契约换英文（对白英文、语速换「词/秒」）、海外平台节奏重排（单镜默认 4s、开场钩子前置）、工具链 `language` 字段识别。
  - `SKILL.md` 〇·0 赛道锁更新：① 国内剧完整四阶段；② 海外剧完整四阶段 + 英文契约；③ 解说叙事明确「不适用本流水线」（旁白稿走素材剪辑，不是分镜）。
- **`validate.py` 支持赛道语速切换**：C04 语速校验按分镜表顶层 `language` 字段（`zh`/`en`）切「字/秒」（4.5~6.5）vs「词/秒」（2.0~2.8），`count_chars` 对英文按词计数。

#### Fixed（修复）

- **全库逻辑检查修复**（跨三个 skill 的全面 review，发现并修复 5 处错误 + 1 处代码重构）：
  - **英文语速数字矛盾（硬错误）**：剧本层 `overseas-adapter.md` 写「英文 2.5~3.5 词/秒」，与本层 `validate.py` 的「2.0~2.8 词/秒」打架。统一为 **2.0~2.8 词/秒**（以制作层校验脚本为最终口径），改剧本层 2 处。
  - **`feed-checklist.md` 漏「跨集回锚」检查项**：做完跨集一致性后，投喂清单仍只有「跨镜面部描述一致」，漏了「跨集回锚已过（series_check）」。补为第 5 项，六项 → 七项。
  - **`shot-language.md` 景别跳变口径矛盾**：文档称「景别连续性纪律」（硬约束语气），脚本 C07 实为 P1（建议不阻塞）。统一为 P1 建议口径。
  - **`emotion-curve.md` 峰值位置数字打架**：文档说「第 9 节拍 ≈ 75%」，脚本 C12 用 0.7（70%）。补「5% 容差」说明。
  - **`series_check.py` name 校验盲区（代码重构）**：原用拼接字符串 + 正则提取编号后第一个词，多编号连写 `P01 林梓泳 P02 沈青蓉` 时 P02 名字漂移会漏检。重构为 `_ref_name_pairs` 逐字段精确解析，删除死代码 `_refs_in_shot`。
  - **`validate.py` docstring 检查码数字残留**：第 5 行写「C1~C26」，实际只有 C1~C12。改为 C1~C12。
  - **`series_check.py` 子编号 name 校验盲区**：`_ref_name_pairs` 正则 `([PSDV]\d{2})` 不认子编号 `P01-A`（`asset-binding.md` 明确「多套服装用 P01-A/P01-B 子编号」），分镜写 `P01-A 某名` 时 name 漂移漏检。改为 `([PSDV]\d{2}(?:-[A-Z])?)` 支持子编号后缀。
  - **`neutral_shot` 字段脚本用了但文档没定义**：`validate.py` C10 用 `neutral_shot` 判断中性镜头换轴，但 `storyboard-format.md` 字段映射表和 `staging.md` 都没写这个 JSON 字段。已补字段说明 + 轴线锁落盘说明。
  - **README 命令与结构脱节**：`tools/README.md` 第 102 行写 `python build.py`（实际是 `prompt_build.py`）；主 README 目录树漏 `series_check.py`、快速上手漏 `series`/`asset` 子命令。已修正补齐。
  - **清理 3 处未使用 import**：`prompt_build.py` 的 `sys`、`series_check.py` 的 `os`。
- **英文赛道逻辑漏洞**（海外剧赛道宣称支持但部分检查形同虚设）：
  - `C05 资产引用`：原用 `[\u4e00-\u9fff]{2,}` 只匹配中文，英文剧的裸描述不会被抓到。改为按 `language` 分流。
  - `C08 运镜分割`：原 `re.split(r'[+、/]')` 不切英文逗号/分号。分割符补 `,，;；`。
  - `C06 防换脸报错`：`f"P{pid}"` 里 `pid` 已是 `P01` 形式，报错显示「PP01」双 P。改为 `f"{pid}"`。
  - `C11 安全转译`：敏感词原本只有中文，补英文敏感词（blood/gore/decapitat/dismember 等）。
- **英文赛道词典缺失**：`validate.py` 运镜/构图/景别/武戏相位关键词词典原本只有中文，英文剧全被判「不在词典」误报。已加英文别名（中英双语，向后兼容）。
- **`gate.py` 闸门4 人脸锚定逻辑缺陷**：原逻辑在提示词文本里找中文词判断锚定，英文剧必误报，且依据本身错误（面部特征在 `face_anchor` 不在提示词）。重构为「扫描分镜表，凡 characters 引用的 Pxx 编号必须都在 face_anchor 里出现」。
- **`gate.py` 闸门3 七段检查漏段**：原只查 5 段，漏「站位声明」「音效」两段。补全 7 段。
- **`prompt_build.py` 空段跳过段名**：`if segs.get(k)` 会在空段时跳过段名，导致下游 gate 闸门3 误判缺段。改为段名始终输出。
- **`prompt_build.py` 硬编码中文未按语言切换**：强制禁止项、画风/音效默认值、空镜/场景占位符原本硬编码中文，海外剧提示词会混入中文。已加 `language` 参数按 `zh`/`en` 切换。
- **`validate.py` 镜头号偏移 bug**：检查函数用 0-based index 上报，导致报告「镜N」与实际分镜号错位 1 位。`run_validate` 统一转 `shot_id` 上报。
- **`prompt_build.py` 七段式拼接格式 bug**：原 `"【" + "】→【".join(...)` 导致每段内容后多一个 `】`、段名前 `【` 缺失。改为 `" → ".join(f"【{k}】{segs[k]}")`。

#### Changed（变更）

- **文档与实现对齐**：
  - `economy.md`：检查码数字「C1~C11」→「C1~C12」；P0/P1/P2 门槛按实际 C07/C10 为 P1 修正。
  - `compliance-translate.md`：「待接入 C 类检查码」→ 明确已接入 C11（P1），并澄清与 `gate.py` 闸门5 违禁词清单的区别。
  - `emotion-curve.md`：「待接入 C 类检查码」→ 明确已接入 C12 峰值校验。
  - `storyboard-format.md`：新增「字段 ↔ JSON key 映射」表，澄清表格版 11 字段（人看）与 JSON schema（脚本消费）的对应关系。
  - `tools/README.md`：检查码数字「C1~C11」→「C1~C12」；示例时长对齐。

### ip-jieshuo-pipeline（成片层）

#### Fixed（修复）

- **`board.py` SRT 字数口径与 `validate.py` 不一致（硬 bug）**：`build_srt` 原用 `len([c for c in narration if c.strip()])` 统计（算标点），而 `validate.py` 的 `count_chars` 去标点、只算中英文+数字。统一为 `count_chars` 同款正则口径。
- **`vo-format.md` 漏 `aspect`（画幅）字段**：SKILL 前置锁 F、`prompt_build.py`、示例数据都用 `aspect`，但 JSON schema 和字段说明表都没写。已补字段定义 + 字段表条目。
- **`gate.py` 闸门2 判断逻辑粗糙**：原用 `str(p)` 隐式序列化判断【画面】【字幕】，改为精确读 `p.get("prompt")` 字段，避免边界误判。
- **`copyright` 字段双源冗余**：版权状态原来同时出现在旁白稿 `vo.json` 和素材匹配表 `assets.json`，V7 只认 assets、V4 却要求 vo 非空，两处必填可能不一致。明确「版权唯一真源 = 素材匹配表」，从 `vo-format.md` 和 `validate.py` V4 移除版权要求，`board.py` 看板版权列只从 assets 读，`examples/vo.json` 同步清理。
- **清理 1 处未使用 import**：`prompt_build.py` 的 `sys`。

---

## [0.1.0] - 2026-10-24

### 顶层

#### Added（新增）

- **三 skill 合并为单一仓库**：`ip-script-pipeline`（剧本层）、`ip-make-pipeline`（制作层）、`ip-jieshuo-pipeline`（成片层）合并为 `short-drama-pipeline` 父项目，统一版本管理与分发。
- **顶层 README**：三 skill 关系图 + 三赛道分流表 + 三条共同承诺 + 快速上手导航。
- **顶层 LICENSE（MIT）+ .gitignore**：与三个子 skill 的许可、忽略规则对齐。

### ip-script-pipeline（剧本层）

#### Added（新增）

- 六阶段编剧链（A1~A6）+ B 先导片 + C 分集的基础规则体系。
- `references/` 下规则文件：`stage-a.md` / `stage-b.md` / `stage-c.md`（分阶段）、`economy.md`（经济性）、`quality-modules.md`（质量模块）、`make-spec.md`（三件套规范）、`packages.md`（交付物 package 约定）。

### ip-make-pipeline（制作层）

#### Added（新增）

- **规则层 7 个 references**：`storyboard-format.md`（分镜表 11 字段规范）、`asset-binding.md`（资产绑定 + A/B/C 分级）、`staging.md`（站位声明 + 180° 轴线 + 位移链）、`shot-language.md`（文武双模 + 运镜 5 模式 + 景别词典）、`prompt-engine.md`（七段式提示词 + 禁令三改法）、`compliance-translate.md`（动作戏安全转译词典）、`economy.md`（经济性 + 机械检查分级）。
- **工具链脚本（Python 纯标准库）**：`validate.py`（C1~C12 检查码 + P0~P2 分级）、`gate.py`（投喂层六道闸门）、`prompt_build.py`（七段式提示词组装器）、`board.py`（离线看板）、`cli.py`（统一入口）。
- **🔒 前置锁**：赛道 / 模型版本 / 画幅 / 交付形态 / 段缝衔接 / 单镜时长 / 画风锁，7 道强制勾选。
- **C11 安全转译检查码**：敏感词（血腥/断肢）命中自动提示合规改写。

#### Changed（变更）

- 定位从「纯规则文档」升级为「规则 + 可执行工具链」。
- 前置锁画风锁从「提示词里一段文字」升级为「锁定后全片冻结的资产」。

#### Fixed（修复）

- `validate.py` C06 防换脸：多角色镜 `face_anchor` 按 `；` 拆分后按角色比对，不再误报。
- `validate.py` C02 字段检查：区分「键缺失」与「值为空」，`dialogue`/`characters` 允许空镜。
- `board.py` `esc()`：`shot_id`/`duration` 为 int 类型时先转 str，修复 `AttributeError`。
- `validate.py` `count_chars()`：正则字符类引号歧义导致的 `SyntaxWarning` / `SyntaxError`。

#### 验证

- 用《跨界追夫》第 1 集（12 镜）真实跑通全链路：`validate` → `prompt_build` → `gate` → `board`。

### ip-jieshuo-pipeline（成片层）

#### Added（新增）

- **解说成片流水线（首个版本）**：承接剧本层赛道③解说叙事的成片环节。
  - **规则层 4 个 references**：`vo-format.md`、`asset-match.md`、`prompt-guide.md`（两段式【画面】→【字幕】）、`subtitle-format.md`。
  - **工具链 5 个脚本**：`validate.py`（V1~V8）、`prompt_build.py`（两段式组装器）、`gate.py`（三道闸门）、`board.py`（解说看板）、`cli.py`（统一入口 + pipeline 一键编排）。
  - **🔒 前置锁**：赛道确认 / 解说类型 / 时长 / 语速 / 交付形态 / 素材来源 / 画幅，7 道强制勾选。
  - **examples/**：历史人物志真实案例（5 段旁白，全链路跑通）。

#### 定位说明

- 与 `ip-make-pipeline`（分镜流水线）**平行**：解说类不做分镜，走素材剪辑。
- 与 `ip-script-pipeline`（剧本层）**衔接**：消费其赛道③产出的解说稿 package。

#### 验证

- 用历史人物志《他活了83岁，却只被记住最后10秒》（5 段旁白）真实跑通全链路：`validate` → `prompt_build` → `gate` → `board`。
