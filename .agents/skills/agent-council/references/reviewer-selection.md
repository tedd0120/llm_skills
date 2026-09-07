# Reviewer 选择与模型列表探测规范

本文件定义启动会审前，探测并向用户呈现可用模型清单的规范。每次启动必须停在第 7 步等待用户明确确认。

## 探测流程

1. **定位根目录**：用 `git rev-parse --show-toplevel` 解析工作区根（非 Git 仓库则使用当前工作目录）。
2. **初始化配置目录**：检查根目录下 `.agent-council/`，不存在则创建。
3. **初始化默认模型配置**：检查 `.agent-council/default-models.txt`，不存在则创建为空文件。
4. **读取默认模型清单**：格式为每行一个 Reviewer ID：`pi:provider/model` 或 `claude:model`。
5. **探测 Pi 可用模型**：执行 `pi --list-models`，获取本次 Pi 实时支持的模型清单。
6. **探测 Claude 可用模型**：在交互式终端启动 `claude` CLI，输入 `/model` 打开选择器，记录可选模型 ID 或别名后退出会话。
7. **统一展示并阻塞等待**：
   在同一条消息中完整展示以下 4 项信息，然后结束当前回合等待用户答复：
   - `默认 reviewer`：逐行列出配置内容（为空时显示“未配置”）；
   - `Pi model list`：`pi --list-models` 完整输出；
   - `Claude model list`：`/model` 探测结果；
   - 询问语句：
     - 若默认配置非空：“是否直接使用默认 reviewer？”
     - 若默认配置为空：“请提供至少两个 reviewer ID（例如 `pi:openai-codex/gpt-4o`、`claude:sonnet`）。”

## 回填与确认机制

- 用户确认使用默认名单时不追加 `--reviewer`；
- 用户指定或覆盖名单时，重复传入 `--reviewer` 参数；
- 至少两个 reviewer 成功跑通时，runner 会自动将实际成功的 reviewer 回填更新到 `.agent-council/default-models.txt`。
