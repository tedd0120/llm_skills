---
name: pan123-renamer
description: 123云盘媒体文件规范化重命名。当用户提到"123网盘/123云盘重命名"、"刮削失败改名"、"规范化媒体文件名"、"整理网盘剧集/电影命名"等场景时使用。扫描网盘视频文件，推断 Emby/Jellyfin 标准命名，用户确认后批量执行，支持回滚。
---

# 123云盘媒体文件规范化重命名

连接 123 云盘开放平台 API，扫描视频文件，由 Claude 推断规范命名并生成方案，用户确认后批量执行改名/移动，全程可回滚。

## 前置配置

项目根目录 `.env`（凭证在 https://www.123pan.com/developer 申请，免审核）：

```env
PAN123_CLIENT_ID=你的clientID
PAN123_CLIENT_SECRET=你的clientSecret
```

依赖：`pip install requests`

## 目标命名格式（Emby/Jellyfin 标准）

- 剧集/综艺：`剧名 (年份)/Season 01/剧名 (年份) S01E01.mkv`（综艺期数映射为集号）
- 电影：`片名 (年份)/片名 (年份).mkv`
- 字幕等附属文件与视频同名（保留 `.chs` 等语言后缀）

## 工作流程（Claude 按此执行）

脚本目录：`.claude/skills/pan123-renamer/scripts/`（cd 到此目录运行，输出在 `scripts/output/`）

1. **自测连接**：`python pan123_client.py` — 验证凭证，打印用户信息和根目录
2. **扫描**：`python scan.py`（全盘）或 `python scan.py --parent <fileId>`（试跑）→ `output/pan123_tree.json`
3. **推断命名**：Claude 读取 tree JSON（文件多时分目录读取，勿一次全部载入上下文）。对每个媒体目录推断：
   - 作品名：去掉【】标签、地区、画质、来源站等噪音
   - 年份：从目录名提取；不确定时用 WebSearch 核实（尤其综艺/剧集首播年份）
   - 类型与集号：从「01期」「第1集」「E01」「S01E01」等提取；单视频大文件通常是电影
   - 已符合规范的跳过，不生成条目
4. **出方案并确认**：生成 `output/rename_plan.json`：
   ```json
   {"rootId": 0, "entries": [{"fileId": 111, "oldParentId": 222,
     "oldPath": "/【韩综】豆豆笑笑2025（韩国）/01期.mp4",
     "newPath": "/豆豆笑笑 (2025)/Season 01/豆豆笑笑 (2025) S01E01.mp4"}]}
   ```
   - `oldParentId` 取自 tree JSON 的 `parentFileId`，**必须带上**（回滚依赖）
   - 向用户展示人类可读的对照表（按目录分组）；低置信度条目用 AskUserQuestion 逐条确认
5. **执行**：先 `python apply.py output/rename_plan.json --dry-run` 给用户过目，再去掉 --dry-run 实际执行。支持断点续跑（自动跳过 rollback_log 中已完成条目）
6. **回滚**（用户要求时）：`python rollback.py output/rollback_log.jsonl`

## 注意事项

- 开放平台接口 QPS 很低（1~5），client 已内置节流，大盘扫描会较慢，属正常
- 文件名非法字符 `" * : < > ? / \ |` 会被 apply 自动过滤
- 旧的空目录不自动删除，执行完提示用户手动清理
- 首次使用建议先选一个小目录 `--parent` 试跑完整流程再全盘执行
