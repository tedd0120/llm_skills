---
name: shadcn-ui-workflow
description: 新增、修改或替换 UI 组件、调整界面样式与交互、搜索图标、添加动效与加载状态，或构建 AI 助手对话界面时使用；优先复用项目已有组件，结合 shadcn/ui、coss ui、Loading UI、Animate UI 与 assistant-ui 选型，通过常用图标库（Lucide、Tabler、Phosphor、Hugeicons）搜索图标，并按目标项目的技术栈完成适配与验证。纯后端任务不触发。
---

# 通用 UI 组件工作流

1. 定位目标：遵循目标项目的代码检索规则，确认现有组件、调用方、业务回调和样式。读取 [项目适配约定](references/project-integration.md)，明确本次改动范围。
2. 优先复用：检查本地 UI 组件。只改文案、间距或颜色时，直接修改现有实现；需要新增交互或替换控件时，查阅 [shadcn/ui 官方组件](https://ui.shadcn.com/docs/components) 的文档、示例和源码。需要紧凑变体、业务组合示例或用户指定 coss 时，读取 [coss ui 选型与接入](references/coss-ui.md)，补充比较组件与 Particles，选定来源和基础库。
   需要加载指示、旋转状态、骨架或 AI 等待动效时，读取 [Loading UI 选型与接入](references/loading-ui.md)，按等待场景选择组件。
   需要复杂交互动效、微交互、动态背景或数字文本过渡时，读取 [Animate UI 选型与接入](references/animate-ui.md)，选定动效原语。
   需要 AI 聊天对话、消息流式渲染、智能助手或生成式 UI 时，读取 [assistant-ui 选型与接入](references/assistant-ui.md)，规划运行时与对话原语。
   需要搜索、新增或替换图标时，读取 [图标库选型与接入](references/icons.md)，按界面语义检索并核对候选图标。仅搜索图标时，交付候选名称、官方链接和推荐理由即可。
3. 按需引入：先查看目标应用的 components.json（如有）、package.json 和锁文件，沿用已配置的组件风格、基础库、路径与包管理器。shadcn/ui 通过 `npx shadcn@latest add <组件名>` 添加缺少的组件；coss 按其参考文件单项引入；Loading UI 按其参考文件配置 registry 或单项添加；Animate UI 按其参考文件通过 `@animate-ui` registry 单项添加或复制源码；assistant-ui 按其参考文件通过 CLI 初始化或安装运行时包引入；图标库按其参考文件核对现有依赖与图标导出后按需导入。审查生成文件、CSS、依赖和锁文件差异。已有组件先比较上游源码与本地修改，再有选择地合并；禁止用覆盖选项直接覆盖定制源码。
4. 适配实现：组合基础组件实现业务界面，将源码放入配置的 UI 目录；业务状态与数据访问保留在业务层。匹配项目主题、尺寸和交互。官方组件不合适时，明确缺口，采用最小自定义实现，无需为常规选型反复请求确认。
5. 验证：运行 package.json 中相关类型检查与构建；用已有 UI 验证方式检查本次涉及的默认、悬停、焦点、禁用及弹层状态。变更有交互时实际操作验证，区分已验证结果和未验证项目。
6. 交付：简要说明采用的组件或组合及来源链接、基础库、本地适配和验证结果。新增项目专属适配或迁移约定时记录在目标项目文档中；遵循 AGENTS.md 的 Git 授权规则。

官方资料不可访问时，如实说明，并基于已存在的组件完成可执行部分；不要把凭记忆编写的代码称为本次获取的官方源码。
