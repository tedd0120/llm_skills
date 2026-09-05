# Agent 指引

## 措辞与断言

写注释、docstring、命名、断言、错误信息和 Markdown 文档时，每句话只承载一条新信息。落笔前检查两类冗余否定：

- **镜像尾巴（Mirrored Tail）**：前半句已经界定范围时，删除后半句对范围外情况的镜像否定或许可。若删掉后半句语义不变，就以较短表述为准。
- **悬空否定（Dangling Negation）**：先判断被否定的选项在当前步骤是否仍然可达；已被上游排除的选项不再列入本步骤的说明。

断言和测试命名遵循同一规则。`keeps_X_excludes_not_X` 之类的对仗名称只保留承载真实区分的部分；多个真实互斥约束分别表达。需要强调完备性时，列出当前步骤仍可接收的输入形态，以此界定边界。

## Skill 编辑默认路径

当任务是编辑 skill 时，默认编辑**当前项目目录**下的 `.agents/skills/`。
只有用户主动要求时，才可修改全局 skill。

## Skill 产出物默认目录

所有 skill 的产出物（报告、抓取结果、导出文件等）默认落到**仓库根目录**的 `data/` 下，每个 skill 使用自己独特的子文件夹：

```
data/{skill 独特指定文件夹}/
```

- 例如 litellm-model-speedtest 落到 `data/litellm-model-speedtest/`。
- 脚本内用向上找 `.git` 的方式定位仓库根目录，保证输出与运行时的 cwd 无关。
- `data/` 已在 `.gitignore` 中忽略。

## Prototype 产出物默认目录

所有 prototype 产出物落到仓库根目录的 `.prototype/` 下。目录结构为：

```
.prototype/{yyyyMMdd_时分秒_prototype主题}/产物
```

- `.prototype/` 已在 `.gitignore` 中忽略。

