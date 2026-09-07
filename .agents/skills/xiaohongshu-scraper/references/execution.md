# 执行阶段流水线编排

本文件供完成澄清阶段后，进入阶段二（执行阶段）时查阅。

## 执行任务清单

进入阶段二后，立即将以下任务写入 `{OUTPUT_DIR}/tasks.md`：

```markdown
## 执行任务清单

- [ ] 确保登录
- [ ] 抓取数据
- [ ] 生成报告
- [ ] 格式化报告
- [ ] 发送报告
```

**铁律**：每完成一步，立即将对应 `[ ]` 改为 `[x]`；结束前必须通过产物校验，禁止发送未通过验证的报告。

---

## 执行步骤

### 步骤 1：确保登录

1. 调用编排脚本：
   ```bash
   python .agents/skills/xiaohongshu-scraper/scripts/orchestrate_login.py --output-dir <OUTPUT_DIR 绝对路径>
   ```
2. 出现 `NEED_LOGIN:<abs_path>` 或对应扫码事件：立即发送消息给用户：
   `"请扫码登录小红书。二维码文件：<abs_path>"`
3. 出现 `LOGIN_OK` / `LOGIN_SUCCESS`：脚本会自动将 `tasks.md` 中“确保登录”标记完成，继续下一步。
4. 出现超时或环境报错：中止流程，按需查阅 [troubleshooting.md](troubleshooting.md)。

### 步骤 2：抓取数据

- **模式 A（固定关键词）**：单次调用 `xiaohongshu-fetch` 生成 `{OUTPUT_DIR}/raw.json`。
- **模式 B（发散模式）**：按照 [mode-divergence.md](mode-divergence.md) 多轮抓取，完成后按 [multi-round-merge.md](multi-round-merge.md) 合并为 `raw.json`。
- **模式 C（总分模式）**：按照 [mode-overview-detail.md](mode-overview-detail.md) 多轮抓取，完成后按 [multi-round-merge.md](multi-round-merge.md) 合并为 `raw.json`。
- 启用超链接时，fetch 会同步产出 `id_url_map.json`。

### 步骤 3：生成报告

调用 `xiaohongshu-summarize`，传入 `raw.json` 与 `REPORT_TYPE`，生成草稿文件 `{OUTPUT_DIR}/{主题}.md`。

### 步骤 4：格式化报告

调用 `xiaohongshu-formatter`，对 `{OUTPUT_DIR}/{主题}.md` 进行 emoji 美化与超链接占位符替换。

### 步骤 5：产物校验与发送

在向用户发送报告前，必须运行自动化校验脚本：

```bash
python .agents/skills/xiaohongshu-scraper/scripts/verify_tasks.py <OUTPUT_DIR>/tasks.md --report-file <REPORT_FILE> --report-type <REPORT_TYPE>
```
（若启用了超链接，追加 `--hyperlinks`）

- 仅当验证通过（`RUN_VALID`）时，才将最终报告正文输出给用户；
- 出现 `RUN_INVALID` 必须中止发送并排查修复。
