## 1. 重命名选择器文件

- [x] 1.1 将 `xiaohongshu-scraper/scripts/selectors.py` 重命名为 `xhs_selectors.py`
- [x] 1.2 将 `xiaohongshu-fetch/scripts/selectors.py` 重命名为 `xhs_selectors.py`
- [x] 1.3 更新 `xiaohongshu-scraper/scripts/login_xhs.py` 的 import 语句
- [x] 1.4 删除 `xiaohongshu-scraper/scripts/__pycache__/selectors.*` 缓存文件
- [x] 1.5 删除 `xiaohongshu-fetch/scripts/__pycache__/selectors.*` 缓存文件

## 2. 强制有头模式

- [x] 2.1 修改 `xiaohongshu-fetch/scripts/fetch_xhs.py`：移除 headless 自动降级逻辑，无 DISPLAY 时报错退出
- [x] 2.2 修改 `xiaohongshu-scraper/scripts/login_xhs.py`：移除 headless 自动降级逻辑，无 DISPLAY 时报错退出

## 3. 合并 hyperlinks 功能

- [x] 3.1 将 `--hyperlinks` 参数添加到 `xiaohongshu-fetch/scripts/fetch_xhs.py`
- [x] 3.2 将 `id_url_map.json` 生成逻辑合并到 `xiaohongshu-fetch/scripts/fetch_xhs.py`
- [x] 3.3 确保启用 hyperlinks 时输出包含 `post_id` 和 `url` 字段

## 4. 删除冗余文件

- [x] 4.1 删除 `xiaohongshu-scraper/scripts/fetch_xhs.py`
- [x] 4.2 删除 `xiaohongshu-scraper/scripts/__pycache__/fetch_xhs.*` 缓存文件

## 5. 更新 SKILL.md

- [x] 5.1 删除 `xiaohongshu-scraper/SKILL.md` 中的 headless 降级说明
- [x] 5.2 在显著位置添加强制有头模式的环境需求提示
- [x] 5.3 更新虚拟显示器配置说明为强制要求
