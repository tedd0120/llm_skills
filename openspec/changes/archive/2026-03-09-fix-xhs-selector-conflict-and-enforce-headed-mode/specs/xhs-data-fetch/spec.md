# 小红书数据抓取增量规范

## 目的

定义 xiaohongshu-fetch 组件的选择器命名规范、强制有头模式和超链接功能。

---

## 新增需求

### 需求:选择器文件必须避免与 Python 标准库命名冲突

fetch 组件的选择器文件必须使用不与 Python 标准库冲突的命名。

#### 场景:选择器文件命名

- **当** 编写选择器文件
- **那么** 文件名必须为 `xhs_selectors.py`
- **禁止** 使用 `selectors.py` 作为文件名

#### 场景:导入选择器

- **当** Python 脚本需要导入选择器
- **那么** 必须使用 `from xhs_selectors import XHSSelectors as S`
- **禁止** 使用 `sys.path.insert(0, ...)` 操纵导入路径

### 需求:必须强制有头模式

fetch 组件必须强制使用有头模式运行浏览器，在无 DISPLAY 环境变量时报错退出并提示虚拟显示器配置。

#### 场景:检测到无 DISPLAY

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

#### 场景:正常启动有头模式

- **当** 在 Windows 环境或 DISPLAY 环境变量已设置
- **那么** 必须使用有头模式启动浏览器
- **并且** 在 Windows 下使用 `channel="msedge"`

### 需求:必须支持超链接功能

fetch 组件必须支持 `--hyperlinks` 参数，生成 `id_url_map.json` 文件。

#### 场景:启用超链接功能

- **当** fetch 组件接收到 `--hyperlinks` 参数
- **那么** 输出的帖子数据必须包含 `post_id` 和 `url` 字段
- **并且** 必须在输出目录下生成 `id_url_map.json` 文件
- **并且** 文件内容必须为 `{post_id: url}` 的映射对象

#### 场景:未启用超链接功能

- **当** fetch 组件未接收到 `--hyperlinks` 参数
- **那么** 输出的帖子数据禁止包含 `url` 字段
- **并且** 不生成 `id_url_map.json` 文件

---

## 移除需求

### 需求:headless 自动降级逻辑

**Reason**: headless 模式下小红书登录难以成功，强制有头模式确保稳定性。

**Migration**: 在无 DISPLAY 环境变量时报错退出，提示用户启动虚拟显示器。

#### 场景:旧行为（已移除）

- ~~当~~ 在非 Windows 环境下运行且 DISPLAY 环境变量未设置
- ~~那么~~ 自动设置 `headless=True` 并继续执行
