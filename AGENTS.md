# Agent 指引

## Skill 编辑默认路径

当任务是编辑 skill 时，默认编辑**当前项目目录**下的 skill（`.agents/skills/`），而不是用户主目录下的全局 skill（`~/.agents/skills/`）。

## Skill 产出物默认目录

所有 skill 的产出物（报告、抓取结果、导出文件等）默认落到**仓库根目录**的 `data/` 下，每个 skill 使用自己独特的子文件夹：

```
data/{skill 独特指定文件夹}/
```

- 例如 litellm-model-speedtest 落到 `data/litellm-model-speedtest/`。
- 脚本内用向上找 `.git` 的方式定位仓库根目录，保证输出与运行时的 cwd 无关。
- `data/` 已在 `.gitignore` 中忽略，产出物不进版本库。