"""
选择器校准工具（维护用）。
当携程改版导致 fetch_prices.py 抓不到数据时，运行本脚本重新核对列表页选择器。

用法：python _calibrate_card.py <cityId> <checkin YYYY-MM-DD> <checkout YYYY-MM-DD>
  例： python _calibrate_card.py 17 2026-06-19 2026-06-20
依赖已登录的 ctrip_auth.json。输出：DOM 中酒店名/卡片/价格选择器命中情况 + 截图 _cal_card.png。
据此更新 ctrip_selectors.py 的 HOTEL_NAME / HOTEL_CARD / HOTEL_PRICE。
"""
import io
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.resolve()
AUTH = SCRIPT_DIR / "ctrip_auth.json"

CITY_ID = sys.argv[1] if len(sys.argv) > 1 else "17"
CHECKIN = sys.argv[2] if len(sys.argv) > 2 else "2026-06-19"
CHECKOUT = sys.argv[3] if len(sys.argv) > 3 else "2026-06-20"

URL = (
    "https://hotels.ctrip.com/hotels/list?flexType=1"
    f"&cityId={CITY_ID}&countryId=1&searchType=CT&optionId={CITY_ID}"
    f"&checkin={CHECKIN}&checkout={CHECKOUT}&crn=1&curr=CNY&locale=zh-CN"
)

CARD_JS = r"""
() => {
  const res = {url: location.href, names: [], guess: [], cards: []};
  // 1) 直接按可能的酒店名 class 找
  const nameEls = [...document.querySelectorAll(
    "[class*='hotel-name'],[class*='hotelName'],[class*='hotel_name'],[class*='list-card-title'],[class*='listCard'] [class*='name']"
  )];
  res.names = nameEls.slice(0,12).map(e=>({cls:(e.className||'').toString().slice(0,70), tag:e.tagName, text:(e.innerText||'').trim().slice(0,40)}));

  // 2) 兜底：文本像酒店名（含酒店/公寓/品牌词）、短、可见
  const hotelWord = /酒店|公寓|宾馆|度假|客栈|全季|汉庭|桔子|美居|宜必思|星程|怡莱|海友|你好|漫心|花间堂|希岸|麗枫|喆啡/;
  const guess = [...document.querySelectorAll('a,div,span,h2,h3')].filter(e=>{
    const t=(e.innerText||'').trim();
    return hotelWord.test(t) && t.length<30 && t.length>4 && e.getBoundingClientRect().width>0 && e.children.length<=2;
  });
  const seen = new Set();
  for (const e of guess) {
    const t=(e.innerText||'').trim();
    if (seen.has(t)) continue; seen.add(t);
    res.guess.push({cls:(e.className||'').toString().slice(0,70), tag:e.tagName, text:t});
    if (res.guess.length>=15) break;
  }

  // 3) 以名字元素为锚，向上找到含价格的卡片根，取卡片整体价格(.sale 最小) 与售罄
  const anchor = nameEls.length ? nameEls : guess;
  for (const nameEl of anchor.slice(0,6)) {
    let node = nameEl, card = null;
    for (let i=0;i<14 && node;i++){
      node = node.parentElement;
      if (node && (node.innerText||'').match(/[¥￥]\s*\d{2,}/)) { card = node; break; }
    }
    let price=null, sold=false, cardCls=null;
    if (card) {
      cardCls=(card.className||'').toString().slice(0,80);
      const saleEl = card.querySelector('.sale');
      if (saleEl) price = saleEl.innerText.trim();
      else { const m=(card.innerText||'').match(/[¥￥]\s*([\d,]+)/); if(m) price='¥'+m[1]; }
      sold = /已订完|订完|无房|售罄|满房/.test(card.innerText||'');
    }
    res.cards.push({name:(nameEl.innerText||'').trim().slice(0,40), price, sold, cardCls});
  }
  res.soldoutHit = /已订完|订完|无房|售罄|满房/.test(document.body.innerText);
  return res;
}
"""


def main():
    with sync_playwright() as pw:
        launch_kw = {"headless": False}
        if sys.platform == "win32":
            launch_kw["channel"] = "msedge"
        browser = pw.chromium.launch(**launch_kw)
        ctx = browser.new_context(storage_state=str(AUTH), locale="zh-CN",
                                  timezone_id="Asia/Shanghai", viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)

        print(f"[*] 直接导航构造 URL:\n    {URL}", flush=True)
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        # 滚动触发懒加载
        for _ in range(3):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1200)
        page.screenshot(path=str(SCRIPT_DIR / "_cal_card.png"))

        data = page.evaluate(CARD_JS)
        print(f"\n===== 落地 URL: {data['url']}", flush=True)
        print(f"===== 页面含售罄文案: {data['soldoutHit']}", flush=True)
        print("\n-- 按 class 找到的酒店名元素 --", flush=True)
        for n in data["names"]:
            print(f"    <{n['tag']}> text={n['text']!r} cls={n['cls']!r}", flush=True)
        print("\n-- 兜底文本猜测(酒店名) --", flush=True)
        for n in data["guess"]:
            print(f"    <{n['tag']}> text={n['text']!r} cls={n['cls']!r}", flush=True)
        print("\n-- 锚定卡片(名->价格->售罄) --", flush=True)
        for i, c in enumerate(data["cards"]):
            print(f"  [card {i}] name={c['name']!r} price={c['price']!r} sold={c['sold']} cardCls={c['cardCls']!r}", flush=True)

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
