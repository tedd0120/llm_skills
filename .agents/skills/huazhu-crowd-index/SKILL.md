---
name: huazhu-crowd-index
description: 基于携程上「汉庭」酒店在特定节假日 vs 节后平日的价格涨幅，判断各城市该日人流量高低并排名。每城锚定一家汉庭（华住最基础、每城必有的系列）做横向对比。用户提到"汉庭/华住酒店价格""哪个城市人多""节假日人流量""涨价倍数""酒店价格判断城市热度"等场景时使用此 skill。
---

# 汉庭人流量指数 Skill

用**「汉庭」酒店价格的节假日涨幅**反推**城市人流量**。核心直觉：同一家汉庭，节假日卖 1000、平日卖 100，涨价 10 倍 → 该城节假日人多。

**为何锚定汉庭**：汉庭是华住会最基础的系列，**每个城市必有**，定位、房型、价位最一致，跨城横向对比最公平。故每城只取**欢迎度最高的一家汉庭**，比较它在「节假日」与「节后平日」的价差。

**数据源**：携程（按城市+日期搜索，价格为该汉庭当日最低可订价）。

**内部架构**（`scripts/` 目录）：
- `login_ctrip.py` —— 检查/建立携程登录态，复用 `ctrip_auth.json`
- `fetch_prices.py` —— 核心抓取：逐城市抓一家汉庭在「目标日」与「平日基准日」的价格，输出 `raw.json`
- `compute_index.py` —— 读 `raw.json`，算每城汉庭涨价倍数并排名，生成 Markdown 报告
- `ctrip_selectors.py` —— 集中选择器（2026-06-05 真机实测）
- `hot_cities.py` —— 内置热门城市清单 + cityId 种子表 + 汉庭/华住识别
- `_calibrate_card.py` —— 选择器校准工具（维护用，携程改版抓不到数据时重新核对）

**抓取原理**（实测）：
1. **定位城市**：列表页由 URL 直达，仅需 `cityId`+`checkin`/`checkout`（无需操作日历）。cityId 命中 `hot_cities.CITY_IDS` 种子表则直接用，否则首页搜索动态解析并缓存。
2. **筛汉庭**：在列表页顶部「位置/品牌/酒店」框输入「汉庭」→搜索，得到**仅含汉庭、按欢迎度排序**的列表。
   （实测：冷链接直接带 `searchWord` 不生效，必须经此 UI 交互建立过滤状态。该框需 **≥1920 宽视口**才渲染，故脚本用 1920×1080。）
3. **取锚定汉庭**：扫描酒店名 `span.hotelName`，取**第一家有报价的汉庭**（最热门那家；若它节日售罄/无报价则顺延，并记 `flagship_sold_out`）。卡片 `.right-card`、价格 `.sale`。
4. **基准日同店对比**：在同一过滤标签页内，把过滤 URL 的日期换成基准日（保持汉庭过滤），按**同名**取该汉庭平日价。
得到同一家汉庭两日价格 → 涨价倍数。

---

## 两阶段执行流程

### 阶段一：澄清阶段（必须执行，逐轮交互，每轮只问一个问题）

**[核心要求]**：澄清阶段每次输出只能包含一个问题，必须等用户回复后再问下一个，禁止合并。

**第 1 轮：目标日期**
```markdown
要分析哪一天的人流量？请给出入住日期（YYYY-MM-DD，如端午 2026-06-19）。
```

**第 2 轮：城市清单**
```markdown
对比哪些城市？
- 直接回车 / 回复「默认」→ 使用内置热门城市（北京、上海、广州、深圳、杭州、成都、西安、重庆、南京、武汉、苏州、长沙、厦门、青岛、三亚、丽江）
- 或自定义，逗号分隔，如「北京,上海,杭州,西安」
```

**第 3 轮：速度模式**
```markdown
选择速度模式：

| 选项 | 模式 | 说明 |
|:----:|:-----|:-----|
| S | 安全模式 | 延迟增大 2.5-3x + 随机停顿，最大限度规避携程风控 |
| N | 正常模式（默认） | 内置随机延时，平衡速度与安全 |
| Y | 极速模式 | 去除所有延时，快但易触发风控 |

回复 S / N / Y（默认 N）。城市多时建议 S。
```

确认完毕后进入执行阶段。

### 阶段二：执行阶段

**步骤 1 — 登录检查**
```bash
python login_ctrip.py --check-only
```
- 输出 `LOGIN_OK` → 已登录，继续。
- 输出 `NEED_LOGIN` → 运行 `python login_ctrip.py`，提示用户在弹出的浏览器中**点击右上角「登录」并扫码/手机号登录**；登录成功后页面会自动跳回携程首页，脚本检测到后保存 cookie 并输出 `LOGIN_SUCCESS`。
- 登录判定依据：首页「登录」按钮（class 含 `home_header_login_not`）消失且 URL 已跳回携程站内（非 passport 登录页），连续两次确认避免误判。

**步骤 2 — 抓取**
```bash
python fetch_prices.py --cities "<城市,逗号分隔或留空>" --target-date <YYYY-MM-DD> [--safe-mode|--speed-mode]
```
- `--baseline-date` 留空时脚本**自动取「节后第一个非节假日的周二」**（如端午 6/19 → 6/23）。
- 每城自动锚定欢迎度最高、且节日当天有报价的一家汉庭，基准日抓同一家。
- 卡片/价格读不到时，加 `--debug`：每城落 `ctrip_debug_*.png` 截图；再用 `_calibrate_card.py` 重新核对并更新 `ctrip_selectors.py`。
- 输出 `data/huazhu/<时间戳>/raw.json`（脚本结尾打印实际路径，记下它）。

**步骤 3 — 计算与报告**
```bash
python compute_index.py --input <上一步的 raw.json 路径>
```
- 生成同目录 `report.md` 并打印到 stdout。
- 将城市排名表呈现给用户，并点出 Top 城市（涨价倍数越高 = 人流越旺；备注里「首选汉庭节日售罄」也是强需求信号）。

---

## 参数说明（fetch_prices.py）

| 参数 | 默认 | 说明 |
|:-----|:----:|:-----|
| `--target-date` | 必填 | 目标入住日期 YYYY-MM-DD |
| `--cities` | 内置热门城市 | 逗号分隔城市；留空用 `hot_cities.HOT_CITIES` |
| `--baseline-date` | 自动 | 平日基准日；留空自动取「节后第一个非节假周二」 |
| `--output` | 自动 | raw.json 路径；留空按时间戳生成 |
| `--safe-mode` / `--speed-mode` | 正常 | 三档速度 |
| `--debug` | 关 | 每城落调试截图 |

## raw.json 结构（每城 hotels 仅 1 条 = 锚定的那家汉庭）

```json
{
  "fetch_time": "2026-06-05 16:00:00",
  "target_date": "2026-06-19",
  "baseline_date": "2026-06-23",
  "cities": [
    {
      "city": "杭州",
      "city_id": 17,
      "hotels": [
        {
          "name": "汉庭酒店(杭州西湖店)", "brand": "汉庭", "room_type": "大床房",
          "target_price": 419, "baseline_price": 259,
          "sold_out": false, "flagship_sold_out": false, "url": ""
        }
      ]
    }
  ]
}
```

## 指标口径

- **涨价倍数（城市）** = 该城锚定汉庭「节假日最低价 ÷ 节后平日最低价」。
- **排名**：按涨价倍数降序，倍数越高 = 节假日溢价越猛 = 人流越旺。
- **`flagship_sold_out`**：欢迎度最高的汉庭节日当天售罄/无报价、已顺延到下一家——该标记本身是强需求信号，报告备注里体现。
- **基准日**：节后第一个非节假日的周二，代表需求回落后的常态价。

---

## 前置依赖

```bash
cd .claude/skills/huazhu-crowd-index/scripts
pip install -r requirements.txt
playwright install
```
- 无强制环境变量；Cookie 固定保存在 `scripts/ctrip_auth.json`（已被 `.gitignore` 忽略）。
- Windows 强制使用 Edge（`channel="msedge"`）降低指纹风险；Linux/无头需先启动 Xvfb 虚拟显示器。

## 常见限制与故障排除

- **读不到酒店卡片 / 价格为空**：携程改版导致 `span.hotelName` / `.right-card` / `.sale` 失效。加 `--debug` 跑单城看截图，再用 `python _calibrate_card.py <cityId> <checkin> <checkout>` 重新核对，更新 `ctrip_selectors.py` 的 `HOTEL_NAME/HOTEL_CARD/HOTEL_PRICE`。
- **品牌搜索失败 / 未找到汉庭**：品牌框需 **≥1920 宽视口**才渲染（脚本已设 1920×1080，勿改窄）。框选择器 `ctrip_selectors.BRAND_INPUT`；若携程改版，用 `--debug` 看截图并更新。汉庭识别在 `hot_cities.is_hanting`。
- **基准价为 null**：基准页（同一标签页换日期）未找到同名汉庭（排序靠后未加载）。脚本已滚动更深（16 屏）并按汉庭名定向抓取；仍缺则该汉庭在基准日可能无房，换一天基准或人工核对。
- **cityId 解析失败**：自定义城市不在 `CITY_IDS` 种子表时走 UI 动态解析；若失败，手动在 `hot_cities.CITY_IDS` 补该城 cityId（从携程搜索结果 URL 的 `cityId=` 读取）。
- **触发风控/验证码**：改用 `--safe-mode` 或分批跑城市。
- **登录后浏览器自动关闭**：属正常——脚本检测到已登录即保存 cookie 退出。若误判，确认是否真的跳回了携程首页。
- **基准日不理想**（恰逢另一节假日）：用 `--baseline-date` 手动指定一个普通工作日。
- **单城冒烟测试**：`python fetch_prices.py --cities 杭州 --target-date 2026-06-19 --debug`
