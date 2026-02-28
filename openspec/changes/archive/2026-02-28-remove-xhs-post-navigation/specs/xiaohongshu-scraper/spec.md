## 新增需求

### 需求: 抓取数据必须不包含 URL 字段
`fetch_xhs.py` 脚本输出的 JSON 数据必须不包含 `url` 字段，只保留标题、内容、作者、日期、点赞数、收藏数、评论数和评论列表。

#### 场景: 数据抓取
- **当** 脚本抓取小红书帖子数据
- **那么** 输出的 JSON 必须包含 8 个字段：title, content, author, date, likes, collects, comments_count, comments
- **并且** 禁止包含 url 字段

#### 场景: 数据兼容性
- **当** 读取已有的 raw.json 数据
- **那么** Agent 应当正常处理，不依赖 url 字段的存在
