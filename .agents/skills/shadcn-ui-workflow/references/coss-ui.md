# coss ui 选型与接入

## 选型与许可边界

- **适用场景**：需要高密度紧凑尺寸、丰富状态变体、[coss Particles](https://coss.com/ui/particles) 业务组合片段，或项目基于 Base UI 构建。仅借鉴视觉排版时，直接使用项目已有基础组件组合。
- **基础库核对**：[coss ui](https://coss.com/ui/docs) 基于 `@base-ui/react` 构建；若项目包含 Origin UI 历史组件，先核对其底层依赖再决定复用或迁移。在 Radix 项目中引入 Base UI 组件前，明确其解决的功能缺口与依赖成本。
- **许可核对**：对照 [LICENSING.md](https://github.com/cosscom/coss/blob/main/LICENSING.md)，仅 `apps/ui/` 与 `apps/origin/` 适用 MIT 许可，仓库其余目录默认 AGPLv3。记录实际采用路径并保留许可声明。

## 源码与安装

1. 确认项目满足 React 与 Tailwind CSS v4 前提。
2. 按组件文档提供的 registry 名称单项添加（参考 [Get Started](https://coss.com/ui/docs/get-started)）：
   ```bash
   npx shadcn@latest add @coss/button
   ```
   `@coss/ui` 会拉取全量基础组件，`@coss/style` 会重写完整主题与字体，仅在全套初始化任务中使用。
3. 替换上游示例中的 Next.js 专属导入（如 `next/link`、`next/font`），适配目标项目路由与字体入口。

## Radix 迁移与交互适配

按 [Radix 迁移指南](https://coss.com/ui/docs/radix-migration) 核对 API 差异：
- **组合委托**：`asChild` 替换为 `render` 属性（如 `render={<Link to="/home" />}`）。
- **事件与结构**：Menu item 的 `onSelect` 替换为 `onClick`；核对 `Portal`、`Positioner`、`Popup`、`Panel` 的层级组合关系。
- **根容器隔离**：涉及 Portal 弹层时，按官方要求在应用根容器配置 `isolation: isolate`，跨库嵌套弹层时实测焦点恢复与 Esc 关闭顺序。

## 样式适配

- 按 [Styling](https://coss.com/ui/docs/styling) 补齐组件引用的扩展语义变量：`--info`、`--success`、`--warning` 及其对应 `-foreground` 变量。
- 在现有样式入口中将 `--font-sans`、`--font-mono`、`--font-heading` 映射到本地字体变量，保持项目既有 `--accent` 与 `--muted` 语义，并验证透明边框、阴影及焦点环在明暗主题下的对比度。

## 按需资料

- 组件索引：[llms.txt](https://coss.com/ui/llms.txt)
- 专项指南：[官方 Agent Skills](https://coss.com/ui/docs/skills)、[Changelog](https://coss.com/ui/docs/changelog)
