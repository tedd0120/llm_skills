# 开发产物规范

本文规定开发过程中产生的文件放在哪里、保留多久、如何收尾。skill 运行产出（`data/`）与本机状态（`.local/`）的目录解析约定见 [AGENTS.md](../../AGENTS.md)。

## 四层归属

每个文件先按“属于谁、活多久”归入一层，再在层内定位。

| 层 | 位置 | Git | 内容 | 生命周期 |
|---|---|---|---|---|
| 正式资产 | `.agents/skills/`、`docs/`、`AGENTS.md`、`CLAUDE.md`、`README.md`、`.env.example` | 跟踪 | 源码、测试、正式截图基线、规范、ADR | 随代码评审演进 |
| 任务工作区 | `.work/<任务ID>/` | 忽略 | 一次开发任务的计划、原型、临时材料、子代理材料与验收证据 | 随任务开始与收尾 |
| 本机持久状态 | `.local/<用途>/` | 忽略 | 跨任务复用的账号、服务、发布包、issue、工具配置 | 随所属对象管理，显式重置 |
| 程序自管状态 | 见下表 | 忽略 | 由代码或第三方工具决定路径的运行态、缓存、客户端状态 | 归属程序管理 |

程序自管状态的路径由代码决定，开发时只读取和清理，不在其中存放任务材料：

| 位置 | 归属 |
|---|---|
| `data/<skill>/` | skill 运行产出（报告、导出、抓取结果），由各 skill 脚本写入 |
| `.agent-council/`、`.impeccable/`、`PRODUCT.md` | 第三方 skill 固定写入仓库根的输出 |
| `__pycache__/`、`.pytest_cache/` | Python 字节码与测试缓存 |
| `.claude/`、`.zcode/`、`.pi/`、`.antigravitycli/` | AI 客户端本机状态 |

判定口诀：**要提交的进正式资产；为某个任务产生的进 `.work/<任务ID>/`；任务结束后还要复用的进 `.local/`；程序自己写的不去动。**

## 任务工作区 `.work/<任务ID>/`

任务 ID 固定为 `{年月日}_{时分秒}_{任务主题}`，例如 `20260921_110524_artifact-layout`：

- `{年月日}_{时分秒}`：创建时执行 `date +%Y%m%d_%H%M%S` 取得的本机当前时间，禁止估写或取整。
- `{任务主题}`：2–5 个小写英文单词，以连字符 `-` 连接，只含 `a-z`、`0-9`、`-`，概括任务对象与动作（如 `login-retry-fix`、`admin-center-proto`）。
- 完整 ID 须匹配 `^[0-9]{8}_[0-9]{6}_[a-z0-9]+(-[a-z0-9]+){1,4}$`；清理工具按此校验。
- 创建前检查重名，冲突时重新取时间；ID 创建后不再改名。

同一任务的全部过程材料都以这个 ID 聚合，按子目录区分用途：

```text
.work/<任务ID>/
├── plan.md        计划、执行阶段与进度（大任务必需）
├── prototype/     原型单入口 index.html，多方案在同一入口切换
├── scratch/       临时脚本、日志、下载、截图草稿、测试服务数据
├── runner/        subagent-task-runner 的账本、brief、report、review package
└── evidence/      收尾后保留的验收记录、结论、子代理账本与关键报告
```

子目录按需创建，只建用得到的。各子目录的保留规则：

| 子目录 | 任务进行中 | 任务收尾后 |
|---|---|---|
| `plan.md` | 随实施更新总体与分项状态 | 保留，顶部 `Status:` 标为完成或放弃 |
| `prototype/` | 入口顶部写明待回答的问题，交付评审后内容冻结；新方案另建任务 | 原样保留；结论写入 `plan.md` 或 `evidence/conclusion.md` |
| `scratch/` | 自由读写 | 删除 |
| `runner/` | 由 skill 管理 | 账本与关键报告移入 `evidence/runner/` 后删除 |
| `evidence/` | 只写需长期留存的证据 | 保留；大任务至少含 `acceptance.md`，未解决失败保留复现材料 |

需要长期生效的结论不停留在工作区：skill 行为写入对应 `SKILL.md` 或其 `references/`，仓库约定写入 `AGENTS.md` 或 `docs/agents/`，可复用脚本迁入对应 skill 的 `scripts/`。

## 按任务规模选择

### 微改动：不建目录

单文件修复、文案调整、配置小改，用现有测试即可验证。无需计划与工作区；一次性临时文件使用系统 `tempfile`/`mktemp` 并在退出时清理。

### 小任务：只建用到的子目录

- 需要落盘的临时材料（日志、截图、下载、测试服务数据）：`.work/<任务ID>/scratch/`。
- 小原型：`.work/<任务ID>/prototype/index.html`，入口顶部写待回答的问题；结论写入 `evidence/conclusion.md`，原型内容不再修改。
- 需要留存的验收证据：`.work/<任务ID>/evidence/`。
- 满足下一节任一条件时升级为大任务并补写 `plan.md`。

### 大任务：`plan.md` 必需

满足任一条件即为大任务：预计跨多个会话；包含多个相互依赖的阶段或跨模块改动；使用 subagent-task-runner；涉及迁移、发布或不可逆操作。

`plan.md` 首行为标题，随后写 `Status:`（`进行中`、`完成`、`放弃`），再划分执行阶段，阶段与子任务均以 `[ ] 未开始`、`[~] 进行中`、`[x] 完成` 标记状态并实时更新。

### 使用 subagent-task-runner

- 计划写在 `.work/<任务ID>/plan.md`，以此文件作为 `PLAN_FILE`。
- runner 工作目录为 `.work/<任务ID>/runner/`：skill 的 `scripts/workspace` 在计划文件名为 `plan.md` 时解析到计划同级的 `runner/`。
- 收尾时将以下文件保持原文件名移入 `evidence/runner/`，再删除 `runner/`：`progress.md`（账本，含全部 `Ruling:` 裁决）；最终审查及其复审涉及的 `review-*.diff` 与报告；账本中仍未解决条目引用的 report、diff 与复现材料。Pi prompt、events、session 等调用过程文件按需保留。
- 并行执行的计划各自使用独立任务 ID，互不共享 `runner/`。

## 本机持久状态 `.local/`

| 位置 | 内容 | 管理 |
|---|---|---|
| `.local/<skill>/` | skill 登录态、token 缓存、验证码截图（如 `xiaohongshu/`、`pan123-renamer/`） | 随账号有效期管理，显式重置 |
| `input/` | 交给 skill 处理的用户输入文件 | 由用户管理 |

issue 描述“要做什么”，可跨多个任务；任务工作区记录“这一次怎么做”。实现某个 ticket 的任务在 `plan.md` 中链接对应 issue 文件。

## 第三方 skill 输出

skill 可以指定输出位置时，写入当前任务的 `.work/<任务ID>/` 相应子目录。固定写入仓库根隐藏目录的 skill 在 `.gitignore` 中防御性忽略，其材料在任务收尾时移入工作区或清理。约定写入系统临时目录的 skill 保持原行为。

## 开始与收尾

1. 开始：按规模决定是否建工作区；建立时一次确定任务 ID，所有材料写入该 ID 目录。
2. 服务：临时服务按需启动；持久服务的进程记录（宿主、PID、端口、命令、日志位置）写入 `.local/services/<环境>/`。仅凭端口或历史 PID 不足以停止进程。
3. 收尾：停止本任务启动的临时服务；证据移入 `evidence/`，runner 材料按上文归档；长期结论写入正式资产；更新 `plan.md` 的 `Status:`。
4. 验收记录：大任务在 `evidence/acceptance.md` 记录验收命令、执行时间、结果摘要与对应代码版本（commit 或 `git diff --stat`）；迁移类操作在执行前记录源文件摘要，执行后记录校验结果。记录随步骤实时写入，事后无法重现的数据如实标注缺失。
5. 清理：预览 `scratch/`、`runner/` 的清理清单，确认任务已结束后执行，再核对目标消失。原型、证据、持久数据库、发布包及业务数据单独处理。

## 查看与清理

```bash
python .agents/skills/workspace-layout/scripts/artifacts.py list
python .agents/skills/workspace-layout/scripts/artifacts.py clean .work/<任务ID>/scratch
python .agents/skills/workspace-layout/scripts/artifacts.py clean .work/<任务ID>/scratch --apply
```

`list` 显示 `.work/` 各任务（附 `task_id_ok`）、`.local/` 各目录及误建的旧布局目录（附 `legacy: true`）。`clean` 默认只预览，只接受 ID 合规的 `.work/<任务ID>` 及其 `scratch`、`runner`，执行前检查符号链接与 Git 跟踪文件；进程占用检查依赖 `/proc`，在 WSL/Linux 执行时生效。

## 旧布局目录

`.prototype/`、`.task-runner/` 为旧布局，已迁移完毕，不再新建。工具或 skill 误建这些目录时，按下表迁入 `.work/`，原目录名不合规时按创建时间与主题重新命名：

| 旧位置 | 新位置 |
|---|---|
| `.prototype/<时间_主题>/` | `.work/<任务ID>/prototype/` |
| `.task-runner/<计划名>/` | `.work/<任务ID>/runner/` |

迁移先核对引用与进程占用（正被服务使用的目录等服务停止后再迁），再移动并校验内容；同一文件系统使用重命名，避免中途复制出不完整目录。有效说明和执行入口同步更新。已冻结的验收记录保持原始字节。
