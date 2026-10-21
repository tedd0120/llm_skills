# Animate UI 选型与接入

## 选型与版本核对

- **适用场景**：将 [Animate UI](https://animate-ui.com/docs)（仓库 [imskyleen/animate-ui](https://github.com/imskyleen/animate-ui)）用于应用内交互控件与微交互：
  - **交互控件原语**：为 Accordion、Dialog、Tabs、Switch、Tooltip 等控件添加状态过渡与弹簧反馈。
  - **应用内微交互组件**：波纹/流体/翻转等交互按钮（`ripple`, `liquid`, `flip`, `copy`）、应用内滑动计数器（`sliding-number`）、交互态动效图标及微交互背景。
- **版本与环境前提**：先检查 `package.json` 与 `components/animate-ui/` 本地目录。当前 v2（`@animate-ui/react`）提供 Radix UI、Base UI、React Aria 动效原语，要求 **React 19** 与 `motion`；使用 `@animate-ui/cli` 要求 **Node.js >= 22.12**（详见 [包文档](https://animate-ui.com/docs/react) 与 [CLI 文档](https://animate-ui.com/docs/cli)）。环境不满足时说明具体版本缺口并保持现有实现。

## 接入方式

安装核心依赖（如 `npm install @animate-ui/react motion`）后，按项目现有组件形态选择接入路径（详见 [Installation](https://animate-ui.com/docs/installation)）：

- **已有 shadcn/ui 组件**：先通过 `--dry-run` 预览 CLI 对目标组件的改造范围：
  ```bash
  npx @animate-ui/cli@latest animate accordion --dry-run
  ```
  核对无误后去掉 `--dry-run` 执行（仅在任务明确覆盖全量组件时使用 `animate all`）。CLI 会替换底层原语导入并清理被 Motion 接管的 CSS 动画类。
- **直接组合无头基础库的组件**：按基础库替换原语导入路径（如 Radix Dialog 替换为 `@animate-ui/react/primitives/radix-ui/dialog`，Base UI Dialog 替换为 `@animate-ui/react/primitives/base-ui/dialog`），并移除同一元素上冲突的 CSS 进出场过渡。
- **微交互组件与动效图标**：按组件页面文档从对应子路径导出或拷入源码。
- **v1 本地源码迁移**：对照 [官方迁移说明](https://github.com/imskyleen/animate-ui/blob/main/skills/animate-ui/references/migrate.md) 评估本地定制与调用方后执行迁移。

## 特有样式与节奏适配

- **居中定位冲突排查**：Tailwind CSS v3 的 `-translate-x-1/2 -translate-y-1/2` 类会与 Motion 的 `transform` 属性冲突，需核对弹窗实际居中位置；Tailwind CSS v4 使用独立 `translate` 属性时可正常共存。
- **全局节奏控制**：需要统一调整动画速率时，在外层挂载 `AnimateUIProvider` 并配置 `tempo` 属性。

## 按需资料

- 组件文档：[Animate UI Docs](https://animate-ui.com/docs)
- 进阶规则与图标制作：[官方 Animate UI skill](https://github.com/imskyleen/animate-ui/blob/main/skills/animate-ui/SKILL.md)
