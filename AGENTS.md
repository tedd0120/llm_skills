# Agent 指引

## 措辞与断言

写注释、docstring、命名、断言、错误信息和 Markdown 文档时，每句话只承载一条新信息。落笔前检查两类冗余否定：

- **镜像尾巴（Mirrored Tail）**：前半句已经界定范围时，删除后半句对范围外情况的镜像否定或许可。若删掉后半句语义不变，就以较短表述为准。
- **悬空否定（Dangling Negation）**：先判断被否定的选项在当前步骤是否仍然可达；已被上游排除的选项不再列入本步骤的说明。

断言和测试命名遵循同一规则。`keeps_X_excludes_not_X` 之类的对仗名称只保留承载真实区分的部分；多个真实互斥约束分别表达。需要强调完备性时，列出当前步骤仍可接收的输入形态，以此界定边界。

## Skill 编辑默认路径

当任务是编辑 skill 时，默认编辑**当前项目目录**下的 `.agents/skills/`。
只有用户主动要求时，才可修改全局 skill。

## 工作区与开发产物

- 开发任务的过程材料按任务聚合在 `.work/<任务ID>/`，任务 ID 固定为 `{年月日}_{时分秒}_{任务主题}`（如 `20260921_110524_artifact-layout`），时间取自 `date +%Y%m%d_%H%M%S`，主题为 2–5 个小写英文单词连字符连接：计划 `plan.md`、原型 `prototype/`、临时材料 `scratch/`、子代理材料 `runner/`、验收证据 `evidence/`，按需创建；跨任务复用的本机状态放 `.local/<用途>/`。微改动不建工作区。创建、迁移或清理产物前读取 [开发产物规范](docs/agents/artifacts.md)，按其规模判定与收尾流程执行。
- 续写、修订或承接计划前读取对应 `plan.md`，并随实施标记总体与分项进度。
- Prototype 使用独立单入口，多方案在同一入口展示；交付评审后内容冻结，结论写入 `plan.md` 或 `evidence/conclusion.md`，新方案另建任务。

## Skill 运行产出与本机状态

- 使用 skill 得到的报告、抓取结果、导出文件写入 `data/<skill>/`；需要按次区分时再分 `{年月日}_{时分秒}_{主题}/` 子目录，主题可用中文。
- skill 的登录态、token 缓存、验证码截图等本机状态写入 `.local/<skill>/`，不放在 skill 源码目录；多个 skill 共用的状态使用共同名称（如 `xiaohongshu`）。
- 脚本按以下顺序解析目录，与运行时的 cwd 无关：
  1. 调用方显式传入的输出参数；
  2. 环境变量 `LLM_SKILLS_DATA_DIR/<skill>`（产出）或 `LLM_SKILLS_STATE_DIR/<skill>`（状态）；
  3. 从脚本位置向上找到的 Git 仓库根下的 `data/<skill>` 或 `.local/<skill>`，查找到家目录为止；
  4. `~/.llm-skills/data/<skill>` 或 `~/.llm-skills/local/<skill>`。
- 每个 skill 独立安装，解析逻辑写在 skill 自己的脚本里，不跨 skill 引用。
