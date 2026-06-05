"""
华住人流量指数 - 核心抓取脚本

对每个城市：
  1. 解析 cityId（命中 hot_cities.CITY_IDS 种子表则直接用，否则 UI 动态解析并缓存）
  2. 直接拼「列表页 URL」(cityId + 入住/退房日期) 导航 —— 无需操作日历（实测稳定）
  3. 解析列表卡片 .right-card：酒店名 span.hotelName + 最低价 .sale + 售罄文案
  4. 对「目标日」与「平日基准日」各抓一次，按酒店名对齐，得到涨价倍数所需的两个价格
最终输出 raw.json（结构见 SKILL.md）。

抓取范式复用 xiaohongshu-fetch：Playwright + stealth + Windows 强制 msedge + cookie 复用 + 三档延时。
选择器实测核对：2026-06-05（见 ctrip_selectors.py）。
"""

import argparse
import io
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import Stealth

from ctrip_selectors import CtripSelectors as S
from hot_cities import parse_cities, is_hanting, CITY_IDS

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.resolve()
AUTH_STATE_PATH = (SCRIPT_DIR / "ctrip_auth.json").resolve()

# 2026 年中国法定节假日（含调休休息日，近似；用于基准日避让，可按需增补）
HOLIDAYS_2026 = {
    "2026-01-01",
    "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",
    "2026-02-20", "2026-02-21", "2026-02-22", "2026-02-23",  # 春节
    "2026-04-04", "2026-04-05", "2026-04-06",  # 清明
    "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",  # 劳动
    "2026-06-19", "2026-06-20", "2026-06-21",  # 端午
    "2026-09-25", "2026-09-26", "2026-09-27",  # 中秋
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04",
    "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08",  # 国庆
}


def compute_baseline_date(target: str, holidays: set = HOLIDAYS_2026) -> str:
    """基准日 = 节假日后第一个非节假日的周二（如端午 6/19 → 6/23）。"""
    t = datetime.strptime(target, "%Y-%m-%d").date()
    d = t + timedelta(days=1)
    for _ in range(60):  # 安全上限
        if d.weekday() == 1 and d.isoformat() not in holidays:  # 周一=0，周二=1
            return d.isoformat()
        d += timedelta(days=1)
    return (t + timedelta(days=7)).isoformat()


class CtripFetcher:
    def __init__(self, safe_mode=False, speed_mode=False, debug=False):
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            print("[✗] 检测到无 DISPLAY 环境变量，请先启动 Xvfb 虚拟显示器", file=sys.stderr, flush=True)
            sys.exit(1)
        self.safe_mode = safe_mode
        self.speed_mode = speed_mode
        self.debug = debug
        self.auth_state_path = AUTH_STATE_PATH
        self.city_id_cache = dict(CITY_IDS)  # 种子表 + 运行期动态解析
        if speed_mode:
            print("[⚡] 极速模式 — 已去除所有延时", flush=True)
        elif safe_mode:
            print("[🛡️] 安全模式 — 延迟增大，模拟人类节奏", flush=True)

    # ---------------- 三档延时 ----------------
    def _sleep(self, lo=2.0, hi=5.0):
        if self.speed_mode:
            return
        if self.safe_mode:
            lo, hi = lo * 2.5, hi * 2.5 + random.uniform(0, 2)
            time.sleep(random.uniform(lo, hi))
            if random.random() < 0.10:
                pause = random.uniform(5, 15)
                print(f"    [safe-mode] reading pause {pause:.1f}s", flush=True)
                time.sleep(pause)
        else:
            time.sleep(random.uniform(lo, hi))

    @staticmethod
    def _parse_price(text: str):
        if not text:
            return None
        m = re.search(r"(\d[\d,]*)", text.replace("￥", "").replace("¥", ""))
        if not m:
            return None
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None

    # ---------------- cityId 解析 ----------------
    def _resolve_city_id(self, page: Page, city: str):
        if city in self.city_id_cache and self.city_id_cache[city]:
            return self.city_id_cache[city]
        print(f"    [*] 动态解析 cityId: {city}", flush=True)
        try:
            page.goto(S.HOME_URL, wait_until="domcontentloaded")
            self._sleep(1.5, 3.0)
            dest = page.locator(S.DESTINATION_INPUT).first
            dest.click()
            dest.fill("")
            dest.type(city, delay=random.randint(60, 130))
            self._sleep(1.2, 2.2)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

            btn = None
            for sel in S.SEARCH_BUTTON:
                loc = page.locator(sel)
                if loc.count() > 0:
                    btn = loc.first
                    break
            url = ""
            if btn:
                try:
                    with page.context.expect_page(timeout=8000) as pinfo:
                        btn.click()
                    newp = pinfo.value
                    newp.wait_for_load_state("domcontentloaded")
                    newp.wait_for_timeout(1500)
                    url = newp.url
                    newp.close()
                except Exception:
                    page.wait_for_timeout(2000)
                    url = page.url
            m = re.search(r"cityId=(\d+)", url)
            cid = int(m.group(1)) if m else None
            self.city_id_cache[city] = cid
            return cid
        except Exception as e:
            print(f"    [!] {city} cityId 解析失败: {e}", flush=True)
            return None

    @staticmethod
    def _build_list_url(city_id, checkin: str) -> str:
        checkout = (datetime.strptime(checkin, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        return S.LIST_URL_TEMPLATE.format(city_id=city_id, checkin=checkin, checkout=checkout)

    @staticmethod
    def _swap_dates(url: str, from_date: str, to_date: str) -> str:
        """把过滤列表 URL 里的入住/退房日期从 from_date 段换成 to_date 段（保持品牌过滤）。"""
        f_co = (datetime.strptime(from_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        t_co = (datetime.strptime(to_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        return url.replace(from_date, to_date).replace(f_co, t_co)

    # ---------------- 列表页搜索框筛选「汉庭」 ----------------
    def _brand_search(self, page: Page, keyword: str = "汉庭"):
        """
        在已加载的列表页顶部「位置/品牌/酒店」框输入 keyword 并搜索，得到该品牌过滤后的列表。
        （实测：携程冷链接直接带 searchWord 不生效，必须经此 UI 交互建立过滤状态；
         之后在同一标签页内换日期 goto 仍保持过滤——基准日据此复用。）
        点「搜索」通常开新标签，返回过滤后的 page（可能是新标签）；失败返回 None。
        """
        box = page.locator(S.BRAND_INPUT)
        if box.count() == 0:
            print("    [!] 未找到品牌搜索框（需 1920 宽视口）", flush=True)
            return None
        box = box.first
        try:
            box.click()
            box.fill("")
            box.type(keyword, delay=random.randint(60, 130))
            page.wait_for_timeout(2500)
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
        except Exception as e:
            print(f"    [!] 品牌框输入失败: {e}", flush=True)
            return None

        target_page = page
        btn = None
        for sel in S.SEARCH_BUTTON:
            loc = page.locator(sel)
            if loc.count() > 0:
                btn = loc.first
                break
        if btn is not None:
            try:
                with page.context.expect_page(timeout=8000) as pinfo:
                    btn.click()
                newp = pinfo.value
                newp.wait_for_load_state("domcontentloaded")
                newp.wait_for_timeout(5000)
                Stealth().apply_stealth_sync(newp)
                target_page = newp
            except Exception:
                page.wait_for_timeout(5000)
        else:
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

        url = target_page.url or ""
        if "/hotels/list" in url and "searchWord" in url:
            return target_page
        print(f"    [!] 品牌搜索后未进入过滤列表，url={url[:80]}", flush=True)
        return None if target_page is page else (target_page.close() or None)

    # ---------------- 扫描列表页（不负责导航）----------------
    def _scan_hanting(self, page: Page, city: str, label: str, want_names: set = None) -> dict:
        """
        在**当前已是汉庭过滤**的列表页上扫描，返回有序 { 酒店名: {...} }。
        携程列表默认「欢迎度排序」，dict 插入序即欢迎度序，首个 key = 最热门汉庭。
        - want_names=None（目标页）：按欢迎度顺序收集，直到第一家「有报价」的汉庭即停。
        - want_names 给定（基准页）：只收指定酒店，滚动更深直到找到。
        """
        result = {}
        page.wait_for_timeout(4000)
        self._sleep(1.0, 2.0)

        max_scrolls = 16 if want_names else 12

        def has_priced():
            return any((not h.get("sold_out")) and h.get("price") for h in result.values())

        def done():
            if want_names is not None:
                return want_names.issubset(set(result.keys()))
            return has_priced()  # 目标页：拿到第一家有报价的汉庭即可

        # 滚动 + 扫描交替进行，边加载边收集
        scanned = 0
        last_seen = 0
        for _ in range(max_scrolls):
            names = page.locator(S.HOTEL_NAME)
            total = names.count()
            for i in range(last_seen, total):
                if done():
                    break
                nm = names.nth(i)
                try:
                    name = (nm.text_content() or "").strip()
                except Exception:
                    continue
                if not name:
                    continue
                scanned += 1
                if not is_hanting(name) or name in result:
                    continue
                if want_names is not None and name not in want_names:
                    continue
                self._collect_hotel(nm, name, "汉庭", result)
            last_seen = total
            if done():
                break
            try:
                page.mouse.wheel(0, 2200)
            except Exception:
                pass
            self._sleep(0.8, 1.6)

        self._debug_shot(page, f"{city}_{label}")
        if scanned == 0:
            print(f"    [!] {city}/{label}: 未读到酒店名（选择器需校准），url={page.url[:90]}", flush=True)
        print(f"    [✓] {city}/{label}: 扫描 {scanned} 家，命中汉庭 {len(result)} 家", flush=True)
        return result

    @staticmethod
    def _pick_hanting(target: dict):
        """
        从目标页有序汉庭 dict 中选「欢迎度最高且有报价」的一家。
        返回 (name, info, flagship_sold_out)：
          flagship_sold_out = 被选中的不是排序最靠前的那家（即首选汉庭节日售罄/无报价被跳过）。
        若无任何有报价汉庭，返回 (None, None, False)。
        """
        first_key = next(iter(target), None)
        for name, info in target.items():
            if (not info.get("sold_out")) and info.get("price"):
                return name, info, (name != first_key)
        return None, None, False

    def _collect_hotel(self, nm, name: str, brand: str, result: dict):
        """从酒店名 locator 出发，解析所在卡片的价格/房型/售罄，写入 result。"""
        # 定位所在卡片
        card = nm.locator(S.CARD_FROM_NAME_XPATH)
        if card.count() == 0:
            card = nm.locator(S.CARD_FROM_NAME_XPATH_FALLBACK)
        card_text = ""
        if card.count():
            try:
                card_text = card.first.text_content() or ""
            except Exception:
                pass

        sold_out = any(t in card_text for t in S.SOLD_OUT_TEXTS)
        price = None
        if not sold_out and card.count():
            sale = card.first.locator(S.HOTEL_PRICE)
            if sale.count():
                price = self._parse_price(sale.first.text_content())
            if price is None:
                price = self._parse_price(card_text)

        room_type = ""
        if card.count():
            rt = card.first.locator(S.ROOM_TYPE)
            if rt.count():
                try:
                    room_type = (rt.first.text_content() or "").strip()
                except Exception:
                    pass

        hotel_url = ""
        try:
            a = nm.locator("xpath=ancestor::a[1]")
            if a.count():
                href = a.first.get_attribute("href") or ""
                hotel_url = ("https:" + href) if href.startswith("//") else href
        except Exception:
            pass

        result[name] = {
            "brand": brand,
            "price": price,
            "room_type": room_type,
            "sold_out": sold_out,
            "url": hotel_url,
        }

    def _debug_shot(self, page: Page, label: str):
        if not self.debug:
            return
        try:
            path = SCRIPT_DIR / f"ctrip_debug_{label}_{int(time.time())}.png"
            page.screenshot(path=str(path))
            print(f"    [DEBUG] 截图: {path}", flush=True)
        except Exception:
            pass

    # ---------------- 入口 ----------------
    def run(self, cities: list, target_date: str, baseline_date: str, output_file: str):
        out = {
            "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_date": target_date,
            "baseline_date": baseline_date,
            "cities": [],
        }

        with sync_playwright() as pw:
            launch_kw = {"headless": False}
            if sys.platform == "win32":
                launch_kw["channel"] = "msedge"
            browser = pw.chromium.launch(**launch_kw)

            ctx_kw = {
                # 1920 宽确保列表页顶部「位置/品牌/酒店」搜索框渲染出来（窄屏会折叠）
                "viewport": {"width": 1920, "height": 1080},
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
            }
            ctx = None
            if self.auth_state_path.exists():
                try:
                    ctx = browser.new_context(storage_state=str(self.auth_state_path), **ctx_kw)
                    print(f"[*] Cookie 已加载: {self.auth_state_path}", flush=True)
                except Exception as e:
                    print(f"[!] Cookie 加载失败: {e}", flush=True)
            if ctx is None:
                print("[!] 未加载 Cookie（建议先运行 login_ctrip.py）", flush=True)
                ctx = browser.new_context(**ctx_kw)

            page = ctx.new_page()
            Stealth().apply_stealth_sync(page)

            try:
                for city in cities:
                    print(f"\n[*] 城市: {city}", flush=True)
                    try:
                        city_id = self._resolve_city_id(page, city)
                        if not city_id:
                            print(f"[!] {city}: 无法解析 cityId，跳过", flush=True)
                            out["cities"].append({"city": city, "city_id": None, "hotels": []})
                            self._save(out, output_file)
                            continue

                        # 目标日：进基础列表页 → 品牌框搜「汉庭」→ 得到汉庭过滤列表
                        page.goto(self._build_list_url(city_id, target_date),
                                  wait_until="domcontentloaded")
                        page.wait_for_timeout(5000)
                        fp = self._brand_search(page, "汉庭")
                        if fp is None:
                            print(f"[!] {city}: 汉庭品牌搜索失败，跳过", flush=True)
                            out["cities"].append({"city": city, "city_id": city_id, "hotels": []})
                            self._save(out, output_file)
                            continue

                        # 目标页扫描：按欢迎度取第一家有报价的汉庭
                        target = self._scan_hanting(fp, city, "target")
                        chosen_name, chosen, flagship_sold_out = self._pick_hanting(target)
                        if not chosen:
                            print(f"[!] {city}: 未找到有报价的汉庭（扫描 {len(target)} 家），跳过", flush=True)
                            if fp is not page:
                                fp.close()
                            out["cities"].append({"city": city, "city_id": city_id, "hotels": []})
                            self._save(out, output_file)
                            continue
                        if flagship_sold_out:
                            print(f"    [!] {city}: 首选汉庭节日售罄，已顺延到「{chosen_name}」", flush=True)
                        print(f"    [→] {city} 锚定汉庭：{chosen_name}（节日价 {chosen.get('price')}）", flush=True)

                        # 基准日：在同一过滤标签页内，把过滤 URL 的日期换成基准日（保持汉庭过滤）
                        self._sleep(2.0, 4.0)
                        baseline_filtered = self._swap_dates(fp.url, target_date, baseline_date)
                        fp.goto(baseline_filtered, wait_until="domcontentloaded")
                        baseline = self._scan_hanting(fp, city, "baseline", want_names={chosen_name})
                        base = baseline.get(chosen_name, {})

                        if fp is not page:
                            fp.close()

                        hotel = {
                            "name": chosen_name,
                            "brand": "汉庭",
                            "room_type": chosen.get("room_type", ""),
                            "target_price": chosen.get("price"),
                            "baseline_price": base.get("price"),
                            "sold_out": chosen.get("sold_out", False),
                            "flagship_sold_out": flagship_sold_out,
                            "url": chosen.get("url", ""),
                        }
                        out["cities"].append({"city": city, "city_id": city_id, "hotels": [hotel]})
                    except Exception as e:
                        print(f"[!] 城市 '{city}' 抓取失败: {e}", flush=True)
                        out["cities"].append({"city": city, "hotels": []})
                    finally:
                        self._save(out, output_file)
                        self._sleep(2.0, 5.0)
            finally:
                self._save(out, output_file)
                ctx.close()
                browser.close()

        return out

    @staticmethod
    def _save(out: dict, output_file: str):
        if not output_file:
            return
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser(description="携程华住酒店价格抓取")
    parser.add_argument("--cities", default="", help="逗号分隔城市；留空使用内置热门城市")
    parser.add_argument("--target-date", required=True, help="目标日期 YYYY-MM-DD（如节假日入住日）")
    parser.add_argument("--baseline-date", default="", help="平日基准日 YYYY-MM-DD；留空自动取「节后第一个非节假周二」")
    parser.add_argument("--output", default="", help="raw.json 输出路径；留空自动按时间戳目录生成")
    parser.add_argument("--safe-mode", action="store_true", help="安全模式（延迟增大）")
    parser.add_argument("--speed-mode", action="store_true", help="极速模式（去除延时，风控风险高）")
    parser.add_argument("--debug", action="store_true", help="每城落调试截图 ctrip_debug_*.png")
    args = parser.parse_args()

    cities = parse_cities(args.cities)
    target_date = args.target_date
    baseline_date = args.baseline_date or compute_baseline_date(target_date)

    output = args.output
    if not output:
        ts = time.strftime("%Y%m%d_%H%M%S")
        # SCRIPT_DIR = <repo>/.claude/skills/huazhu-crowd-index/scripts → parents[3] = <repo>
        output = str(SCRIPT_DIR.parents[3] / "data" / "huazhu" / ts / "raw.json")

    print(f"[*] 目标日期: {target_date} | 平日基准日: {baseline_date}", flush=True)
    print(f"[*] 城市({len(cities)}): {', '.join(cities)}", flush=True)
    print(f"[*] 输出: {output}", flush=True)

    fetcher = CtripFetcher(
        safe_mode=args.safe_mode,
        speed_mode=args.speed_mode,
        debug=args.debug,
    )
    fetcher.run(cities, target_date, baseline_date, output)
    print(f"\n[✓] 抓取完成 → {output}", flush=True)


if __name__ == "__main__":
    main()
