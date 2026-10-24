# Changelog

本文件记录 `ip-make-pipeline` 的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added（新增）

- **跨集一致性（兑现「不漂移」承诺的最后一公里）**：防换脸从「单集内跨镜」升级到「跨集回锚定妆单」。
  - 新增 `tools/ipmake/series_check.py`：跨集一致性质检。两个子命令——`check`（单集回锚：face_anchor 是否 = 台账 face、编号 name 是否一致、**人物集合双向对齐**）、`series`（多集回锚：跨集同一角色无多套面部描述、A 级人物台账都有 face、**A 级人物全季出场连续性**）。
  - 新增 `references/series-consistency.md`：跨集一致性规则（face_anchor 是「回锚定妆单」不是「现场自由描述」+ 三个层面 + 与 C06 分工）。
  - `cli.py` 新增 `series` 子命令；`SKILL.md` 补「①.5 跨集一致性」阶段 + 承诺标注 + 铁律 2 补跨集回锚；`tools/README.md` 补 series_check 说明。
  - 根因：原 C06 只在单集内比对首镜 vs 后续镜，跨集时各集 face_anchor 各自漂移无人比对。定妆单 `assets.json[Pxx].face` 才是唯一真源，face_anchor 应逐字等于它。

- **赛道对齐（制作层）**：打通剧本层三赛道，制作层不再「只认国内剧」。
  - 新增 `references/overseas-shots.md`：海外剧分镜适配——语言契约换英文（对白英文、语速换「词/秒」）、海外平台节奏重排（单镜默认 4s、开场钩子前置）、工具链 `language` 字段识别。
  - `SKILL.md` 〇·0 赛道锁更新：① 国内剧完整四阶段；② 海外剧完整四阶段 + 英文契约；③ 解说叙事明确「不适用本流水线」（旁白稿走素材剪辑，不是分镜）。
- **`validate.py` 支持赛道语速切换**：C04 语速校验按分镜表顶层 `language` 字段（`zh`/`en`）切「字/秒」（4.5~6.5）vs「词/秒」（2.0~2.8），`count_chars` 对英文按词计数。

### Fixed（修复）

- **全库逻辑检查修复**（跨三个 skill 的全面 review，发现并修复 5 处错误 + 1 处代码重构）：
  - **英文语速数字矛盾（硬错误）**：剧本层 `overseas-adapter.md` 写「英文 2.5~3.5 词/秒」，与本层 `validate.py` 的「2.0~2.8 词/秒」打架——同样一句台词剧本层说读得完、脚本判超时。统一为 **2.0~2.8 词/秒**（以制作层校验脚本为最终口径），改剧本层 2 处。
  - **`feed-checklist.md` 漏「跨集回锚」检查项**：做完跨集一致性后，投喂清单仍只有「跨镜面部描述一致」，漏了「跨集回锚已过（series_check）」。补为第 5 项，六项 → 七项。
  - **`shot-language.md` 景别跳变口径矛盾**：文档称「景别连续性纪律」（硬约束语气），脚本 C07 实为 P1（建议不阻塞）。统一为 P1 建议口径。
  - **`emotion-curve.md` 峰值位置数字打架**：文档说「第 9 节拍 ≈ 75%」，脚本 C12 用 0.7（70%）。补「5% 容差」说明。
  - **`series_check.py` name 校验盲区（代码重构）**：原用拼接字符串 + 正则提取编号后第一个词，多编号连写 `P01 林梓泳 P02 沈青蓉` 时 P02 名字漂移会漏检。重构为 `_ref_name_pairs` 逐字段精确解析，删除死代码 `_refs_in_shot`。针对性测试确认多编号连写的名字漂移能被精确抓取。
  - **`validate.py` docstring 检查码数字残留**：第 5 行写「C1~C26」，实际只有 C1~C12。改为 C1~C12。
  - **`series_check.py` 子编号 name 校验盲区**：`_ref_name_pairs` 正则 `([PSDV]\d{2})` 不认子编号 `P01-A`（`asset-binding.md` 明确「多套服装用 P01-A/P01-B 子编号」），分镜写 `P01-A 某名` 时 name 漂移漏检。改为 `([PSDV]\d{2}(?:-[A-Z])?)` 支持子编号后缀。
  - **`neutral_shot` 字段脚本用了但文档没定义**：`validate.py` C10 用 `neutral_shot` 判断中性镜头换轴，但 `storyboard-format.md` 字段映射表和 `staging.md` 都没写这个 JSON 字段，agent 照文档写不会填。已补字段说明 + 轴线锁落盘说明。
  - **README 命令与结构脱节**：`tools/README.md` 第 102 行写 `python build.py`（实际是 `prompt_build.py`）；主 README 目录树漏 `series_check.py`、快速上手漏 `series`/`asset` 子命令。已修正补齐。
  - **清理 3 处未使用 import**：`prompt_build.py` 的 `sys`、`series_check.py` 的 `os`。

- **英文赛道逻辑漏洞**（逻辑检查发现，海外剧赛道宣称支持但部分检查形同虚设）：
  - `C05 资产引用`：原用 `[\u4e00-\u9fff]{2,}` 只匹配中文，英文剧的裸描述（没写编号）不会被抓到。改为按 `language` 分流：英文非空且无编号前缀即报，中文保留「人物资产」等标签词白名单。
  - `C08 运镜分割`：原 `re.split(r'[+、/]')` 不切英文逗号/分号，英文多运镜组合无法逐项校验。分割符补 `,，;；`。
  - `C06 防换脸报错`：`f"P{pid}"` 里 `pid` 已是 `P01` 形式，导致报错显示「PP01」双 P。改为 `f"{pid}"`。
  - `C11 安全转译`：敏感词原本只有中文，英文剧的 blood/gore/severed 等不检测。补英文敏感词（blood/gore/decapitat/dismember 等）。

- **英文赛道词典缺失**（真实跑海外剧案例发现）：`validate.py` 的运镜/构图/景别/武戏相位关键词词典原本只有中文，英文剧的 `static`/`push-in`/`close-up` 等全被判「不在词典」误报。已加英文别名（中英双语，向后兼容）。
- **`gate.py` 闸门4 人脸锚定逻辑缺陷**：原逻辑在提示词文本里找「定妆」「面部」两个中文词判断是否锚定，英文剧必误报，且判断依据本身错误（面部特征在 storyboard 的 `face_anchor` 里，不在提示词里）。重构为「扫描分镜表，凡 characters 引用的 Pxx 编号必须都在 face_anchor 里出现」。
- **`prompt_build.py` 硬编码中文未按语言切换**：强制禁止项、画风/音效默认值、空镜/场景占位符原本硬编码中文，海外剧提示词会混入中文。已加 `language` 参数按 `zh`/`en` 切换。

- **`validate.py` 镜头号偏移 bug**：检查函数用 0-based index 上报，导致报告里的「镜N」与实际分镜号（1-based）错位 1 位。现在 `run_validate` 统一把 index 转为 `shot_id` 上报（表尾合计行显示为「合计行」）。
- **`prompt_build.py` 七段式拼接格式 bug**：原 `"【" + "】→【".join(f"{k}】...")` 导致每段内容后多一个 `】`，段名前的 `【` 缺失。改为 `" → ".join(f"【{k}】{segs[k]}")`，输出正确的 `【画风风格】内容 → 【场景资产】内容` 格式。

### Changed（变更）

- **文档与实现对齐**：
  - `economy.md`：检查码数字「C1~C11」→「C1~C12」；P0/P1/P2 门槛的典型检查项按实际 C07/C10 为 P1 修正；机械检查清单补全 C11、C12。
  - `compliance-translate.md`：「待接入 C 类检查码」→ 明确已接入 C11（P1），并澄清与 `gate.py` 闸门5 违禁词清单的区别。
  - `emotion-curve.md`：「待接入 C 类检查码」→ 明确已接入 C12 峰值校验。
  - `storyboard-format.md`：新增「字段 ↔ JSON key 映射」表，澄清表格版 11 字段（人看）与 JSON schema（脚本消费）的对应关系。
  - `tools/README.md`：检查码数字「C1~C11」→「C1~C12」。

## [0.1.0] - 2026-10-24

### Added（新增）

- **规则层 7 个 references**：
  - `storyboard-format.md` 分镜表 11 字段规范（对标《逆境》分镜表）
  - `asset-binding.md` 资产绑定 + A/B/C 分级（借鉴 Asset-First）
  - `staging.md` 站位声明 + 180° 轴线 + 位移链（借鉴「空间」模块）
  - `shot-language.md` 文武双模 + 运镜 5 模式 + 景别词典
  - `prompt-engine.md` 七段式提示词 + 禁令三改法（借鉴 P0+P1 最核心两条）
  - `compliance-translate.md` 动作戏安全转译词典（血腥→气浪/火花/定格）
  - `economy.md` 经济性 + 机械检查分级（P0~P2 门槛）
- **工具链 4 个脚本（Python 纯标准库）**：
  - `validate.py` 质检（C1~C11 检查码 + P0~P2 分级）
  - `gate.py` 投喂层六道闸门
  - `prompt_build.py` 七段式提示词组装器
  - `board.py` 离线看板（HTML + SRT + CSV + JSON 导出）
  - `cli.py` 统一入口
- **🔒 前置锁**：赛道 / 模型版本 / 画幅 / 交付形态 / 段缝衔接 / 单镜时长 / 画风锁，7 道强制勾选（补了原「六道前置锁」漏掉的「时长锁 E」）。
- **C11 安全转译检查码**：敏感词（血腥/断肢）命中自动提示合规改写，对接 `compliance-translate.md`。

### Changed（变更）

- 定位从「纯规则文档」升级为「规则 + 可执行工具链」。
- 前置锁画风锁从「提示词里一段文字」升级为「锁定后全片冻结的资产」。

### Fixed（修复）

- `validate.py` C06 防换脸：多角色镜 `face_anchor` 按 `；` 拆分后按角色比对，不再误报。
- `validate.py` C02 字段检查：区分「键缺失」与「值为空」，`dialogue`/`characters` 允许空镜（无台词/无人物合法）。
- `board.py` `esc()`：`shot_id`/`duration` 为 int 类型时先转 str，修复 `AttributeError`。
- `validate.py` `count_chars()`：正则字符类引号歧义导致的 `SyntaxWarning` / `SyntaxError`。

### 验证

- 用《跨界追夫》第 1 集（12 镜）真实跑通全链路：`validate`（P0 通过）→ `prompt_build`（12 条七段式）→ `gate`（六道闸门全过）→ `board`（HTML/SRT/CSV/JSON）。
