# 工具链使用说明（ip-jieshuo-pipeline）

解说成片流水线的可执行工具链，纯 Python 标准库，无第三方依赖。

## 脚本清单

| 脚本 | 作用 | 检查码/闸门 |
|---|---|---|
| `validate.py` | 旁白稿质检 | V1~V8（V1~V6 为 P0 硬错误，V7/V8 为 P1 警告） |
| `prompt_build.py` | 成片提示词组装（两段式） | — |
| `gate.py` | 投喂层三道闸门 | 段落对齐 / 提示词组装 / 质检通过 |
| `board.py` | 离线解说看板（HTML + SRT + CSV） | — |
| `cli.py` | 统一入口 + pipeline 一键编排 | — |

## 快速上手

```bash
# 一键编排（质检 → 提示词 → 闸门 → 看板）
python cli.py pipeline vo.json assets.json -o board.html

# 或分步
python validate.py vo.json assets.json          # 旁白稿质检
python prompt_build.py vo.json assets.json -o prompts.json   # 成片提示词
python gate.py vo.json assets.json prompts.json validate_report.json  # 三道闸门
python board.py vo.json assets.json prompts.json -o board.html  # 看板
```

## 输入文件

- `vo.json`：旁白稿（字段见 `references/vo-format.md`）
- `assets.json`：素材匹配表（字段见 `references/asset-match.md`）

## 与 ip-make-pipeline 工具链的区别

解说类**没有** `asset_check.py`（资产编号检查）——它没有角色资产跨镜一致性问题，只有「素材方向 + 版权」。也没有分镜的「站位/运镜」检查，换成「段落对齐（V3）/ 版权（V7）/ 字幕漂移（V8）」。
