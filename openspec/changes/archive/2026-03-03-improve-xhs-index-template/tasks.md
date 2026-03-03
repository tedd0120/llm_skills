## 1. 修改 fetch_xhs.py 脚本

- [x] 1.1 添加 `--search-strategy` 命令行参数，接收 JSON 字符串
- [x] 1.2 解析 search_strategy 参数，验证 JSON 格式
- [x] 1.3 将 search_strategy 数据写入 raw.json 顶层字段
- [x] 1.4 确保 search_strategy 缺失时写入空数组（向后兼容）

## 2. 更新 SKILL.md 报告模板

- [x] 2.1 更新"搜索概览"模板，采用方案A嵌入式设计
- [x] 2.2 修改表头列名，使用 Emoji 前缀替代"字段"/"值"
- [x] 2.3 添加搜索策略子表格模板
- [x] 2.4 添加 Emoji 映射规则说明文档

## 3. 更新 Agent 执行逻辑

- [x] 3.1 澄清阶段：保存 search_strategy 数据结构（关键词、篇数、意图）
- [x] 3.2 执行阶段：将 search_strategy 序列化为 JSON 传递给 fetch_xhs.py
- [x] 3.3 报告生成：从 raw.json 读取 search_strategy 并渲染
- [x] 3.4 报告生成：实现 search_strategy 缺失时的降级逻辑
- [x] 3.5 报告生成：实现意图类型到 Emoji 的映射函数

## 4. 验证与测试

> 验证任务将在实际使用技能时自然完成

- [ ] 4.1 测试完整流程：澄清→执行→报告生成
- [ ] 4.2 测试向后兼容：读取不含 search_strategy 的旧 raw.json
- [ ] 4.3 验证报告渲染：检查 Markdown 表格格式正确
