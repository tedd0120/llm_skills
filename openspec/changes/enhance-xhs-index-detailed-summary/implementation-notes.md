# Implementation Notes

## 本次验收动作

- 更新正式规范：`openspec/specs/xhs-output-enforcement/spec.md`
- 更新技能说明：`.agent/skills/xiaohongshu-scraper/SKILL.md`
- 更新项目说明：`README.md`

## 干跑验收（任务 3.1）

执行命令：
`python .agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py --keywords "扫地机器人 推荐" --max-posts 2 --output "data/tmp_xhs_dryrun_20260227.json" --headless`

结果：成功抓取 2 篇帖子并输出 JSON。

## 抽查验收（任务 3.2）

基于干跑数据生成验收目录：
`data/xiaohongshu/扫地机器人推荐_20260227_implementation_dryrun/`

抽查结果：
- `_index.md` 包含单篇结构化字段（核心结论、关键证据、评论区共识/分歧、适用边界、可执行启示）
- `_index.md` 包含跨帖字段（共识结论、主要分歧、分人群/场景建议、风险与信息缺口）
- 本地链接校验通过（无缺失文件）
- 未出现“一句简短判语”式输出

## 后续默认标准

后续小红书任务默认按“深度汇总报告”输出 `_index.md`，不再接受“导航+一句话”或“纯榜单无依据”作为最终交付。
