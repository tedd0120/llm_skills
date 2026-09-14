# coss ui 选型与接入

## 选型

- 将 [coss ui](https://coss.com/ui/docs) 的紧凑尺寸、状态变体和 [Particles](https://coss.com/ui/particles) 业务组合纳入候选。仅借鉴视觉或组合时，使用项目已有基础组件实现。
- 采用组件源码前确认其基础库：coss ui 使用 Base UI；若项目包含 Origin UI 历史组件，先核对其基础库与维护状态。按目标组件当前文档和 registry 源码选型。
- 需要新增 Base UI 实现时，明确它解决的功能缺口与依赖成本；已有 Radix 功能的替换按完整组件迁移评估，覆盖调用方和交互验证。

## 源码与安装

1. 阅读目标组件文档和 registry 条目，确认源码、依赖及递归引入的组件。核对 [目录许可](https://github.com/cosscom/coss/blob/main/LICENSING.md)：`apps/ui/`、`apps/origin/` 为 MIT 例外，其余目录默认 AGPLv3；记录实际采用路径并保留适用许可声明。
2. 确认项目满足 React 与 Tailwind CSS v4 前提。沿用 components.json 的路径、别名和现有包管理器；按组件页面提供的 registry 名称单项添加，例如 `npx shadcn@latest add @coss/button`。若当前 CLI 无法解析命名空间，查阅官方文档确认 registry 地址后配置，或按文档手动引入。
3. 安装前比较同名本地组件与递归依赖，已有定制组件采用选择性合并。`@coss/ui` 是全部基础组件，`@coss/style` 涉及完整主题与字体；仅在任务需要全套接入时使用。
4. 安装后审查源码、依赖、CSS 和锁文件差异，复用项目 cn 工具与别名。按具体文件替换 Next.js 示例中的 Link、字体或布局接线，适配目标项目的运行入口。

安装细节以 [Get Started](https://coss.com/ui/docs/get-started) 和目标组件页面为准。

## API 与交互适配

- 按 [Radix 迁移指南](https://coss.com/ui/docs/radix-migration) 逐项核对 props、事件、受控值和 DOM 状态属性。常见差异包括 `asChild` → `render`、Menu item `onSelect` → `onClick`，以及 Content、Popup、Panel 的组合结构；以目标组件实际 API 为准。
- 保持复合组件内部使用同一套上下文。跨库嵌套弹层时实际验证焦点、Esc 和关闭顺序；已有弹窗的退出动画与焦点处理需要按目标基础库生命周期重新评估。
- 验证键盘导航、焦点恢复、禁用与 loading 状态及业务回调。涉及 Portal 时检查挂载容器、层级、滚动和官方要求的根容器 `isolation: isolate`，沿用项目已有 UI 验证流程。

## 样式适配

- 按 [Styling](https://coss.com/ui/docs/styling) 检查组件实际引用的 token；按需补齐 info、success、warning 及对应 foreground，以及字体变量。
- 在项目样式入口的现有语义映射中扩展，保持项目原有 `--accent`、`--muted` 的语义；所需基础样式按项目约定局部添加，保留当前 Preflight 策略。
- 将 `--font-sans`、`--font-mono`、`--font-heading` 接到本地字体入口。使用项目配色时验证透明边框、阴影和焦点环的可见性，并检查本次涉及的交互状态。

## 按需资料

- 查找组件与组合入口时使用 [llms.txt](https://coss.com/ui/llms.txt)。需要更详细的 API、样式或迁移指导时，查阅 [官方 Agent Skills](https://coss.com/ui/docs/skills) 中命中的主题。
- 升级或发现文档与源码不一致时，对照 [Changelog](https://coss.com/ui/docs/changelog) 与目标 registry 的当前依赖、源码，确定适用行为。
