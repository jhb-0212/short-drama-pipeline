# Changelog

本文件记录 `ip-jieshuo-pipeline` 的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Fixed（修复）

- **`board.py` SRT 字数口径与 `validate.py` 不一致（硬 bug）**：`build_srt` 原用 `len([c for c in narration if c.strip()])` 统计（算标点），而 `validate.py` 的 `count_chars` 去标点、只算中英文+数字。导致 V2 语速校验说「读得完」，SRT 时间轴却按偏长口径分配时长，最终字幕总时长偏长。统一为 `count_chars` 同款正则口径。
- **`vo-format.md` 漏 `aspect`（画幅）字段**：SKILL 前置锁 F、`prompt_build.py`、示例数据都用 `aspect`，但 JSON schema 和字段说明表都没写，agent 照文档写旁白稿会漏掉画幅。已补字段定义 + 字段表条目。
- **`gate.py` 闸门2 判断逻辑粗糙**：原用 `str(p)` 隐式序列化判断【画面】【字幕】，改为精确读 `p.get("prompt")` 字段，避免边界误判。
- **`copyright` 字段双源冗余**：版权状态原来同时出现在旁白稿 `vo.json` 和素材匹配表 `assets.json` 的 segment 里，V7 只认 assets、V4 却要求 vo 非空，两处必填可能不一致。明确「版权唯一真源 = 素材匹配表」，从 `vo-format.md` 和 `validate.py` V4 移除版权要求，`board.py` 看板版权列只从 assets 读，`examples/vo.json` 同步清理。
- **清理 1 处未使用 import**：`prompt_build.py` 的 `sys`。

## [0.1.0] - 2026-10-24

### Added（新增）

- **解说成片流水线（首个版本）**：承接剧本层赛道③解说叙事的成片环节，补齐了「旁白稿 → 成片」的空档。
  - **规则层 4 个 references**：
    - `vo-format.md` 旁白稿字段规范 + 语速校验（`字数 ÷ 语速 ≤ 时长`）
    - `asset-match.md` 素材匹配表 + 版权分级（公共领域/需授权/自摄）
    - `prompt-guide.md` 成片提示词（两段式【画面】→【字幕】，区别于分镜七段式）
    - `subtitle-format.md` 字幕稿 + SRT 规范（主字幕 + 强调字幕两级）
  - **工具链 5 个脚本（纯标准库）**：
    - `validate.py` 质检（V1~V8：结构/语速超时/段落对齐/字段完整/字数准确/违禁词/版权缺失/字幕漂移）
    - `prompt_build.py` 两段式成片提示词组装器
    - `gate.py` 投喂层三道闸门（段落对齐/提示词组装/质检通过）
    - `board.py` 离线解说看板（HTML + SRT + CSV）
    - `cli.py` 统一入口 + pipeline 一键编排
  - **🔒 前置锁**：赛道确认 / 解说类型 / 时长 / 语速 / 交付形态 / 素材来源 / 画幅，7 道强制勾选。
  - **examples/**：历史人物志真实案例（5 段旁白，全链路跑通）。

### 定位说明

- 与 `ip-make-pipeline`（分镜流水线）**平行**：解说类不做分镜，走素材剪辑。
- 与 `ip-script-pipeline`（剧本层）**衔接**：消费其赛道③产出的解说稿 package。

### 验证

- 用历史人物志《他活了83岁，却只被记住最后10秒》（5 段旁白）真实跑通全链路：`validate`（V5 字数检查正确拦截手填错误后，P0 通过）→ `prompt_build`（5 条两段式）→ `gate`（三道闸门全过）→ `board`（HTML/SRT/CSV）。
