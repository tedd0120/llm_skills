---
name: pan123-renamer
description: 123云盘媒体文件规范化重命名。当用户提到"123网盘/123云盘重命名"、"刮削失败改名"、"规范化媒体文件名"、"整理网盘剧集/电影命名"等场景时使用。扫描网盘视频文件，推断 Emby/Jellyfin 标准命名，用户确认后批量执行，支持回滚。
---

# 123云盘媒体文件规范化重命名

连接 123 云盘开放平台 API，扫描视频文件，推断符合 Emby/Jellyfin 的规范命名方案，经用户确认后批量执行改名与目录移动，全程支持断点续跑与一键回滚。

## 前置配置

在项目根目录 `.env` 中配置凭证（可在 123 云盘开放平台申请）：

```env
PAN123_CLIENT_ID=你的clientID
PAN123_CLIENT_SECRET=你的clientSecret
```

依赖：`pip install requests`

## 目标命名规范

命名格式须遵循 Emby / Jellyfin 标准（详见 **[references/naming-standards.md](references/naming-standards.md)**）：
- 剧集与综艺：`剧名 (年份)/Season 01/剧名 (年份) S01E01.mkv`
- 电影：`片名 (年份)/片名 (年份).mkv`

---

## 工作流程

脚本目录：`.agents/skills/pan123-renamer/scripts/`（输出默认存放在 `output/`）。

1. **自测连接**：
   运行 `python pan123_client.py` 验证凭证连通性，打印用户信息与根目录状态。
2. **扫描文件树**：
   运行 `python scan.py`（全盘）或 `python scan.py --parent <fileId>`（子目录测试）生成 `output/pan123_tree.json`。
3. **推断规范命名**：
   读取 tree JSON。凡涉及作品名、年份、季号、集号等事实字段，**必须阅读 [references/media-verification.md](references/media-verification.md) 通过网络核验，严禁凭直觉推断**。
4. **生成方案并确认**：
   输出计划文件 `output/rename_plan.json`（包含 `rootId`、`entries` 与清空目录清单 `oldDirs`），向用户呈现分组对照表，低置信度条目主动向用户确认。
5. **执行改名**：
   先运行带 `--dry-run` 参数的演练命令供用户确认：
   ```bash
   python apply.py output/rename_plan.json --dry-run
   ```
   用户认可后去掉 `--dry-run` 实际执行。
6. **回滚操作**（用户要求时）：
   运行 `python rollback.py output/rollback_log.jsonl` 一键还原。

---

## 注意事项

- 接口 QPS 较低（1~5），客户端已内置自动限流节流，扫描大盘较慢属于正常现象。
- 文件名中非法字符 `" * : < > ? / \ |` 在执行时由脚本自动转义清理。
- 执行成功后，默认会将已清空的旧目录移入回收站（可随 rollback 还原）；可追加 `--keep-old-dirs` 保留空目录。
