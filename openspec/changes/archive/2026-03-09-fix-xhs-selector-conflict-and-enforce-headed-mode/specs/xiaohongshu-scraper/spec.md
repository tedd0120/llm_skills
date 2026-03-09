# 小红书爬虫增量规范

## 目的

定义 xiaohongshu-scraper 在强制有头模式下的环境需求规范。

---

## 修改需求

### 需求:SKILL.md 必须在显著位置提示有头模式环境需求

xiaohongshu-scraper 的 SKILL.md 必须在"前置依赖配置"章节中明确强制提示有头模式的环境需求，删除 headless 降级说明。

#### 场景:环境需求提示

- **当** Agent 读取 SKILL.md 的前置依赖配置章节
- **那么** 必须看到明确的虚拟显示器配置要求
- **并且** 必须包含完整的 Xvfb 安装和启动命令
- **并且** 禁止出现 headless 降级相关的说明

#### 场景:删除 headless 降级说明

- **当** 更新 SKILL.md
- **那么** 必须删除类似"如无法安装 Xvfb，可降级使用 `--headless` 参数"的说明
- **并且** 必须强调有头模式是必须的环境要求

---

## 移除需求

### 需求: scraper 目录下的 fetch_xhs.py

**Reason**: scraper 作为编排层应调用 xiaohongshu-fetch 子 skill，不应保留冗余的 fetch_xhs.py。

**Migration**: 删除 `xiaohongshu-scraper/scripts/fetch_xhs.py`，所有抓取逻辑由 xiaohongshu-fetch 组件提供。

#### 场景:删除冗余文件

- **当** scraper 需要执行抓取
- **那么** 必须调用 xiaohongshu-fetch 子 skill
- **禁止** 直接执行 scraper 目录下的 fetch_xhs.py
