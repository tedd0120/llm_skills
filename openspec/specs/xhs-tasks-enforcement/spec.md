# 小红书任务清单执行规范

## 目的

定义 xiaohongshu-scraper 执行阶段的任务清单机制，确保 Agent 按步骤完成所有任务。

---

## 新增需求

### 需求:执行阶段必须创建 tasks.md

Agent 进入阶段二后，必须立即在 OUTPUT_DIR 下创建 `tasks.md` 文件，内容为预设的任务清单。

#### 场景:创建 tasks.md

- **当** 澄清阶段完成且 OUTPUT_DIR 已创建
- **那么** Agent 必须在 OUTPUT_DIR 下写入 tasks.md
- **并且** tasks.md 内容必须包含 5 个未勾选任务项

#### 场景:tasks.md 内容格式

- **当** tasks.md 被创建
- **那么** 内容必须为：
```markdown
## 执行任务清单

- [ ] 检查登录状态
- [ ] 抓取数据
- [ ] 生成报告
- [ ] 格式化报告
- [ ] 发送报告
```

### 需求:每完成一项任务必须打勾

Agent 每完成 tasks.md 中的一项任务后，必须立即更新该文件，将对应的 `[ ]` 改为 `[x]`。

#### 场景:任务完成打勾

- **当** Agent 完成某项任务（如检查登录状态返回 LOGIN_OK）
- **那么** Agent 必须编辑 tasks.md
- **并且** 将对应行的 `- [ ]` 改为 `- [x]`

#### 场景:跳过打勾违反核心要求

- **当** Agent 完成任务但未更新 tasks.md
- **那么** 视为违反核心要求
- **并且** 阶段结束时验证将失败

### 需求:阶段结束前必须验证任务完成

Agent 在阶段二结束前，必须执行 `verify_tasks.py` 脚本验证所有任务已完成。

#### 场景:验证全部完成

- **当** Agent 执行 `python scripts/verify_tasks.py <tasks_file_path>`
- **并且** tasks.md 中所有任务均为 `[x]`
- **那么** 脚本输出 `TASKS_COMPLETE: 5/5`
- **并且** 脚本返回退出码 0

#### 场景:验证存在未完成项

- **当** Agent 执行 `python scripts/verify_tasks.py <tasks_file_path>`
- **并且** tasks.md 中存在 `[ ]` 未完成项
- **那么** 脚本输出 `TASKS_INCOMPLETE: N/5`
- **并且** 脚本输出未完成项列表
- **并且** 脚本返回退出码 1

#### 场景:验证失败必须中止

- **当** verify_tasks.py 返回非零退出码
- **那么** Agent 必须报错并中止任务
- **禁止** 在任务未完成时发送报告给用户
