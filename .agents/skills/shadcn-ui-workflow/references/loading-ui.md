# Loading UI 选型与接入

## 场景选型映射

从 [Loading UI](https://loading-ui.com/docs)（仓库 [turbostarter/loading-ui](https://github.com/turbostarter/loading-ui)）按等待语义选择指示器，同一视口限制可见加载器数量（常规大块布局占位直接使用本地或 shadcn/ui `skeleton`）：

- **按钮与表单行内提交**：紧凑旋转类（`ring`, `classic`, `spokes`, `triple-dot-spinner`）。
- **AI 思考生成与状态标签**：微光扫光或呼吸打字类（`text-shimmer`, `text-shimmer-wave`, `pulse-dot`, `typing`, `text-dots`）。
- **异步队列与列表刷新**：点阵、条形或波形类（`dots`, `bars`, `wave`, `bouncing-dots`）。
- **终端或极客风格界面**：字符轨迹或块状动画类（`terminal`, `accordion-loader`, `square-snake`）。

## 依赖评估与安装

- **零额外依赖优先**：大多数组件基于纯 SVG 与 CSS Keyframes，仅依赖 `cn`。`text-shimmer`、`text-shimmer-wave`、`bobbing-dots`、`pulsating-dots`、`morphing-infinity`、`analyzing-image` 依赖 `motion`（`motion/react`）；未安装 `motion` 的项目优先选用纯 SVG/CSS 变体。
- **CLI 安装**：直接执行 `npx shadcn@latest add https://loading-ui.com/r/<name>.json`，或在 `components.json` 的 `registries` 中配置 `"@loading-ui": "https://loading-ui.com/r/{name}.json"` 后执行 `npx shadcn@latest add @loading-ui/<name>`。
- **手动接入**：从 [组件文档](https://loading-ui.com/docs/components) 复制源码至项目 UI 目录。

## 样式与无障碍适配

- **尺寸与颜色**：通过 `className` 传入 `size-4`、`size-5` 等尺寸类；颜色默认继承 `currentColor`。
- **周期控制**：通过 CSS 变量调整速度，如 `style={{ "--duration": "1.5s" } as React.CSSProperties}`。
- **无障碍语义**：紧邻说明文案的指示器标记 `aria-hidden="true"`；独立呈现的加载器配置 `role="status"` 与 `<span className="sr-only">加载中...</span>`。

## 按需资料

- 组件目录：[Loading UI Components](https://loading-ui.com/docs/components)
- 全量索引：[llms.txt](https://loading-ui.com/llms.txt)、[llms-full.txt](https://loading-ui.com/llms-full.txt)
