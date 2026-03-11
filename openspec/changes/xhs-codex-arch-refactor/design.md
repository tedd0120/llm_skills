## 上下文

当前仓库中的小红书能力已经形成“一个入口 skill + 多个子 skill/脚本”的雏形，但真实边界并不稳定：
- `xiaohongshu-scraper` 在文档中承担编排层角色，但大量流程正确性仍依赖 `SKILL.md` 文本约束。
- 报告链被拆成 `xiaohongshu-summarize` 与 `xiaohongshu-formatter`，两者围绕同一个 `_index.md` 产物建立了强耦合协议（尤其是 `id:{post_id}` 占位符与链接替换）。
- 登录在规范与 README 中被表述为独立 skill，但仓库当前并没有对应的实际 skill 目录，造成架构漂移。
- `xhs_selectors.py` 等基础能力在多个位置重复存在，未来页面改版会导致多点维护。

用户已经明确要求按方案 A 创建一套不覆盖原实现的新技能，并统一加 `-codex` 后缀。因此这次设计必须同时满足两件事：保留旧版可参考性；建立一套新的、边界更清晰的目标架构。

## 目标 / 非目标

**目标：**
- 建立以 `xiaohongshu-scraper-codex` 为唯一用户入口的新技能套件。
- 将实际编排逻辑下沉到内部 orchestrator 层，减少对 Markdown 说明驱动流程正确性的依赖。
- 保留抓取边界为独立能力，不将采集与报告生成揉成单个模块。
- 合并 `summarize` 与 `formatter` 为统一的报告流水线能力。
- 抽出共享基础层，统一 selectors、browser/session、auth state 与数据 schema。
- 清理与新架构不一致、与实际文件不一致、或明显重复的脚本和文档描述。
- 保持旧 skills 不被覆盖，作为迁移期兼容参考。

**非目标：**
- 不要求在本次变更中删除旧版小红书 skills。
- 不要求维持“新体系中登录必须作为独立 skill 暴露”的旧约束。
- 不尝试将抓取、报告、编排全部重新合并为单体 skill。
- 不引入新的外部服务或复杂的进程间通信机制。

## 决策

### 决策 1：保留单一用户入口，新增内部 orchestrator 层

**选择：** 新体系只对外暴露 `xiaohongshu-scraper-codex`；编排逻辑通过内部 orchestrator 模块承载，而不是新增一个对用户可见的 orchestrator skill。

**理由：**
- 用户真正需要的是“一站式入口”，不是理解内部层次。
- 登录、目录初始化、固定/发散模式调度、任务状态与最终校验都属于流程编排职责，适合聚合在代码层而非继续散落在 `SKILL.md` 中。
- 内部 orchestrator 可以作为未来测试、迁移、恢复执行和状态收敛的稳定落点。

**替代方案：**
- 新增对外的 `xiaohongshu-orchestrator-codex` skill → 否决：增加用户心智负担，且与 scraper 入口职责重叠。
- 继续把编排逻辑主要写在 SKILL.md 中 → 否决：流程真相依旧漂浮在文档层，难以维持一致性。

### 决策 2：保留 fetch 独立，合并 summarize 与 formatter

**选择：** `xiaohongshu-fetch-codex` 作为独立抓取引擎保留；`xiaohongshu-summarize` 与 `xiaohongshu-formatter` 的职责在新体系中合并为 `xiaohongshu-report-codex`。

**理由：**
- 抓取层与报告层属于不同能力域：前者负责浏览器自动化与数据采集，后者负责内容理解、可追溯报告生成与最终渲染。
- `summarize` 与 `formatter` 围绕 `_index.md` 及超链接占位符协议紧耦合，拆开维护收益低，合并后可以移除跨组件的半成品协议。
- 保留 fetch 独立，有利于未来单独维护反爬适配、去重逻辑和浏览器行为。

**替代方案：**
- 将 fetch 与 report 进一步合并为单一执行模块 → 否决：采集与分析边界会混乱，测试与维护成本更高。
- 保持 summarize/formatter 分离 → 否决：仍然保留当前最脆弱的内部协议边界。

### 决策 3：登录收回为 orchestrator 内部 auth 能力

**选择：** 新 codex 架构中不再把登录定义为独立 skill 边界；登录能力作为 orchestrator 内部依赖的 auth 模块/脚本存在。

**理由：**
- 登录本质上是会话与环境准备，不是用户要单独编排的业务能力。
- 现有仓库已出现“文档写有 login skill、实际目录不存在”的漂移，继续强调独立 skill 只会扩大不一致。
- 对用户来说，“确保已登录”是 scraper 流程的一部分，而不是独立产品面。

**替代方案：**
- 在 codex 版重建 `xiaohongshu-login-codex` → 否决：除非明确需要独立运维入口，否则会继续强化假边界。

### 决策 4：抽取 shared core，消除重复基础设施

**选择：** 增加 `xiaohongshu-core-codex` 作为共享基础层，统一承载选择器、浏览器启动参数、会话状态路径、数据契约等公共能力。

**理由：**
- 目前存在重复的 `xhs_selectors.py` 与重复的环境前提说明。
- 页面改版、平台适配、浏览器配置属于共享问题，应当在单一位置维护。
- 数据 schema 抽出后，有助于 fetch、report、orchestrator 三层共享输入输出约束。

**替代方案：**
- 在每个 skill 下继续复制脚本 → 否决：会造成多点漂移与重复修复。

### 决策 5：保留旧版，新增 codex 后缀目录而非原地替换

**选择：** 所有新技能使用 `-codex` 后缀，旧版技能目录保留。

**理由：**
- 用户已明确要求不要覆盖原技能。
- 新旧并存可以降低迁移风险，并保留对旧实现的回溯能力。
- 文档清理可以逐步切换推荐入口，而不强迫一次性重构全部调用面。

**替代方案：**
- 直接在原技能目录上重构 → 否决：风险较高，也违背用户要求。

## 风险 / 权衡

- [新旧 skill 并存导致仓库条目增多] → 在 README 和新旧 SKILL.md 中清晰标明“旧版保留 / codex 推荐入口”。
- [部分旧文档与旧 spec 仍会引用 login skill] → 通过文档清理能力统一移除或改写新体系中的相关引用，并限制清理范围只覆盖 codex 相关描述。
- [合并报告链可能暂时牺牲单独格式化入口] → 保留旧版 formatter 供兼容参考，新体系中以 report 统一承担职责。
- [共享 core 可能造成初期目录调整较多] → 在迁移计划中先建立 core，再迁移调用，避免一步到位式替换。
- [任务状态仍然可能依赖 `tasks.md`] → 新体系保留 `tasks.md` 作为用户可见进度，同时允许 orchestrator 拥有更明确的内部状态组织。

## Migration Plan

1. 在 `.claude/skills/` 下创建 codex 后缀的新目录结构，不修改旧目录。
2. 先建立 `xiaohongshu-core-codex`，承载共享脚本与 schema。
3. 建立 `xiaohongshu-fetch-codex`，让其引用 core 层的共享能力。
4. 建立 `xiaohongshu-report-codex`，吸收 summarize 与 formatter 的职责，统一报告产出契约。
5. 建立 `xiaohongshu-scraper-codex`，接入 orchestrator、fetch-codex、report-codex 形成完整链路。
6. 清理 codex 相关 README / SKILL.md 中的漂移描述、冗余章节与失效 login 边界描述。
7. 在验证 codex 体系可用后，将文档中的推荐入口切换到 codex 版，但旧版目录继续保留。

## Open Questions

- 是否需要为维护/调试场景保留一个仅内部使用的独立登录入口脚本说明？
- codex 版是否需要引入单独的 `run_state.json` 作为内部状态真相源，还是继续以 `tasks.md` 为唯一外显状态？
- README 是只补充 codex 入口，还是同时将旧入口显式标记为 legacy？