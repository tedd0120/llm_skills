# 毓数平台映射

以下内容来自 2026-08-14 的只读页面探查和 `SELECT 1 AS codex_smoke_test` 冒烟查询。实时 `state`、`find` 和网络响应优先于本文。

## 页面与控件

- 地址：`https://insight.360shuke.com/bolt/dataQuery`
- 标题：`毓数 自助查询`
- SQL 编辑器：CodeMirror，当前定位为 `.cm-content[contenteditable='true'][role='textbox']`
- 并行执行入口：`.run.head-icon`；页面提示的原生快捷键是 `Shift + Enter`
- 查询结果容器：`.results`
- 当前结果的下载按钮：`.results .download-btn`
- 结果网格使用虚拟表格/Canvas；页面文字树可能只有列外信息，没有单元格值。

主流程优先使用“聚焦编辑器 + `Shift+Enter`”。图标点击依赖编辑器中的当前语句/选区，未聚焦时可能没有提交请求。

## 查询引擎指令

不写指令时使用智能路由，平台会尝试 Doris 或 Presto 加速。

把指令作为 SQL 顶部的单行注释：

```sql
--presto
select * from db.table;
```

同时指定引擎和大数据集群：

```sql
--presto safe_lycc
select * from db.table;
```

平台列出的引擎：`presto`、`spark`、`spk`、`pst`、`hive`、`doris`、`mysql`、`mongodb`。

平台列出的集群：

- `safe_lycc`、`safelycc`、`sfly`：一般业务集群
- `bjmd`：高可用集群
- `report_doris`：Doris 报表集群

逻辑表只写表名并添加：

```sql
--logical
select * from table_name;
```

MongoDB 使用 mongosh 语法：

```javascript
--mongodb dbName
db.tableName.find().limit(10);
```

仅在用户明确指定或业务上下文要求时添加引擎/集群指令；不要用已观察到的列表替用户猜选路由。

## 结果 API

执行后页面轮询：

```text
GET /bolt_api/dataQuery/getResult?jobId=<job-id>&page=1&pageSize=50
```

已验证的成功条件：

- 顶层 `flag` 为 `S`
- `data.status` 为 `2`
- `data.success` 为 `true`

关键字段：

- `columnNameList`：列名
- `compressedData`：Base64 编码的 Zstandard 数据，解压后为 JSON 行矩阵
- `totalCount` / `resultTotalCount`：结果总行数
- `displayCostTime` / `costTimeMill`：耗时
- `jobId`：任务编号
- `dataSourceType`：执行引擎
- `dataCenterType`：执行集群
- `canDownload`：是否可下载
- `other`：JSON 字符串，包含 `rawSql` 等信息

成功响应中的 `errorMsg` 可能只是执行节点信息，因此不得仅凭它非空判定失败。

页面还会请求：

```text
GET /bolt_api/sql/info?jobId=<job-id>
```

它包含 `rawSql`、路由后的 `sql`、`dataSource` 和 `dataCenter`。冒烟查询中平台把输入的 `select 1 as codex_smoke_test` 显示为带 `LIMIT 1000` 的实际 SQL；每次以本次响应为准，不假设所有查询都会这样改写。

## 下载结果

仅在用户明确要求下载时执行：

1. 确认最新 detail 的 `canDownload == true`。
2. 重新 `state`/`find`，确认 `.results .download-btn` 是唯一可见的当前结果按钮。
3. 点击后运行 `opencli browser <session> --window background wait download --timeout 60000`。
4. 返回 OpenCLI 报告的文件名/下载元数据；不要自动移动、重命名或上传文件。

平台页面提示：只可下载最近 7 天查询的文件，每个文件最多支持 2 万行。审计、脱敏或审批提示优先于下载流程。

## 当前页面结果恢复

页面未刷新但 OpenCLI 网络缓存已经丢失时，可以只读访问 VTable 已加载的当前页。不得用它宣称恢复了未加载分页或任务元数据。

```bash
opencli browser <session> --window background eval "(() => { const table = document.querySelector('.results .vtable')?.__vtable__; const columns = (table?.options?.columns ?? []).filter(c => c.field !== 'seq'); const records = table?.options?.records ?? []; return { columns: columns.map(c => c.title), rows: records.map(record => columns.map(c => record[c.field])), loadedRows: records.length, summary: document.querySelector('.results .page-text')?.innerText ?? null, header: document.querySelector('.results .text-space')?.innerText ?? null, status: document.querySelector('.results .result-text')?.innerText ?? null }; })()"
```

只有 `columns` 和 `rows` 来自当前已加载表格。`summary`、`header` 和 `status` 是页面显示文本；任务编号、精确路由元数据、未加载页和下载能力仍需 `getResult` 响应。

## 漂移恢复

- 编辑器选择器失效：先用 `find --role textbox` 和 `state` 找唯一可见的 CodeMirror/contenteditable 控件。
- 快捷键失效：悬停当前运行入口确认页面提示，再使用唯一可见的运行控件。
- `getResult` 路径失效：运行 `network --since 10m`，按任务编号、`status`、列名和行数据形状定位本次结果请求。
- 页面状态与本文冲突：信任实时页面，完成当前任务后再更新本文。
