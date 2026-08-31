---
name: litellm-model-speedtest
description: 列出 LiteLLM 网关（或任意 Anthropic Messages 兼容端点）的全部模型并批量测速，输出连通性、首字延迟(TTFT)、端到端 token/秒 的排序报告。用户要求"列出某网关/某 provider 的所有模型"、"测速"、"连通性+首字延迟+token每秒"、"对比模型速度"时使用。
---

# LiteLLM 网关全量模型测速

从网关的 `/v1/models` 拉取完整模型清单（而非本地配置的那几个），再对每个模型做流式对话测速，输出一份按 TPS/首字延迟等指标排序的报告。默认针对 360 LiteLLM Gateway（`litellm-dev.sandbox.deepbank.daikuan.qihoo.net`），可通过参数切换到任意网关。

## 何时使用

- 用户说"列出某个网关/360 provider 的**所有**模型"，而本地 `~/.pi/agent/models.json` 只配了子集时（调用本 skill 自动执行全量测速）。
- 用户要求"测速"，指标包含：连通性、首字延迟(TTFT)、token/秒(TPS)。
- 需要在同模型多个后端前缀（`m1/`、`m2/`、`360/`、`-openai` 后缀）之间选最快的部署。

## 关键事实（360 网关，先记住）

- **域名只能走本地代理**解析：必须用 `http://127.0.0.1:7897`（与 pi settings 的 `httpProxy` 一致），直连会 `Could not resolve host`。
- 对话端点是 **Anthropic Messages 格式**：`POST {base}/v1/messages`，头 `x-api-key` + `anthropic-version: 2023-06-01`。
- API key 从**仓库根目录 `.env`** 的 `LLM_API_KEY` 读取（不再硬编码），缺失时脚本会报错提示；`--api-key` 或环境变量可覆盖。
- 拉模型清单用 OpenAI 风格端点：`GET {base}/v1/models`（返回可路由的模型 ID 全集），`GET {base}/model/info`（返回元信息，但**同模型名有多条部署记录**，只取第一条）。
- `/v1/models` 里混着**非对话模型**：embedding（如 `bge-m3`）、图像生成（如 `qwen-image`）、plan 类（`qwen3-*-plan-*`）、路由组（`all-team-models`）——它们测速会失败或返回空，属正常，不是网关挂了。
- 部分模型对当前 key **无权限(403)**、后端不存在(404)、无可用 channel(503)——归因后单独列示。

## 执行步骤

1. 运行脚本（`<skill-dir>` 为本 SKILL.md 所在目录）：

   ```bash
   # 只列全部模型 + 元信息（规模/上下文/视觉/推理/来源）
   python "<skill-dir>/scripts/speedtest.py" --list-only

   # 全量测速（默认并发 8，每模型 max_tokens 512）
   python "<skill-dir>/scripts/speedtest.py"

   # 自定义网关 / 调参
   python "<skill-dir>/scripts/speedtest.py" \
     --base-url https://gateway.example.com --api-key sk-xxx \
     --proxy http://127.0.0.1:7897 \
     --concurrency 6 --max-tokens 1024 --timeout 120
   ```

   测速默认在**仓库根目录** `data/litellm-model-speedtest/` 下生成固定命名的自包含 HTML 报告
   （`speedtest.html`，每次运行直接覆盖）与同名 JSON（`speedtest.json`）。`--report-dir` 改目录、
   `--no-html` 关闭 HTML、`--models` 只测子集。测速结束后脚本会用**默认浏览器自动打开 HTML 报告**，
   `--no-browser` 关闭自动打开。

2. 读取脚本输出（测速结束后默认浏览器会自动打开 HTML 报告）：
   - 终端进度行 `[n/总] ✅/❌ 模型 TTFT … E2E tok/s …` + 汇总表（可用模型按 TTFT 升序；不可用模型带失败归因）。
   - 生成的 HTML 报告（浅色主题，自包含单文件）：
     - 自动同步 GitHub `anomalyco/models.dev` 开源数据库中的模型元信息（发布日期、上下文限制、最大输出 Tokens、思考推理、视觉等多模态能力，无价格）；
     - 自动识别并归一化模型版本（如 `360/glm-5.3`、`m3/glm-5.3`、`m3/glm-5.3-openai` 归为 `GLM-5.3` 版本，`m1/deepseek-v4-flash`、`360/deepseek-v4-flash-openai` 归为 `DeepSeek V4 Flash` 版本）；
     - 按供应商（GLM / Kimi / DeepSeek / Qwen / Doubao / MiniMax 等）分类；每个供应商下将同一模型版本合并为专属卡片，**优先展示最新发布的版本（release_date 降序）**；
     - **每个模型版本卡片内各部署节点按实测端到端 TPS 降序排列**，高亮对比不同后端速度；
     - 自动读取本地 Pi（`~/.pi/agent/models.json`）中 360 provider 已配置的模型并在表格中高亮（`⚡ 已配置` 徽章 + 背景着色），点击模型名自动复制到剪贴板，顶部有「🔍 搜索模型名 / 版本名」输入框 + 供应商筛选 chips（含一键筛选「⚡ 已配置」）；打开仓库根目录 `data/litellm-model-speedtest/speedtest.html` 呈现给用户。

3. 按以下口径解读，再回复用户（HTML 报告直接给文件路径，终端贴一份精简结论，并**主动询问用户是否需要为本地 Pi（360 provider）增删模型**）：
   - **首字延迟(TTFT)** = 首个可见文字 delta 时间。推理模型会先吐 `thinking_delta`，所以 TTFT 可能远大于"首个思考"时间——两个都报告。
   - **端到端 TPS** = usage 上报的输出 token 数 ÷ 总耗时；usage 缺失时按 CJK=1 token、其余 4 字符=1 token 估算。
   - TTFT 为 `(无正文)` 表示在 max_tokens 预算内只输出了思考、没有正文（纯推理模型），或模型非对话（embedding 返回 0 token）。
   - 每次测速完成回复的最后，提示用户："如需为本地 Pi（360 provider）新增或删除模型，可直接告诉我模型名。"

4. **增/删模型后续处理**：
   - 测速完成后用户若要求"帮我增/删模型"或"加到配置里"，默认修改本机 Pi 的全局配置 `~/.pi/agent/models.json` 中 `providers["360"].models` 列表。
   - 新增模型时参考元信息（`/model/info`）补全 `id`、`name`、`reasoning`、`input`（是否含 `image` 视觉能力）、`contextWindow` 与 `maxTokens`。

## 陷阱

- **超时≠挂了**：慢推理模型（如 kimi-k3、glm-5.3）首字要 30~60s，冷启动往返就要 8~28s；用默认 60s 超时会误报 ReadTimeout。慢模型要 `--timeout 120` 或更大。
- **别只看 `/model/info` 数量**：它返回的是部署记录数（360 上是 79 条），`/v1/models` 才是可路由模型数（55 个）。以 `/v1/models` 为准。
- **同模型多个后端速度差异巨大**：deepseek-v4-flash 在 `m1/`(109 tok/s)、`360/`(63)、`-openai`(58)、`m2/`(24) 之间差 4 倍。选模型时带对前缀，别用错部署。
- **403/404/503 与"模型不存在"要区分**：403 是当前 key 无权限（换 key 或申请），404/503 是网关没配后端（找网关管理员），超时是慢或非对话模型。
- API key 从仓库根目录 `.env` 的 `LLM_API_KEY` 读取；base-url 和代理仍是 360 默认值，测别的网关必须显式 `--base-url` / `--proxy`，避免把 key 发错域名。

## 验证

- 脚本正常结束时打印 `JSON 结果: <路径>` 与 `HTML 报告: <路径>`；JSON 中 `ok=true` 条目数 + 失败条目数 = `/v1/models` 模型总数。
- 生成的 HTML 是自包含单文件（含内联 CSS/JS），用浏览器打开无资源缺失；可用表点击表头能排序。
- 抽查一个最快模型的 TTFT 是否 < 2s（360 上 `m1/deepseek-v4-flash` 约 0.4s）。
