# `.gitignore` 分析

目标：每个路径是否进入版本库都有明确理由，规则按归属分节，且不误伤正式资产。

## 判定规则

| 归属 | 规则 |
|---|---|
| `work` | 忽略 `.work/` |
| `local` | 忽略 `.local/`（不带前导 `/`，同时覆盖模块内 `.local/`） |
| `program` | 忽略；依赖、缓存、构建输出按名称忽略，运行时目录用前导 `/` 锚定到确切位置 |
| `secret` | 忽略；模板用 `!` 显式放行（`.env` + `.env.*` + `!.env.example`） |
| `asset` | 不得被任何规则命中；命中则收窄规则或加 `!` 放行 |
| `legacy` | 迁移后作为防御性规则保留，防止旧工具或 skill 误建后被提交 |
| 占位目录 | `dir/*` + `!dir/.gitkeep`，不用 `dir/`（后者无法放行子项） |

需要问用户的典型条目：`.claude/`、`.codex/`、`.cursor/`、`.vscode/`（团队共享配置与本机状态混放）；`data/`、`inputs/`、`configs/`（数据与模板混放）。按子路径拆分，例如 `.claude/settings.local.json` 忽略、`.claude/settings.json` 跟踪。

## 必查项

逐项执行并把结论写入 `plan.md`：

1. **已跟踪却命中忽略规则**：`git ls-files -ci --exclude-standard`。每个文件判定是规则过宽（收窄规则）还是文件不该跟踪（`git rm --cached`，需用户授权）。
2. **规则误伤**：对每条不带 `/` 的目录规则（如 `plans/`），用 `git ls-files | grep -E '(^|/)<名称>/'` 查找它在深层命中的已跟踪路径；再对正式资产关键文件执行 `git check-ignore -v --no-index <路径>`，确认未被命中（如 `CONTEXT.md`、`docs/**`）。
3. **漏忽略**：扫描结果中非 `asset` 且 `untracked_unignored_files > 0` 的条目，补规则。
4. **模块级 `.gitignore`**：`git ls-files '*.gitignore'` 列出全部；根规则与模块规则重复时保留一处，模块自治的保留在模块内。
5. **自写的 `.gitignore`**：目录内容仅为 `*` 的 `.gitignore`（工具自建）说明该目录未在根规则登记，补登记。

## 文件组织

按以下分节重排根 `.gitignore`，每节一行注释说明归属，规则只出现一次：

```gitignore
# 开发产物：任务工作区与本机持久状态
.work/
.local/

# 旧布局与第三方工具固定输出目录（防御性忽略）
...

# 程序自管：运行态与锁
...

# 依赖、构建与缓存
...

# AI 客户端与编辑器本机状态
...

# 机密与本机配置
...
```

改动前后各执行一次 `git status --porcelain --ignored`，对比差异：新出现的未跟踪文件说明规则被放宽，消失的已跟踪文件说明误伤。差异逐条解释后才算完成。
