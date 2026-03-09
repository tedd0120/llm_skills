# 小红书数据抓取规范

## 目的

定义小红书数据抓取组件的执行规范。此组件为内部组件，仅由 xiaohongshu-scraper 调用。

---

## 新增需求

### 需求: 禁止单独调用

fetch 组件必须标记为内部组件，禁止用户单独调用。

#### 场景: 内部组件标识

- **当** 编写 fetch 组件的 SKILL.md
- **那么** 必须在文档顶部添加警告标识，说明此组件仅由 scraper 内部调用
- **并且** 禁止在用户文档中提及如何单独调用

### 需求: 接收明确参数执行抓取

fetch 组件必须接收明确的参数并执行抓取，不进行澄清或用户交互。

#### 场景: 固定关键词模式

- **当** fetch 组件接收到固定关键词模式参数
- **那么** 必须接收 `--keywords`（逗号分隔的关键词列表）
- **并且** 必须接收 `--max-posts`（篇数上限）
- **并且** 必须接收 `--output`（输出文件路径）
- **并且** 必须接收 `--search-strategy`（搜索策略 JSON，可选）
- **并且** 必须执行抓取并输出到指定路径

#### 场景: 发散模式单轮抓取

- **当** fetch 组件接收到发散模式单轮参数
- **那么** 必须接收 `--keywords`（单个关键词）
- **并且** 必须接收 `--max-posts`（本轮配额）
- **并且** 必须接收 `--output`（输出文件路径，如 raw_round_N.json）
- **并且** 必须接收 `--seen-ids`（已见 ID 文件路径）
- **并且** 必须执行抓取并输出到指定路径

### 需求: 输出格式

fetch 组件必须输出标准格式的 JSON 文件。

#### 场景: 输出文件格式

- **当** fetch 组件完成抓取
- **那么** 必须输出 JSON 文件包含以下字段：
  - `search_time`: 执行时间
  - `keywords`: 搜索关键词列表
  - `posts`: 帖子数组（包含 title, content, author, date, likes, collects, comments_count, comments）
- **并且** 禁止包含 `url` 字段

#### 场景: 发散模式输出

- **当** fetch 组件执行发散模式单轮抓取
- **那么** 输出文件名必须为 `raw_round_N.json`（N 为轮次号）
- **并且** 文件格式与固定模式相同

### 需求: 跨轮去重支持

fetch 组件必须支持通过 seen-ids 文件实现跨调用去重。

#### 场景: 读取已有 ID

- **当** fetch 组件接收到 `--seen-ids` 参数
- **那么** 启动时必须读取文件中已有的 note_id 集合
- **并且** 搜索时必须跳过已见的 note_id

#### 场景: 追加新 ID

- **当** fetch 组件完成抓取
- **那么** 必须将本次新发现的 note_id 追加写入 seen-ids 文件
- **并且** 文件格式必须为每行一个 note_id（纯文本）

#### 场景: 文件不存在处理

- **当** seen-ids 文件不存在
- **那么** 必须自动创建该文件

---

## 新增需求 (来自 fix-xhs-selector-conflict-and-enforce-headed-mode)

### 需求: 选择器文件必须避免与 Python 标准库命名冲突

fetch 组件的选择器文件必须使用不与 Python 标准库冲突的命名。

#### 场景: 选择器文件命名

- **当** 编写选择器文件
- **那么** 文件名必须为 `xhs_selectors.py`
- **禁止** 使用 `selectors.py` 作为文件名

#### 场景: 导入选择器

- **当** Python 脚本需要导入选择器
- **那么** 必须使用 `from xhs_selectors import XHSSelectors as S`
- **禁止** 使用 `sys.path.insert(0, ...)` 操纵导入路径

### 需求: 必须强制有头模式

fetch 组件必须强制使用有头模式运行浏览器，在无 DISPLAY 环境变量时报错退出并提示虚拟显示器配置。

#### 场景: 检测到无 DISPLAY

- **当** 在非 Windows 环境下运行且 `DISPLAY` 环境变量未设置
- **那么** 必须输出错误信息：
  ```
  [✗] 检测到无 DISPLAY 环境变量
      请先启动虚拟显示器:
      Xvfb :99 -screen 0 1920x1080x24 &
      export DISPLAY=:99
  ```
- **并且** 必须以非零退出码退出
- **禁止** 自动降级到 headless 模式

#### 场景: 正常启动有头模式

- **当** 在 Windows 环境或 DISPLAY 环境变量已设置
- **那么** 必须使用有头模式启动浏览器
- **并且** 在 Windows 下使用 `channel="msedge"`

### 需求: 必须支持超链接功能

fetch 组件必须支持 `--hyperlinks` 参数，生成 `id_url_map.json` 文件。

#### 场景: 启用超链接功能

- **当** fetch 组件接收到 `--hyperlinks` 参数
- **那么** 输出的帖子数据必须包含 `post_id` 和 `url` 字段
- **并且** 必须在输出目录下生成 `id_url_map.json` 文件
- **并且** 文件内容必须为 `{post_id: url}` 的映射对象

#### 场景: 未启用超链接功能

- **当** fetch 组件未接收到 `--hyperlinks` 参数
- **那么** 输出的帖子数据禁止包含 `url` 字段
- **并且** 不生成 `id_url_map.json` 文件

---

## 移除需求 (来自 fix-xhs-selector-conflict-and-enforce-headed-mode)

### 需求: headless 自动降级逻辑

**Reason**: headless 模式下小红书登录难以成功，强制有头模式确保稳定性。

**Migration**: 在无 DISPLAY 环境变量时报错退出，提示用户启动虚拟显示器。

#### 场景: 旧行为（已移除）

- ~~当~~ 在非 Windows 环境下运行且 DISPLAY 环境变量未设置
- ~~那么~~ 自动设置 `headless=True` 并继续执行

---

## 新增需求 (来自 minimize-browser-window-on-windows)

### 需求: Windows 环境下浏览器必须最小化启动

fetch 组件在 Windows 环境下启动浏览器时，必须使用 `--start-minimized` 参数使窗口最小化。

#### 场景: Windows 环境启动

- **当** 在 Windows 环境下启动 Edge 浏览器
- **那么** 必须添加 `--start-minimized` 参数
- **并且** 窗口应以最小化状态启动

#### 场景: 非 Windows 环境启动

- **当** 在 Linux 或其他非 Windows 环境下启动浏览器
- **那么** 不添加 `--start-minimized` 参数
- **并且** 保持现有启动行为
