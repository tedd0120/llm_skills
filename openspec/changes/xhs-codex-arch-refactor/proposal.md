## 为什么

当前小红书技能体系存在架构边界与实际实现不一致的问题：文档、规范与代码对 `xiaohongshu-login`、编排层职责、报告生成链路的描述已经发生漂移；同时 `summarize` 与 `formatter` 围绕同一 `_index.md` 产物形成了高耦合、低复用的分层，导致维护成本上升。现在需要在不覆盖现有技能的前提下，建立一套带 `-codex` 后缀的新技能体系，作为清晰、可演进的目标架构。

这项变更要解决两个问题：一是为后续实现提供一套边界稳定的新架构；二是清理仓库中与真实实现不一致、重复或过时的技能说明，降低后续维护与迁移成本。

## 变更内容

- 新增一套带 `-codex` 后缀的小红书技能，避免覆盖现有 skills。
- 新建 `xiaohongshu-scraper-codex` 作为唯一用户入口，负责澄清与对外展示进度。
- 新建内部编排层（orchestrator），将目录创建、登录、阶段调度、状态管理从散落的文档约束下沉为内部执行结构。
- 新建 `xiaohongshu-fetch-codex` 作为独立抓取引擎，保留采集边界，不与报告层合并。
- 新建 `xiaohongshu-report-codex`，合并原 `xiaohongshu-summarize` 与 `xiaohongshu-formatter` 的职责，统一生成最终 `_index.md`。
- 新建 `xiaohongshu-core-codex` 作为共享基础层，承载 selectors、browser/session、auth、schema 等公共能力。
- 清理冗余与漂移描述，包括重复的选择器脚本、过时的 `xiaohongshu-login` 引用，以及与新架构不一致的技能文档描述。
- **BREAKING**：无运行时破坏性变更；旧技能保留不动，但文档对“推荐入口”的描述将切换到 codex 版技能体系。

## 功能 (Capabilities)

### 新增功能
- `xhs-codex-skill-suite`: 定义带 `-codex` 后缀的新小红书技能套件、入口边界与共享基础层。
- `xhs-codex-report-pipeline`: 定义将报告生成与格式化合并后的统一报告流水线能力。
- `xhs-codex-doc-cleanup`: 定义与 codex 架构一致的文档清理规则，移除失效、重复和漂移描述。

### 修改功能
- `xiaohongshu-scraper`: 将架构说明更新为“旧版保留、codex 版为新目标架构”的并存关系。
- `xhs-login`: 调整登录边界说明，登录作为 codex 编排层内部能力存在，而不再作为新体系中的独立技能边界。

## 影响

- 受影响目录：`.claude/skills/` 下的小红书相关 skills，及其 `scripts/` 子目录。
- 受影响文档：相关 `SKILL.md`、README 小红书模块说明、必要的 OpenSpec 增量规范。
- 受影响实现边界：报告生成链、登录边界、共享脚本位置、选择器文件组织方式。
- 受影响维护方式：新架构以 codex 目录为目标实现，旧技能作为兼容参考保留。