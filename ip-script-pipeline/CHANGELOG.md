# Changelog

本文件记录 `ip-script-pipeline` 的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

> 说明：本 skill 是最早建立的一层，早期未同步铺开源三件套（README/CHANGELOG/LICENSE）。本文件从补齐三件套之日起开始记录，并回溯记录了赛道扩展等关键变更。

## [Unreleased]

### Fixed（修复）

- **英文语速数字矛盾（硬错误，跨层）**：本层 `overseas-adapter.md` 原写「英文 2.5~3.5 词/秒」，与制作层 `ip-make-pipeline` 校验脚本的「2.0~2.8 词/秒」打架——同样一句台词，本层说读得完、制作层判超时。统一为 **2.0~2.8 词/秒**（以制作层校验脚本为最终口径），改了 `overseas-adapter.md` 两处（转译铁律 + 节奏重排表）。
- **`SKILL.md` 阶段0赛道表海外剧语速格为空**：赛道①写了「中文字/秒」、赛道③写了「4.5~6.5 字/秒」，赛道②（海外剧）语速格缺失。补「英文 2.0~2.8 词/秒」，三条赛道语速齐全且口径统一。

### Added（新增）

- **赛道硬分流（阶段0）**：`SKILL.md` 新增「🔒 赛道硬分流」——① 国内剧走六阶段编剧链；② 海外剧走六阶段链 + 英文对白适配层；③ 解说叙事走解说剧本链（旁白稿 VO Script，非分集对白剧本）。
- **`references/overseas-adapter.md`**：海外剧英文对白适配层（中文写→英文适配、词/秒语速 2.0~2.8、海外节奏重排）。
- **`references/jieshuo-script.md`**：解说剧本链（选题→考据→结构→旁白→画面匹配），产出旁白稿 + 画面提示表 + 字幕稿 + 考据来源。交付物现转交 `ip-jieshuo-pipeline`（解说成片流水线）。

### Changed（变更）

- `jieshuo-script.md` 交付物说明：从「解说类直接进素材剪辑（无承接）」改为「转交 `ip-jieshuo-pipeline`」，消除成片环节的断档。

## [0.1.0] - 2026-10-24（回溯）

### Added（新增）

- 六阶段编剧链（A1~A6）+ B 先导片 + C 分集的基础规则体系。
- `references/` 下规则文件：`stage-a.md` / `stage-b.md` / `stage-c.md`（分阶段）、`economy.md`（经济性）、`quality-modules.md`（质量模块）、`make-spec.md`（三件套规范）、`packages.md`（交付物 package 约定）。
