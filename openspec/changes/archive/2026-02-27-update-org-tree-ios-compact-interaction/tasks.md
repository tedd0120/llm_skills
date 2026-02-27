## 1. 实施
- [x] 1.1 调整组织树布局参数（节点宽高、层级横纵间距、根节点间距），使默认视图更紧凑
- [x] 1.2 新增节点悬停 1 秒提示框，展示祖先链“姓名-部门”列表
- [x] 1.3 修正拖动与文本选择冲突：节点文本可框选，文本选择期间不触发画布平移
- [x] 1.4 更新页面样式为 iOS 极简风格（字体栈、配色、留白、阴影）

## 2. 文档
- [x] 2.1 更新 `.agent/skills/teams-group-members/SKILL.md`，补充新交互（悬停链路、文本可选）与风格说明

## 3. 验证
- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
- [x] 3.2 冒烟验证：运行抓取命令并确认 HTML 可生成且包含祖先提示容器与 iOS 字体声明
- [x] 3.3 OpenSpec 校验：`openspec-cn validate update-org-tree-ios-compact-interaction --strict`
