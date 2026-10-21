# Magic UI 选型与接入

## 场景选型映射

将 [Magic UI](https://magicui.design/docs)（仓库 [magicuidesign/magicui](https://github.com/magicuidesign/magicui)）用于产品宣传页、营销展示区块与展示型视觉特效，控制同一视口内持续运动元素的数量：

- **品牌与社会认同**：`marquee`（跑马灯）、`avatar-circles`（头像组）。
- **功能与架构展示**：`bento-grid`（便当盒网格）、`terminal`（终端演示）、`animated-beam`（节点连接光束）、`globe`（3D 地球）。
- **展示大字与营销数字**：`text-animate`（展示型文字进场）、`number-ticker`（营销数字滚动计数）。
- **宣传页背景与边框**：`particles`（Canvas 粒子背景）、`grid-pattern`（网格背景）、`border-beam`（流光边框）。

## 源码与安装

1. 核对目标组件页面的运行时依赖（`motion`、Canvas、WebGL/Cobe 等）及所需 Tailwind CSS keyframes。
2. 通过 shadcn CLI 单项添加（参考 [Installation](https://magicui.design/docs/installation)）：
   ```bash
   npx shadcn@latest add @magicui/globe
   ```
   手动引入时，同步补齐官方页面列出的依赖、工具函数与 CSS keyframes 配置。

## 渲染与性能适配

- **Canvas / WebGL 生命周期**：使用 `globe`、`particles` 等连续帧渲染组件时，监听容器尺寸变化（ResizeObserver），并在组件卸载时销毁实例与动画帧，控制首屏加载体积与帧率。
- **内容替换**：将官方示例中的演示文案、Mock 头像或演示终端指令替换为真实业务数据。

## 按需资料

- 组合与选型参考：[官方 Magic UI skill](https://github.com/magicuidesign/magicui/blob/main/skills/magic-ui/SKILL.md)
- MCP 检索（环境已配置时）：[Magic UI MCP](https://magicui.design/docs/mcp)
