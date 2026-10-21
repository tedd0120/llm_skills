# 图标库选型与接入

## 选型与导入对照

优先沿用目标项目 `package.json` 中已安装的图标库及本地封装。需新增选型时，按视觉特征挑选并按项目使用的技术静态导入：

| 图标库 | 官方目录 / 仓库 | 依赖包 | 风格特征 | 标准导入与调用示例 |
| :--- | :--- | :--- | :--- | :--- |
| **Lucide** | [lucide.dev/icons](https://lucide.dev/icons) / [GitHub](https://github.com/lucide-icons/lucide) | `lucide-react` | 24×24 轮廓线，shadcn/ui 默认标配，无品牌 Logo | `import { Clock } from "lucide-react";`<br>`<Clock className="size-4" />` |
| **Tabler** | [tabler.io/icons](https://tabler.io/icons) / [GitHub](https://github.com/tabler/tabler-icons) | `@tabler/icons-react` | 5800+ 图标，统一 `Icon` 前缀，支持 `stroke` 线宽微调与 Filled 变体 | `import { IconClock } from "@tabler/icons-react";`<br>`<IconClock className="size-4" stroke={1.5} />` |
| **Phosphor** | [phosphoricons.com](https://phosphoricons.com) / [GitHub](https://github.com/phosphor-icons/homepage) | `@phosphor-icons/react` | 6 种粗细变体（Thin/Light/Regular/Bold/Fill/Duotone），支持 `IconContext` | `import { Clock } from "@phosphor-icons/react";`<br>`<Clock className="size-4" weight="bold" />` |
| **Hugeicons** | [hugeicons.com/icons](https://hugeicons.com/icons) / [GitHub](https://github.com/hugeicons) | `@hugeicons/react` + `@hugeicons/core-free-icons` | 现代圆角笔触，渲染器与图标数据分离（旧包 `hugeicons-react` 已弃用） | `import { HugeiconsIcon } from "@hugeicons/react";`<br>`import { Clock01Icon } from "@hugeicons/core-free-icons";`<br>`<HugeiconsIcon icon={Clock01Icon} size={16} />` |

## 检索与核对

1. 将界面语义提炼为英文动作或实体关键词（如“时间/历史”对应 `clock`、`history`、`timer`）。
2. 在上表官方目录或对应 GitHub 仓库 `icons/` 目录检索并核对真实导出的图标名称。
3. 仅搜索图标任务：交付候选图标名称、官方展示链接、所属库、支持的变体及推荐理由。

## 样式与无障碍适配

- **尺寸与颜色**：通过 Tailwind 类（`size-4`、`size-5`）或组件 `size` 属性控制；颜色默认继承 `currentColor`。
- **无障碍语义**：纯图标交互按钮必须提供 `aria-label`；装饰性图标配置 `aria-hidden="true"`。
