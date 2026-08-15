---
name: yushu-sql
description: 通过 OpenCLI 复用 Chrome 登录态，在公司毓数自助查询平台执行、监控、读取或下载 SQL 结果。用户提到毓数、自助查询、毓数 SQL、公司平台跑 SQL、查表取数、导出查询结果或排查查询失败时使用。
---

# 毓数 SQL 查询

在 `https://insight.360shuke.com/bolt/dataQuery` 中完成查询闭环。使用 OpenCLI 驱动已登录的 Chrome；保留用户 SQL 的语义，并明确区分只读查询与数据变更。

## 执行边界

- 用户提供 SQL 时原样使用；只处理外层空白，不擅自改写字段、过滤条件、引擎或集群。
- 用户只描述取数目标时，仅在库、表、字段和口径足够明确时生成 SQL。探索性查询默认加 `LIMIT 100`；口径不明确时先询问。
- 把一个尾随分号视为单条语句。检测到多条语句时拆开说明，逐条执行。
- 把 `SELECT`、`SHOW`、`DESC`、`DESCRIBE`、`EXPLAIN` 和最终产出只读结果的 `WITH` 作为只读候选；检查完整语句，因为 `WITH` 可能包裹写操作。
- 对 `INSERT`、`UPDATE`、`DELETE`、`MERGE`、`CREATE`、`ALTER`、`DROP`、`TRUNCATE`、存储过程调用及其他变更操作，展示完整 SQL、影响对象和不可逆风险，取得用户对该 SQL 的明确确认后再运行。
- 用户只要求编写、解释或评审 SQL 时，不打开页面、不执行查询。
- 只复用浏览器登录态。不得读取、输出或落盘 Cookie、Session、Token 等凭据。
- 默认仅在回复中展示至多 50 行结果；仅在用户要求时下载或持久化结果。对可能含个人或敏感字段的结果只展示完成任务所需的最小范围。

## 运行查询

1. 运行 `opencli doctor`。浏览器桥接未全绿时，根据诊断修复；不得绕过登录或改用抓取凭据的方式。

2. 为当前任务创建唯一会话名，例如 `yushu-sql-<时间戳或短随机串>`。默认把会话标记为 `owned`，并在首次连接时使用后台窗口：

   ```bash
   opencli browser <session> --window background open "https://insight.360shuke.com/bolt/dataQuery"
   opencli browser <session> --window background state
   ```

   从 `open` 的 JSON 响应保存 `page` 为 `owned_page`；响应没有 `page` 时，运行 `tab list`，只在目标 URL 唯一匹配时保存其 `page`。确认 URL 和标题属于“毓数 自助查询”。`background` 是后台真实 Chrome 窗口，不是真正 headless；本任务的每条 `opencli browser <session>` 命令都继续携带 `--window background`，防止后续命令把窗口切到前台。

   若用户要求继续当前 Chrome 标签中的查询，或后台页面跳到登录、SSO、无权限页，则使用绑定分支：先关闭刚创建的 `owned_page` 并释放其 lease，让用户在 Chrome 完成登录并把目标标签置为当前标签，再用新的唯一会话执行 `bind`，把会话标记为 `bound`。绑定用户标签时不设置 `owned_page`。

3. 每次都从实时页面定位编辑器，不复用旧 ref：

   ```bash
   opencli browser <session> --window background find --css ".cm-content[contenteditable='true'][role='textbox']" --limit 5 --text-max 300
   ```

   要求唯一可见匹配。使用当前 shell 的字面量引用把完整 SQL 作为一个参数传给 `fill <ref> <sql>`，并检查响应中的 `verified: true`。SQL 含引号、换行或 `$` 时，先用该 shell 的 literal heredoc/here-string 存入任务专用变量，再传入；不得让 shell 展开 SQL 内容。

4. `fill` 会使 CodeMirror 的旧 ref 失效。重新定位并聚焦编辑器，再用页面原生快捷键提交：

   ```bash
   opencli browser <session> --window background focus ".cm-content[contenteditable='true'][role='textbox']"
   opencli browser <session> --window background keys "Shift+Enter"
   opencli browser <session> --window background wait xhr "/bolt_api/dataQuery/getResult" --timeout 60000
   ```

   每条 SQL 只提交一次。超时表示“状态未知”，不是失败；先检查结果请求和页面状态，禁止直接重跑。

5. 从本次提交后的网络记录中选择时间戳最新的 `getResult` 项：

   ```bash
   opencli browser <session> --window background network --since 10m --filter "status,compressedData"
   opencli browser <session> --window background network --detail "<latest-getResult-key>"
   ```

   仅在响应满足 `body.flag == "S"`、`body.data.status == 2` 且 `body.data.success == true` 时判定成功。`success == false` 时报告任务编号、SQL、错误字段和日志入口。其余状态继续等待新的 `getResult` XHR 并读取最新项；等待期间向用户提供简短进度，禁止再次提交 SQL。

6. 对有结果集的成功查询，把同一个 detail JSON 通过 stdin 交给解码器。将 `<skill-dir>` 解析为本 `SKILL.md` 所在目录：

   ```bash
   opencli browser <session> --window background network --detail "<latest-getResult-key>" | node "<skill-dir>/scripts/decode-result.mjs"
   ```

   解码器输出列名、行矩阵、总行数、耗时、引擎、集群、任务编号和下载能力。零行结果应明确报告为零行，不视为失败。

7. 准备回复内容：执行的 SQL、成功或失败状态、任务编号、引擎/集群、耗时、总行数，以及至多 50 行 Markdown 表格。若平台显示或 API 返回的实际 SQL 与输入不同，同时给出两者并说明平台改写。完成所需下载后再进入清理。

8. 在发送最终回复前执行清理；成功、失败、超时和取消路径使用同一规则：

   - `owned`：先物理关闭本任务保存的 `owned_page`，再释放 lease。两个命令都要尝试；第一个失败时仍执行第二个。

     ```bash
     opencli browser <session> --window background tab close "<owned_page>"
     opencli browser <session> --window background close
     ```

   - `bound`：只解除绑定，保留用户自己的标签和窗口。

     ```bash
     opencli browser <session> unbind
     ```

   检查清理命令的输出。只有清理已成功，或清理失败已在回复中明确报告时，任务才算完成。用户明确要求保留页面供连续查询时才延后清理，并在最后一次查询后执行。

## 分支与恢复

- 用户指定查询引擎/集群、要求下载，或页面/API 结构与主流程不一致时，读取 [references/platform.md](references/platform.md)。
- 遇到 `stale_ref`、`not_found` 或 `reidentified` 时重新运行 `state`/`find`；写操作命中 `reidentified` 时先验证目标再继续。
- `fill` 成功但没有查询请求时，重新定位并聚焦编辑器，再按一次 `Shift+Enter`；确认此前没有任务编号或 `getResult` 请求后才能这样做。
- 页面结果区使用虚拟表格，DOM 中可能没有单元格文本。优先解码 `getResult`，不要 OCR 或抓 Canvas。
- 网络缓存丢失但当前结果仍显示时，按 `references/platform.md` 的“当前页面结果恢复”只读提取 VTable 当前页；明确标注这是当前页恢复，任务编号、完整总量等未恢复字段不得猜测。
- 用户要求下载时先确认 detail 中 `canDownload == true`。如果平台弹出审计、脱敏或审批提示，报告提示并停止，等待用户处理。
- 没有已保存的 `owned_page` 时先用 `tab list` 恢复目标；匹配不唯一时释放 lease 并报告无法安全关闭，禁止猜测并关闭其他 Chrome 标签。
