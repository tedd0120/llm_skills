---
name: litellm-model-speedtest
description: 列出 LiteLLM 网关（或任意 Anthropic Messages 兼容端点）的全部模型并批量测速，输出连通性、首字延迟(TTFT)、端到端 token/秒 的排序报告。用户要求"列出某网关/某 provider 的所有模型"、"测速"、"连通性+首字延迟+token每秒"、"对比模型速度"时使用。
---

# LiteLLM 网关全量模型测速

从网关的 `/v1/models` 拉取完整模型清单，对每个模型进行流式对话测速，输出按 TPS 与首字延迟排序的交互式报告。默认针对 360 LiteLLM 网关，支持参数切换至任意兼容网关。

## 何时使用

- 用户要求列出某网关的**所有**模型并测速。
- 需要测试模型的连通性、首字延迟（TTFT）与端到端吞吐率（TPS）。
- 需要在同模型的多个部署节点（如 `m1/`、`360/`、`-openai`）之间选优。

*注：360 网关本地代理配置、超时与失败归因规则见 [references/gateway-quirks.md](references/gateway-quirks.md)。*

---

## 执行步骤

### 1. 运行测速脚本

通过本技能脚本执行测速（产物默认写入仓库根目录 `data/litellm-model-speedtest/`）：

```bash
# 全量测速（默认并发 8，每模型 max_tokens 512）
python "<skill-dir>/scripts/speedtest.py"

# 仅列出模型全量清单与元信息（不发起对话测速）
python "<skill-dir>/scripts/speedtest.py" --list-only

# 自定义网关地址与参数
python "<skill-dir>/scripts/speedtest.py" \
  --base-url https://gateway.example.com --api-key sk-xxx \
  --proxy http://127.0.0.1:7897 --concurrency 6 --timeout 120
```

- 测速完成后脚本会自动使用默认浏览器打开自包含 HTML 报告（`data/litellm-model-speedtest/speedtest.html`）。
- 若需推送报告至远程 Web 服务器，参考 [references/deploy-remote.md](references/deploy-remote.md)。

### 2. 解读输出并回复用户

- **首字延迟 (TTFT)**：首个可见文字输出耗时。若为推理模型，会先输出 `thinking_delta`，报告将同时呈现思考与正文延迟。
- **端到端 TPS**：单位时间输出 Token 速率（tokens/s）。
- **回复要求**：在终端向用户贴出精简结论与 HTML 报告文件路径，并在最后主动询问：
  `"如需为本地 Pi（360 provider）新增或删除模型，可直接告诉我模型名。"`

### 3. 后续模型同步

当用户要求增删本地 Pi 模型时，查阅 **[references/pi-models-sync.md](references/pi-models-sync.md)** 修改 `~/.pi/agent/models.json`。

---

## 验证与验收

- 脚本正常完成时输出 `HTML 报告: <绝对路径>` 与 `JSON 结果: <绝对路径>`。
- 确认生成的 HTML 报告可在浏览器完整浏览且支持卡片排序与搜索。
