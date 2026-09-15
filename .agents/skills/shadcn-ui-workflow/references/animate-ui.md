# Animate UI 选型与接入

## 选型

- 将 [Animate UI](https://animate-ui.com/docs)（仓库 [imskyleen/animate-ui](https://github.com/imskyleen/animate-ui)）作为动效增强与微交互组件候选。
- 适用场景与分类：
  - 动效原语（Primitives）：自带过渡动画的手风琴、对话框、选项卡、开关、浮动卡片（`accordion`, `dialog`, `tabs`, `switch`, `tooltip`，基于 Radix UI、Base UI 或 Headless UI）。
  - 交互按钮（Buttons）：波纹、流体、翻转、主题切换、点赞计数等动效按钮（`ripple`, `liquid`, `flip`, `theme-toggler`, `copy`）。
  - 文本与数字动效（Texts）：平滑滚动计数器、字符打散进入动效（`sliding-number`, `splitting`）。
  - 动态背景（Backgrounds）：粒子星空、气泡上浮、烟花、重力轨迹（`stars`, `bubble`, `gravity-stars`, `fireworks`）。
  - 动效图标（Animated Icons）：带悬停或触发微动效的图标集合。

## 源码与安装

1. 确认项目满足 React、Tailwind CSS 与 `motion`（`motion/react`）依赖前提。
2. 通过 shadcn CLI 按需添加：
   ```bash
   npx shadcn@latest add @animate-ui/<组件路径>
   ```
   例如添加滚动数字或波纹按钮：
   ```bash
   npx shadcn@latest add @animate-ui/primitives-texts-sliding-number
   npx shadcn@latest add @animate-ui/buttons-ripple
   ```
3. 手动引入：查阅 [Animate UI 官方文档](https://animate-ui.com/docs) 复制代码到项目 UI 目录，按项目别名调整工具函数与依赖导入路径。
4. 审查生成文件、动画依赖与 CSS 类差异。

## 依赖与性能评估

- 组件强依赖 `motion`（`motion/react`）。
- 动效背景（如粒子、烟花）涉及持续帧率渲染，在首屏或关键转化路径上使用时需监测重绘与 GPU 占用。
- 遵循用户的减少动画偏好（`prefers-reduced-motion`），在禁用动效环境下提供即时状态呈现。

## 样式与可访问性适配

- 动画组件遵循项目 Tailwind 主题颜色变量（`primary`, `muted`, `accent` 等）。
- 动效数字与文本变动保证屏幕阅读器正确播报最终内容（配置 `aria-live="polite"`）。
- 弹窗与折叠组件保持原底层库（Radix/Base UI）原生的键盘导航与焦点管理机制。

## 按需资料

- 浏览全部组件与示例：[Animate UI Components](https://animate-ui.com/docs/components)。
- LLM 上下文参考：[llms-full.txt](https://animate-ui.com/llms-full.txt)。
