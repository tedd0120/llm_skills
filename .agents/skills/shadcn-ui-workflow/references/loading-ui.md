# Loading UI 选型与接入

## 选型

- 将 [Loading UI](https://loading-ui.com/docs)（仓库 [turbostarter/loading-ui](https://github.com/turbostarter/loading-ui)）作为加载指示与动画候选。
- 保持等待形态与界面语义匹配：
  - 按钮与表单行内提交：选择紧凑的环形、经典叶片或多点旋转（如 `ring`, `classic`, `spokes`, `triple-dot-spinner`）。
  - 文本标签与 AI 生成：选择微光扫光或呼吸动效（如 `text-shimmer`, `text-shimmer-wave`, `pulse-dot`, `typing`, `text-dots`）。
  - 异步队列与列表刷新：选择点阵、条形或波形（如 `dots`, `bars`, `wave`, `bouncing-dots`）。
  - 终端或极客风格：选择字符轨迹或块状贪吃蛇（如 `terminal`, `accordion-loader`, `square-snake`）。
  - 结构化大块数据排版：使用骨架屏（`skeleton`）保持布局稳定。
- 单一界面限制可见的加载指示器数量。

## 源码与安装

1. 确认项目配置了 React 与 Tailwind CSS。
2. 配置 registry 安装：在 `components.json` 的 `registries` 中添加 `"@loading-ui": "https://loading-ui.com/r/{name}.json"`，执行 `npx shadcn@latest add @loading-ui/<name>`。
3. 直接通过 URL 安装：执行 `npx shadcn@latest add https://loading-ui.com/r/<name>.json`。
4. 手动接入：从 [Loading UI 组件文档](https://loading-ui.com/docs/components) 复制组件代码至项目 UI 目录（如 `components/loading-ui/<name>.tsx`），更新 `@/lib/utils` 别名。
5. 审查生成文件、样式类与依赖变动。

## 依赖评估

- 大多数组件基于纯 SVG 与 CSS Keyframes 构建，仅依赖本地 `cn` 工具函数。
- `text-shimmer`、`text-shimmer-wave`、`bobbing-dots`、`pulsating-dots`、`morphing-infinity`、`analyzing-image` 等组件依赖 `motion`（`motion/react`）。
- 未安装 `motion` 的项目优先选用纯 SVG 或 CSS 变体。

## 样式与可访问性适配

- 尺寸通过 `className` 传递 Tailwind 尺寸类控制，如 `size-4`、`size-5`。
- 颜色默认继承 `currentColor`，通过文本颜色类适配所在容器。
- 动画周期通过 CSS 变量 `--duration` 调整，例如 `style={{ "--duration": "1.5s" } as React.CSSProperties}`。
- 装饰性或已有周围文案说明的指示器标记 `aria-hidden="true"`。
- 独立状态指示器配置 `role="status"` 与 `<span className="sr-only">Loading...</span>`。

## 按需资料

- 浏览全部可用指示器查看 [Loading UI Components](https://loading-ui.com/docs/components)。
- 获取全量 LLM 上下文可查阅 [llms.txt](https://loading-ui.com/llms.txt) 与 [llms-full.txt](https://loading-ui.com/llms-full.txt)。
