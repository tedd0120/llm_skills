# 令牌与产物契约

## 目录

- [唯一事实源](#唯一事实源)
- [令牌组](#令牌组)
- [扩展字段](#扩展字段)
- [生成映射](#生成映射)
- [完成门槛](#完成门槛)

## 唯一事实源

以 `<slug>-tokens.json` 为唯一事实源。使用 DTCG 风格的 `$value`、`$type`、`$description`，并用 `$extensions.com.website-uiux-extractor` 保存设计系统上下文。

必需根字段：

```json
{
  "$schema": "https://tr.designtokens.org/format/",
  "$description": "Design tokens for Example",
  "meta": {
    "name": "Example",
    "description": "一句能区分该站点的视觉语言总结。",
    "theme": "light"
  },
  "color": {},
  "typography": {},
  "spacing": {},
  "radius": {},
  "$extensions": {
    "com.website-uiux-extractor": {}
  }
}
```

直接复制 `../assets/tokens.example.json` 作为起点。保留 JSON 结构，替换示例内容；删除未观察到的可选令牌组，不用空壳伪装完整度。

## 令牌组

令牌名使用小写 kebab-case。每个令牌包含 `$value`、`$type` 和能解释语义角色的 `$description`。

先做语义去重：

- 完全重复的页面、视口、状态、证据、组件和规则由构建脚本按首次出现顺序合并。
- 同组内同值同义的令牌只保留一个名称。
- 同组内同值但用途不同的令牌保留各自语义名，只让一个令牌保存字面值，其余使用完整别名，例如 `canvas.$value = "{color.white}"`、`on-primary.$value = "{color.white}"`。
- 组件名称相同但定义冲突、路由相同但元数据冲突时停止并人工裁决，不静默选择一份。

| 组 | `$type` | `$value` | CSS 变量 |
|---|---|---|---|
| `color` | `color` | CSS 颜色字符串 | `--color-<name>` |
| `typography` | `typography` | `fontFamily`、`fontSize`、`fontWeight`、`lineHeight`、`letterSpacing` | `--text-*`、`--font-weight-*`、`--leading-*`、`--tracking-*`；唯一字体族另生成 `--font-primary`、`--font-family-2...` |
| `spacing` | `dimension` | CSS 长度 | `--spacing-<name>` |
| `radius` | `dimension` | CSS 长度 | `--radius-<name>` |
| `shadow` | `shadow` | CSS shadow 字符串，或包含 `color`、`offsetX`、`offsetY`、`blur`、`spread`、可选 `inset` 的对象/数组 | `--shadow-<name>` |
| `duration` | `duration` | `ms` 或 `s` | `--duration-<name>` |
| `easing` | `cubicBezier` | 四个数字的数组，或 CSS easing 字符串 | `--ease-<name>` |
| `breakpoint` | `dimension` | CSS 长度 | `--breakpoint-<name>` |

色值优先写不透明 hex；确实存在透明度、广色域或颜色函数时保留源格式。字体值保留网站声明的家族名，并给出系统回退。行高可以是无单位数或 CSS 长度。

## 扩展字段

`$extensions.com.website-uiux-extractor` 至少包含以下结构：

```json
{
  "source": {
    "url": "https://example.com/",
    "capturedAt": "2026-08-14T10:00:00+08:00"
  },
  "coverage": {
    "viewports": ["1440x900", "390x844"],
    "routes": [
      {
        "url": "https://example.com/",
        "family": "landing",
        "states": ["default", "navigation-open"]
      }
    ],
    "gaps": []
  },
  "layout": {
    "density": "comfortable",
    "maxContentWidth": "1200px",
    "sectionGap": "80px",
    "cardPadding": "24px",
    "elementGap": "16px",
    "gridColumns": "12",
    "gutter": "24px"
  },
  "components": [
    {
      "name": "button-primary",
      "role": "主要转化操作",
      "properties": {
        "backgroundColor": "{color.primary}",
        "textColor": "{color.on-primary}",
        "typography": "{typography.button}",
        "radius": "{radius.pill}",
        "padding": "12px 24px"
      },
      "states": ["default", "hover", "focus-visible", "disabled"],
      "specimen": {
        "kind": "button",
        "label": "继续",
        "states": {
          "default": {},
          "hover": {
            "style": {"backgroundColor": "{color.primary-hover}"}
          },
          "focus-visible": {
            "style": {"outlineColor": "{color.primary}"}
          },
          "disabled": {
            "disabled": true,
            "style": {"opacity": 0.48}
          }
        }
      },
      "evidence": [
        {
          "url": "https://example.com/",
          "viewport": "1440x900",
          "state": "default",
          "note": "Hero CTA"
        }
      ]
    }
  ],
  "guidelines": {
    "do": ["用 primary 处理最高优先级操作。"],
    "avoid": ["把强调色扩展为大面积装饰背景。"]
  },
  "responsiveNotes": [],
  "motionNotes": []
}
```

`routes` 按页面族记录代表页面，不列举内容相同的分页或详情实例。`states` 只写实际检查过的状态。`gaps` 记录被登录、权限、地区、反爬或不可复现状态阻断的范围。

组件 `properties` 使用接近 CSS 的属性名；令牌引用必须指向现有路径。把同一个组件的状态放在 `states`，把真正具有不同构造的变体拆成独立组件。

每个组件必须有 `specimen`，以便预览页呈现真实可见的组件，而不是属性文字清单。支持的 `kind`：

- 原生交互控件：`button`、`icon-button`、`input`、`textarea`、`switch`、`slider`、`tabs`。
- 复合与结构样本：`composer`、`card`、`panel`。

`specimen.states` 是要在预览中并排呈现的已观察状态，键必须出现在组件的 `states` 中。每个状态可以设置 `disabled`、`checked`、`selectedIndex`、`value`，`composer` 还可用 `toolsActive` 标出工具按钮选中态；并用 `style` 覆盖 `properties` 中的视觉属性。不要为未观察到的状态或控件类型造样本。

`slider` 还必须给出数字 `min`、`max`、`step`、`value`；`tabs` 必须给出 `secondaryLabel`。预览会为按钮、输入框、开关、滑块和标签页使用对应的原生 HTML 控件，并保留可访问语义。

## 生成映射

构建脚本从同一个 JSON 生成五个顶层文件：

```text
<slug>-DESIGN.md
<slug>-tokens.json
<slug>-variables.css
<slug>-theme.css
<slug>-preview.html
```

`variables.css` 使用 `:root`；`theme.css` 使用 Tailwind CSS v4 的 `@theme`。两者的变量集合和值必须相同。预览页只读取构建时生成的同一变量集合，不维护第二套品牌值；它会从每个组件的 `specimen` 渲染原生控件或结构样本，其下载链接使用其余四个文件带 `<slug>` 前缀的完整文件名。

## 完成门槛

- `color`、`typography`、`spacing`、`radius` 均非空。
- 同一令牌组没有重复字面值；共享值通过完整别名表达。
- 至少有一个组件、一个代表页面和桌面/移动两个不同视口。
- 每个组件都有至少一个可渲染的 `specimen` 状态；采集到按钮、输入框、开关、滑块或标签页时，预览中存在对应的真实控件。
- `source.url` 为 HTTP(S) URL，`capturedAt` 明确采集时间。
- 每个核心组件至少有一条证据；无法取得的证据进入 `coverage.gaps`。
- 所有令牌引用都能解析到现有路径。
- 生成脚本通过，五个顶层文件均非空，预览页完成桌面与移动视觉检查。
