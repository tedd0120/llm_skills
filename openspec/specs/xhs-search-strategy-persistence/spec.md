## 新增需求

### 需求: 搜索策略元数据必须保存到 raw.json
系统必须在生成 raw.json 时，将搜索策略元数据保存到顶层 `search_strategy` 字段。

#### 场景: 成功保存搜索策略
- **当** fetch_xhs.py 脚本接收到 `--search-strategy` 参数
- **那么** raw.json 必须包含 `search_strategy` 数组字段
- **并且** 每个策略对象必须包含 `keyword`、`posts_count`、`intent` 三个字段

#### 场景: 未提供搜索策略参数
- **当** fetch_xhs.py 脚本未接收到 `--search-strategy` 参数
- **那么** raw.json 的 `search_strategy` 字段必须设置为空数组 `[]`

### 需求: search_strategy 数据结构必须符合规范
`search_strategy` 数组中的每个对象必须包含完整的字段定义。

#### 场景: 验证字段完整性
- **当** 读取 raw.json 中的 `search_strategy` 字段
- **那么** 每个对象必须包含：
  - `keyword`: 字符串，搜索关键词
  - `posts_count`: 整数，分配的帖数
  - `intent`: 字符串，搜索意图描述

#### 场景: 验证数组顺序
- **当** 读取 raw.json 中的 `search_strategy` 数组
- **那么** 数组顺序必须与关键词分配顺序一致
