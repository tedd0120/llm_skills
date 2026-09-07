# Codex 展示层推荐

本规范仅在当前运行环境标识为 `codex`（大小写不敏感）时查阅执行。

## 数据获取

在展示 subagent 模型与思考强度配置表时，先读取 [Codex 雷达](https://codex-reset-radar.pages.dev/) 的 `https://codex-reset-radar.pages.dev/data/intelligence-efficiency.json`。

读取顺序：
1. 优先使用当前可用的网页工具读取完整 JSON URL。
2. 网页工具不可用或受限时，改用当前环境允许的只读 HTTPS 客户端（如 `curl` 或 `Invoke-WebRequest`）获取。
3. 成功获取且可解析为 JSON 时继续生成推荐；均失败时跳过推荐行，继续正常流程。

## 候选筛选与推荐计算

- 候选条件：`harness == "codex"` 且包含数值 `iq`、`average_price_usd` 的模型档位。
- 计划已限定模型族时按计划筛选；未限定时取最新的 `gpt-*` 主模型系列。
- **执行者推荐**：IQ ≥ 95 中价格最低的档位。
- **任务审查者推荐**：IQ ≥ 100 中价格最低的档位。
- **最终整体审查**：IQ 最高的档位。
- 门槛无候选时，该角色取 IQ 最高的档位（三个角色可共用同一档位）。
- 价格使用 `average_price_usd`（美元/基准任务）；日期使用 `source_updated_at`（北京时间日期）。

## 输出格式

推荐行保持单行极简格式：

```text
Codex 推荐：执行者 <档位> IQ <分数> / $<价格> · 任务审查者 <档位> IQ <分数> / $<价格> · 最终整体审查 <档位> IQ <分数> / $<价格> · 更新 <YYYY-MM-DD>
```

该行仅供参考，派发仍采用用户确认后的配置。缺少更新日期时跳过。
