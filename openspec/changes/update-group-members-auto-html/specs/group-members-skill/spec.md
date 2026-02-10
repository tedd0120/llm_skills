# 功能：group-members-skill

## 修改需求
### 需求：CLI 入口支持

脚本**必须**可通过命令行直接运行，**必须**支持 `--group` 参数指定群组代码，并在每次抓取后默认生成最新组织树 HTML。

#### 场景：命令行单群调用
- 运行 `python fetch_group_members.py --group <group_code>`
- 系统**必须**输出格式化成员列表到控制台
- 系统**必须**基于本次抓取结果生成 HTML

#### 场景：命令行批量调用
- 运行 `python fetch_group_members.py`（未传 `--group`，从 `TEAMS_GROUP_CODES` 批量抓取）
- 系统**必须**对并集去重后的最终结果生成 HTML
- 系统**禁止**在批量流程中为每个中间单群结果重复生成 HTML

## 新增需求
### 需求：HTML 输出路径默认规则

抓取流程生成 HTML 时，系统**必须**遵循统一默认规则确定输出路径。

#### 场景：提供 JSON 输出路径
- 当调用方提供 `save_path` 或 CLI `--output`
- 系统**必须**以该文件名主干追加 `_org_tree.html` 生成 HTML 文件

#### 场景：未提供 JSON 输出路径
- 当调用方未提供 `save_path` 且 CLI 未提供 `--output`
- 系统**必须**写入默认路径 `data/latest_group_members_org_tree.html`
