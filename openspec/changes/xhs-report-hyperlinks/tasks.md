## 1. 数据抓取层修改

- [x] 1.1 修改 `fetch_xhs.py` 的 `_extract_post` 方法，提取并保存帖子 URL
- [x] 1.2 在 `fetch_xhs.py` 中实现帖子 ID 提取逻辑（从 URL path 中提取）
- [x] 1.3 修改 `fetch_xhs.py` 返回的字典，添加 `post_id` 字段
- [x] 1.4 在 `fetch_xhs.py` 中实现 `id_url_map.json` 文件生成逻辑（仅在超链接启用时）
- [x] 1.5 添加 `--hyperlinks` 参数到 `fetch_xhs.py` CLI 接口

## 2. Scraper 编排层修改

- [x] 2.1 修改 `xiaohongshu-scraper/SKILL.md`，在澄清阶段新增超链接格式选择步骤
- [x] 2.2 更新 `xiaohongshu-scraper/SKILL.md` 执行流程，传递 `hyperlinks` 配置到 fetch 阶段
- [x] 2.3 更新 `xiaohongshu-scraper/SKILL.md`，传递 `hyperlinks` 配置到 summarize 和 formatter 阶段

## 3. 报告生成层修改

- [x] 3.1 修改 `xiaohongshu-summarize/SKILL.md` 报告模板，定义超链接启用时的引用格式
- [x] 3.2 更新 `xiaohongshu-summarize/SKILL.md` 引用格式规范表格
- [x] 3.3 在 `xiaohongshu-summarize/SKILL.md` 中添加向后兼容说明（无 post_id 时降级）

## 4. 格式化层修改

- [x] 4.1 修改 `xiaohongshu-formatter/SKILL.md`，添加 URL 替换逻辑说明
- [x] 4.2 在 `xiaohongshu-formatter/SKILL.md` 中定义 ID 占位符到 URL 的替换规则
- [x] 4.3 添加 `id_url_map.json` 文件不存在时的处理逻辑

## 5. 测试验证

- [ ] 5.1 测试超链接禁用（默认）流程，确认报告为纯文本格式
- [ ] 5.2 测试超链接启用流程，确认报告包含可点击超链接
- [ ] 5.3 测试向后兼容性，使用旧 raw.json 确认降级处理正常
- [ ] 5.4 验证 `id_url_map.json` 文件生成和读取
