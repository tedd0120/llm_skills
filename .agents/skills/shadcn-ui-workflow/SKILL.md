---
name: shadcn-ui-workflow
description: 新增、修改或替换 UI 组件、调整界面样式与交互、搜索图标、添加动效与加载状态，或构建 AI 助手对话界面时使用；优先复用项目已有组件，结合 shadcn/ui、coss ui、Loading UI、Magic UI、Animate UI 与 assistant-ui 选型，通过常用图标库（Lucide、Tabler、Phosphor、Hugeicons）搜索图标，并按目标项目使用的技术完成适配与验证。纯后端任务不触发。
---

# 通用 UI 组件工作流

1. **前置分流与目标定位**
   - 仅搜索图标时，直接读取 [图标库选型与接入](references/icons.md)，检索并交付候选图标名称、官方链接、所属库与推荐理由后结束流程。
   - 遵循目标项目的代码检索规则、UI 规范与设计令牌文档，确认现有组件、调用方、业务回调和样式入口。只修改文案、间距或颜色时，直接调整现有组件并跳至第 5 步验证。

2. **按场景选型（仅读取命中的分支文件）**
   - **常规基础控件与布局骨架屏**：优先复用本地 UI 组件；缺少时查阅 [shadcn/ui 官方组件](https://ui.shadcn.com/docs/components)。
   - **Base UI 基础库、高密度紧凑控件、业务组合片段（coss Particles）或指定 coss**：读取 [coss ui 选型与接入](references/coss-ui.md)。
   - **专用加载指示器（多形态旋转、队列点阵/波形、AI 生成微光/打字等待、终端加载器）**：读取 [Loading UI 选型与接入](references/loading-ui.md)。
   - **应用内交互控件与微交互（Dialog/Tabs/Accordion/Switch/Tooltip 等状态过渡、波纹/流体交互按钮、滑动计数器、交互图标动画、微交互背景）**：读取 [Animate UI 选型与接入](references/animate-ui.md)。
   - **产品宣传页与营销展示区块（Bento Grid、Marquee 跑马灯、Globe 地球、Animated Beam 光束、Terminal、Border Beam、展示大字、营销数字滚动、粒子与网格背景）**：读取 [Magic UI 选型与接入](references/magic-ui.md)。
   - **AI 聊天对话流、消息流式渲染、历史会话列表或 Tool Call 生成式 UI**：读取 [assistant-ui 选型与接入](references/assistant-ui.md)。
   - **新增或替换静态矢量图标**：读取 [图标库选型与接入](references/icons.md)。

3. **按需引入与差异审查**
   - 检查目标应用的 `components.json`、`package.json` 和锁文件，沿用已配置的组件风格、基础库、路径别名、`cn` 工具与包管理器。
   - `shadcn/ui` 执行 `npx shadcn@latest add <组件名>` 添加；其余组件库与图标库按命中的参考文件引入。
   - 同名组件已存在时，比对上游源码与本地修改后选择性合并，保护本地定制源码。
   - 审查生成文件、CSS 入口（保护既有 `body` 样式、主题变量与 Preflight 策略）、依赖和锁文件差异，保留上游适用许可声明。

4. **适配实现**
   - 将通用 UI 源码放入配置的 UI 目录，页面布局组合、业务状态与数据访问保留在业务层；调整基础组件前核对全部调用方。
   - 保持同一复合组件的 `Root`、`Trigger`、`Popup`、`Content` 来自同一基础库。核对项目语义令牌的真实含义后映射颜色、尺寸与字体变量。
   - 按目标框架适配路由、链接、字体与 SSR 客户端边界；Electron 项目的标题栏交互控件补充 `-webkit-app-region: no-drag`。
   - **动效附加约束**：同一元素的同一动画属性仅由单一机制驱动，引入 Motion 时清理冲突的 CSS `transform` 与 `transition`，保留颜色等独立过渡；确保 SSR 首屏主要内容在水合前可见；持续背景、滚动条与 Canvas 动画在离屏或页面隐藏时暂停并在卸载时释放资源；动效文字与数字保留稳定可访问文本，按需控制 live region 播报频率。
   - 官方组件不满足需求时，明确功能缺口并采用最小自定义实现，常规选型直接决策执行。

5. **验证**
   - 运行 `package.json` 中相关的类型检查与构建命令。
   - 在项目支持的主题与视口尺寸下，实际操作验证默认、悬停、焦点、禁用及展开状态。
   - 涉及弹层时，验证 Portal 容器、层级、滚动、Esc 关闭、焦点限制与恢复及嵌套关闭顺序；包含退出动画时确认关闭后焦点限制及时解除。
   - 涉及动效时，验证 `prefers-reduced-motion` 下的内容可达性，以及快速重复触发、中途打断和反向切换时的最终状态与业务回调。

6. **交付**
   - 说明采用的组件及来源链接、基础库、本地适配点与验证结果，区分已验证项目与未验证项目。
   - 新增项目专属适配或迁移约定时记录至目标项目文档；遵循 `AGENTS.md` 的 Git 授权规则。官方资料不可访问时如实说明，仅将本次实际读取的官方代码标注为官方源码。
