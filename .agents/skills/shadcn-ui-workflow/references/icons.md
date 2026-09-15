# 图标库选型与接入

## 选型与特性对比

优先沿用目标项目已有图标库及封装（检查 `package.json` 中的依赖）。需新增或选型时，按视觉特征与功能需求挑选：

| 图标库 | 官方网站 / 仓库 | 依赖包 | 风格特征与典型场景 |
| :--- | :--- | :--- | :--- |
| **Lucide** | [lucide.dev](https://lucide.dev/icons) / [GitHub](https://github.com/lucide-icons/lucide) | `lucide-react` | 社区通用标配，24×24 轮廓线风格，与 shadcn/ui 深度整合。无品牌 Logo。 |
| **Tabler Icons** | [tabler.io/icons](https://tabler.io/icons) / [GitHub](https://github.com/tabler/tabler-icons) | `@tabler/icons-react` | 5800+ 矢量轮廓图标，统一 24×24 栅格，覆盖面广，支持描边细调与 Filled 变体。 |
| **Phosphor Icons** | [phosphoricons.com](https://phosphoricons.com) / [GitHub](https://github.com/phosphor-icons/homepage) | `@phosphor-icons/react` | 6 种视觉重量（Thin, Light, Regular, Bold, Fill, Duotone），支持 `IconContext` 全局配置。 |
| **Hugeicons** | [hugeicons.com](https://hugeicons.com) / [GitHub](https://github.com/hugeicons) | `@hugeicons/react`<br>`@hugeicons/core-free-icons` | 现代圆角笔触（Stroke Rounded），支持双色调与次要色透明度，视觉现代精致。 |

## 检索与核对

1. 将需求提炼为英文动作或实体关键词（例如“时间/历史”检索 `clock`, `history`, `timer`）。
2. 在对应官方目录检索并预览候选图标：
   - **Lucide**：[Lucide 图标目录](https://lucide.dev/icons/)（或 `site:lucide.dev/icons/ <关键词>`），源码见 GitHub `icons/` 目录。
   - **Tabler Icons**：[Tabler 图标目录](https://tabler.io/icons)（可按分类筛选），源码见 GitHub `icons/` 目录。
   - **Phosphor Icons**：[Phosphor 探索器](https://phosphoricons.com)（可实时切换 6 种粗细变体），源码见 GitHub 仓库。
   - **Hugeicons**：[Hugeicons 搜索器](https://hugeicons.com/icons)（可按风格分类筛选），源码见 GitHub 仓库。
3. 仅搜索图标任务：交付候选图标名称、官方展示链接、所属库、支持的风格变体及推荐理由。

## 接入与导入范式

按项目技术栈和已选图标库静态导入所需图标：

### Lucide
```tsx
import { Clock } from "lucide-react";

export function Example() {
  return <Clock className="size-4" />;
}
```

### Tabler Icons
组件统一以 `Icon` 前缀命名，支持 `stroke` 属性微调线宽：
```tsx
import { IconClock } from "@tabler/icons-react";

export function Example() {
  return <IconClock className="size-4" stroke={1.5} />;
}
```

### Phosphor Icons
支持通过 `weight` 属性切换粗细形态，或通过 `IconContext.Provider` 提供全局默认值：
```tsx
import { Clock } from "@phosphor-icons/react";

export function Example() {
  return <Clock className="size-4" weight="bold" />;
}
```

### Hugeicons
由渲染组件与核心图标数据包组合使用（旧包 `hugeicons-react` 已弃用）：
```tsx
import { HugeiconsIcon } from "@hugeicons/react";
import { Clock01Icon } from "@hugeicons/core-free-icons";

export function Example() {
  return <HugeiconsIcon icon={Clock01Icon} size={16} />;
}
```

## 样式与可访问性适配

- 尺寸：优先通过 Tailwind 类（如 `size-4`, `size-5`）或组件属性控制。
- 颜色：优先继承 `currentColor`，随父级文字颜色自适应。
- 可访问性：交互式按钮必须提供明确的 `aria-label`；装饰性图标配置 `aria-hidden="true"`。
