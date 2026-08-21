#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LiteLLM 网关全量模型测速脚本。

从一个 LiteLLM 网关（或任意 Anthropic Messages 兼容端点）：
  1. GET /v1/models 拉取完整模型清单（可选 GET /model/info 拉元信息）
  2. 对每个模型做流式对话测速：连通性 / 首字延迟(TTFT) / 思考耗时 / 端到端吞吐(TPS)

用法示例：
  # 只列模型清单（含元信息）
  python speedtest.py --list-only

  # 全量测速（默认并发 8，每模型 max_tokens 512，报告落到仓库根目录 data/litellm-model-speedtest/）
  python speedtest.py

  # 自定义网关
  python speedtest.py --base-url https://gateway.example.com --api-key sk-xxx \
      --proxy http://127.0.0.1:7897 --concurrency 6 --max-tokens 1024

输出：终端汇总 + 默认生成仓库根目录 data/litellm-model-speedtest/speedtest_YYYYMMDD.json
与同目录同名 .html 自包含报告（--no-html 关闭）。

配置优先级：命令行参数 > 环境变量 > 内置默认值。
环境变量：LLM_BASE_URL / LLM_API_KEY / LLM_PROXY / LLM_HTTP_PROXY
"""
import argparse
import html
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ---- 默认值（360 LiteLLM Gateway）----
DEFAULT_BASE_URL = os.environ.get(
    "LLM_BASE_URL", "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net")
DEFAULT_API_KEY = os.environ.get(
    "LLM_API_KEY", "sk-REPLACED")
# 该域名仅能通过本地代理解析（与 pi settings 的 httpProxy 一致）
DEFAULT_PROXY = os.environ.get("LLM_PROXY") or os.environ.get(
    "LLM_HTTP_PROXY", "http://127.0.0.1:7897")


def _repo_root():
    """定位仓库根目录（向上找 .git），找不到则回退到当前工作目录。"""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


# 报告默认输出到仓库根目录 data/litellm-model-speedtest/（与 cwd 无关）
DEFAULT_REPORT_DIR = os.environ.get(
    "LLM_REPORT_DIR", str(_repo_root() / "data" / "litellm-model-speedtest"))

DEFAULT_PROMPT = "请用200字左右介绍你自己，说明你的能力和适用场景。"

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def build_proxies(proxy):
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}


def build_headers(api_key):
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def estimate_tokens(text: str) -> int:
    """无 usage 上报时的粗略估算：CJK 字=1 token，其余按 4 字符=1 token。"""
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return cjk + (len(text) - cjk) // 4


def fetch_models(base, api_key, proxies):
    """GET /v1/models -> 模型 ID 列表。"""
    h = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(base.rstrip("/") + "/v1/models", headers=h,
                     proxies=proxies, timeout=60)
    r.raise_for_status()
    return [m["id"] for m in r.json()["data"]]


def fetch_model_info(base, api_key, proxies):
    """GET /model/info -> {model_name: {size, ctx, vision, reasoning, provider}}。
    只取每个 model_name 的第一条部署记录。失败返回空 dict（不致命）。"""
    h = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(base.rstrip("/") + "/model/info", headers=h,
                         proxies=proxies, timeout=120)
        r.raise_for_status()
    except Exception:
        return {}
    out = {}
    for m in r.json().get("data", []):
        mn = m.get("model_name")
        if not mn or mn in out:
            continue
        lp = m.get("litellm_params", {}) or {}
        mi = m.get("model_info", {}) or {}
        out[mn] = {
            "size": mi.get("model_size"),
            "context": mi.get("model_context"),
            "vision": bool(mi.get("supports_vision")),
            "reasoning": bool(mi.get("supports_reasoning")),
            "provider": mi.get("litellm_provider"),
            "base_model": lp.get("model"),
            "input_cost": lp.get("input_cost_per_token"),
            "output_cost": lp.get("output_cost_per_token"),
            "tags": lp.get("tags"),
        }
    return out


def test_model(base, headers, proxies, model_id, max_tokens, prompt, timeout):
    """流式测速单个模型。返回结果 dict。"""
    body = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    res = {"model": model_id}
    t_start = time.perf_counter()
    t_first_think = t_first_text = None
    text_chunks, think_chunks = [], []
    out_tokens, stop_reason, status, err = None, None, None, None
    try:
        with requests.post(base.rstrip("/") + "/v1/messages", headers=headers,
                           json=body, proxies=proxies,
                           timeout=(timeout, timeout), stream=True) as r:
            status = r.status_code
            if status != 200:
                err = r.text[:200].replace("\n", " ")
                res.update(ok=False, status=status, err=err)
                return res
            for raw in r.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                payload = raw[5:].strip()
                if not payload:
                    continue
                try:
                    ev = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                et = ev.get("type")
                if et == "content_block_delta":
                    d = ev.get("delta", {})
                    now = time.perf_counter()
                    if d.get("type") == "text_delta" and d.get("text"):
                        t_first_text = t_first_text or now
                        text_chunks.append(d["text"])
                    elif d.get("type") == "thinking_delta" and d.get("thinking"):
                        t_first_think = t_first_think or now
                        think_chunks.append(d["thinking"])
                elif et == "message_delta":
                    u = ev.get("usage") or {}
                    if u.get("output_tokens") is not None:
                        out_tokens = u["output_tokens"]
                    if ev.get("delta", {}).get("stop_reason"):
                        stop_reason = ev["delta"]["stop_reason"]
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        res.update(ok=False, status=status, err=err)
        return res

    t_end = time.perf_counter()
    total_s = t_end - t_start
    text = "".join(text_chunks)
    thinking = "".join(think_chunks)
    tokens = out_tokens if out_tokens else (
        estimate_tokens(text) + estimate_tokens(thinking))
    res.update(
        ok=True, status=status,
        total_s=round(total_s, 2),
        ttft_s=round(t_first_text - t_start, 3) if t_first_text else None,
        first_think_s=round(t_first_think - t_start, 3) if t_first_think else None,
        think_chars=len(thinking), text_chars=len(text),
        tokens=tokens, from_usage=out_tokens is not None,
        e2e_tps=round(tokens / total_s, 2) if total_s > 0 else 0.0,
        stop_reason=stop_reason, err=err,
    )
    return res


def classify_failure(r):
    """把失败结果归因，方便用户判断要不要重试。"""
    if not r.get("err"):
        return "未知"
    e = r["err"]
    st = r.get("status") or ""
    if st == 403 or "Permission" in e or "access deny" in e:
        return "无权限(403)"
    if st == 404 or "NotFound" in e or "not found" in e:
        return "后端不存在(404)"
    if st == 503 or "No available channel" in e:
        return "无可用channel(503)"
    if st == 400:
        return "参数/模型名非法(400)"
    if "ReadTimeout" in e or "ConnectTimeout" in e:
        return "超时(慢或非对话模型)"
    return f"{st} {e[:40]}"


VENDOR_ORDER = [
    "GLM / 智谱", "Kimi / 月之暗面", "DeepSeek", "Qwen / 阿里",
    "ChatGPT / OpenAI", "Claude / Anthropic", "Gemini / Google",
    "Embedding / 向量", "Image / 图像", "其他",
]


def detect_vendor(model_id):
    """从模型名推断供应商，用于分组与筛选。"""
    m = (model_id or "").lower().split("/")[-1]   # 去路由前缀 m1/ m2/ 360/
    m = re.sub(r"-openai$", "", m)                 # 去 -openai 后缀变体
    if any(k in m for k in ("embedding", "bge", "rerank")):
        return "Embedding / 向量"
    if any(k in m for k in ("image", "dall-e", "flux", "sdxl", "stable-diffusion")):
        return "Image / 图像"
    families = [
        ("GLM / 智谱", ["glm", "chatglm", "zhipu"]),
        ("Kimi / 月之暗面", ["kimi", "moonshot"]),
        ("DeepSeek", ["deepseek"]),
        ("Qwen / 阿里", ["qwen"]),
        ("ChatGPT / OpenAI", ["gpt", "chatgpt", "openai", "o1", "o3", "o4"]),
        ("Claude / Anthropic", ["claude", "anthropic"]),
        ("Gemini / Google", ["gemini", "google"]),
    ]
    for vendor, keys in families:
        if any(k in m for k in keys):
            return vendor
    return "其他"


def _fmt(v, suffix=""):
    return "-" if v is None else f"{v}{suffix}"


def _badge(text, kind):
    colors = {
        "ok": ("#dafbe1", "#1a7f37"),
        "bad": ("#ffebe9", "#cf222e"),
        "warn": ("#fff8c5", "#9a6700"),
        "dim": ("#f6f8fa", "#57606a"),
    }
    bg, fg = colors.get(kind, colors["dim"])
    return (f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'background:{bg};color:{fg};font-size:12px;'
            f'font-weight:600;">{html.escape(text)}</span>')


def render_html(results, meta, base_url, params, total_sec):
    """生成自包含 HTML 报告（浅色主题，按供应商分组，带搜索/供应商筛选）。"""
    ok = [r for r in results if r.get("ok")]
    bad = [r for r in results if not r.get("ok")]
    ok_sorted = sorted(ok, key=lambda x: x["ttft_s"] if x.get("ttft_s") is not None else 99999)

    fastest = min((r for r in ok if r.get("ttft_s") is not None),
                  key=lambda x: x["ttft_s"], default=None)
    best_tps = max(ok, key=lambda x: x.get("e2e_tps", 0), default=None)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def meta_cell(mid, key):
        m = meta.get(mid) or {}
        return m.get(key) or ""

    def group_by(rows):
        groups = {}
        for r in rows:
            groups.setdefault(detect_vendor(r["model"]), []).append(r)

        def order_key(v):
            return (0, VENDOR_ORDER.index(v)) if v in VENDOR_ORDER else (1, v)
        return {v: groups[v] for v in sorted(groups, key=order_key)}

    ok_groups = group_by(ok_sorted)
    bad_groups = group_by(sorted(bad, key=lambda x: x["model"]))

    rows_ok_tbodies = []
    for vendor, rs in ok_groups.items():
        body = [f'<tbody class="group" data-vendor="{html.escape(vendor)}">',
                f'<tr class="ghead"><td colspan="12">'
                f'<span class="gname">{html.escape(vendor)}</span>'
                f'<span class="gcount">{len(rs)} 个</span></td></tr>']
        for i, r in enumerate(rs):
            ttft = r.get("ttft_s")
            ttft_cls = "dim" if ttft is None else ("fast" if ttft < 2 else ("mid" if ttft < 15 else "slow"))
            tps = r.get("e2e_tps", 0)
            tps_cls = "fast" if tps >= 60 else ("mid" if tps >= 25 else "slow")
            vision = "👁" if meta_cell(r["model"], "vision") else ""
            reason = "🧠" if meta_cell(r["model"], "reasoning") else ""
            body.append(
                f'<tr data-vendor="{html.escape(vendor)}">'
                f"<td class='num'>{i + 1}</td>"
                f"<td class='mono'>{html.escape(r['model'])}</td>"
                f"<td class='dim'>{html.escape(vendor)}</td>"
                f"<td class='dim'>{html.escape(str(meta_cell(r['model'], 'size')))}</td>"
                f"<td class='dim'>{html.escape(str(meta_cell(r['model'], 'context')))}</td>"
                f"<td class='dim'>{vision}{reason}</td>"
                f"<td class='mono {ttft_cls}'>{_fmt(ttft, 's')}</td>"
                f"<td class='mono dim'>{_fmt(r.get('first_think_s'), 's')}</td>"
                f"<td class='mono {tps_cls}'>{_fmt(r.get('e2e_tps'))}</td>"
                f"<td class='mono dim'>{r.get('tokens')}</td>"
                f"<td class='mono dim'>{_fmt(r.get('total_s'), 's')}</td>"
                f"<td class='dim'>{html.escape(str(r.get('stop_reason') or ''))}</td>"
                f"</tr>")
        body.append("</tbody>")
        rows_ok_tbodies.append("".join(body))

    rows_bad_tbodies = []
    for vendor, rs in bad_groups.items():
        body = [f'<tbody class="group" data-vendor="{html.escape(vendor)}">',
                f'<tr class="ghead"><td colspan="5">'
                f'<span class="gname">{html.escape(vendor)}</span>'
                f'<span class="gcount">{len(rs)} 个</span></td></tr>']
        for r in rs:
            body.append(
                f'<tr data-vendor="{html.escape(vendor)}">'
                f"<td class='mono'>{html.escape(r['model'])}</td>"
                f"<td class='dim'>{html.escape(vendor)}</td>"
                f"<td>{_badge(classify_failure(r), 'bad')}</td>"
                f"<td class='mono dim'>{html.escape(str(r.get('status') or ''))}</td>"
                f"<td class='dim err'>{html.escape((r.get('err') or '')[:160])}</td>"
                f"</tr>")
        body.append("</tbody>")
        rows_bad_tbodies.append("".join(body))

    kpi = [
        ("总模型", len(results), "dim"),
        ("可用", len(ok), "ok"),
        ("不可用", len(bad), "bad" if bad else "dim"),
        ("最快首字", f"{fastest['model'].split('/')[-1]} · {_fmt(fastest['ttft_s'], 's')}" if fastest else "-", "ok"),
        ("最高吞吐", f"{best_tps['model'].split('/')[-1]} · {_fmt(best_tps.get('e2e_tps'), ' tok/s')}" if best_tps else "-", "ok"),
    ]
    kpi_cards = "".join(
        f"<div class='kpi {k}'>"
        f"<div class='kpi-label'>{html.escape(label)}</div>"
        f"<div class='kpi-value'>{html.escape(str(val))}</div>"
        f"</div>" for label, val, k in kpi
    )

    vendors = []
    for v in list(ok_groups) + list(bad_groups):
        if v not in vendors:
            vendors.append(v)
    chips = '<button class="chip active" data-v="">全部</button>' + "".join(
        f'<button class="chip" data-v="{html.escape(v)}">{html.escape(v)}</button>' for v in vendors)

    return rf"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>模型测速报告 · {html.escape(base_url)}</title>
<style>
  :root {{ --bg:#f6f8fa; --card:#ffffff; --border:#d0d7de; --text:#1f2328; --dim:#57606a;
           --accent:#0969da; --green:#1a7f37; --yellow:#9a6700; --red:#cf222e; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
         font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:1280px; margin:0 auto; padding:32px 24px 64px; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .sub {{ color:var(--dim); font-size:13px; margin-bottom:20px; }}
  .sub code {{ color:var(--accent); }}
  .toolbar {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:24px; }}
  .toolbar input {{ padding:8px 12px; border:1px solid var(--border); border-radius:8px; font-size:14px;
                    background:var(--card); color:var(--text); width:240px; outline:none; }}
  .toolbar input:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px rgba(9,105,218,.15); }}
  .chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .chip {{ padding:5px 12px; border:1px solid var(--border); border-radius:999px; background:var(--card);
           color:var(--dim); font-size:13px; cursor:pointer; transition:.15s; }}
  .chip:hover {{ color:var(--accent); border-color:var(--accent); }}
  .chip.active {{ background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:28px; }}
  .kpi {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px 16px;
          box-shadow:0 1px 2px rgba(0,0,0,.04); }}
  .kpi-label {{ color:var(--dim); font-size:12px; }}
  .kpi-value {{ font-size:20px; font-weight:700; margin-top:4px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
  .kpi.ok .kpi-value {{ color:var(--green); }}
  .kpi.bad .kpi-value {{ color:var(--red); }}
  h2 {{ font-size:16px; margin:32px 0 12px; padding-left:10px; border-left:3px solid var(--accent); }}
  .table-wrap {{ background:var(--card); border:1px solid var(--border); border-radius:10px; overflow:auto;
                 max-height:70vh; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
  table {{ border-collapse:collapse; width:100%; min-width:1040px; }}
  th, td {{ padding:8px 12px; text-align:left; border-bottom:1px solid var(--border); white-space:nowrap; }}
  th {{ position:sticky; top:0; background:#f6f8fa; color:var(--dim); font-size:12px; font-weight:600;
        cursor:pointer; user-select:none; z-index:2; }}
  th:hover {{ color:var(--text); }}
  tr:hover td {{ background:#f0f4f8; }}
  tr.ghead td {{ background:#eef2f6; color:var(--text); font-weight:700; font-size:13px; padding:6px 12px; }}
  .gname {{ margin-right:8px; }}
  .gcount {{ color:var(--dim); font-weight:500; font-size:12px; }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
  .num {{ color:var(--dim); font-size:12px; }}
  .dim {{ color:var(--dim); }}
  .err {{ white-space:normal; max-width:520px; }}
  .fast {{ color:var(--green); }} .mid {{ color:var(--yellow); }} .slow {{ color:var(--red); }}
  footer {{ margin-top:40px; color:var(--dim); font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>🛰️ 模型测速报告</h1>
  <div class="sub">gateway <code>{html.escape(base_url)}</code> · 生成于 {stamp}
     · 并发 {params['concurrency']} · max_tokens {params['max_tokens']} · 总耗时 {total_sec:.0f}s</div>

  <div class="toolbar">
    <input id="search" type="text" placeholder="🔍 搜索模型名…">
    <div id="vendorChips" class="chips">{chips}</div>
  </div>

  <div class="kpis">{kpi_cards}</div>

  <h2>✅ 可用模型（按供应商分组，组内按首字延迟排序）</h2>
  <div class="table-wrap"><table id="okTable">
    <thead><tr>
      <th data-n="num">#</th><th>模型</th><th>供应商</th><th>规模</th><th>上下文</th><th>能力</th>
      <th data-n="num">TTFT·首字</th><th data-n="num">首个思考</th><th data-n="num">端到端TPS</th>
      <th data-n="num">输出tok</th><th data-n="num">总耗时</th><th>stop</th>
    </tr></thead>
    {''.join(rows_ok_tbodies) or '<tbody><tr><td colspan="12" class="dim">无</td></tr></tbody>'}
  </table></div>

  <h2>❌ 不可用模型</h2>
  <div class="table-wrap"><table id="badTable">
    <thead><tr><th>模型</th><th>供应商</th><th>归因</th><th>状态</th><th>错误信息</th></tr></thead>
    {''.join(rows_bad_tbodies) or '<tbody><tr><td colspan="5" class="dim">无</td></tr></tbody>'}
  </table></div>

  <footer>数据来源 /v1/models + /model/info · 脚本 scripts/speedtest.py · 端到端TPS=输出token÷总耗时</footer>
</div>
<script>
let activeVendor = '';
const search = document.getElementById('search');
function applyFilters() {{
  const q = search.value.trim().toLowerCase();
  document.querySelectorAll('table tbody.group').forEach(tb => {{
    const vendor = tb.dataset.vendor;
    const vendorOk = activeVendor === '' || vendor === activeVendor;
    let visible = 0;
    tb.querySelectorAll('tr[data-vendor]').forEach(row => {{
      const ok = vendorOk && (q === '' || row.innerText.toLowerCase().includes(q));
      row.style.display = ok ? '' : 'none';
      if (ok) visible++;
    }});
    tb.style.display = (vendorOk && visible > 0) ? '' : 'none';
  }});
}}
search.addEventListener('input', applyFilters);
document.querySelectorAll('#vendorChips .chip').forEach(c => {{
  c.addEventListener('click', () => {{
    document.querySelectorAll('#vendorChips .chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
    activeVendor = c.dataset.v;
    applyFilters();
  }});
}});
document.querySelectorAll('table').forEach(t => {{
  const ths = t.querySelectorAll('thead th');
  ths.forEach((th, ci) => {{
    th.addEventListener('click', () => {{
      const numeric = th.dataset.n === 'num';
      const dir = th.dataset.dir === 'asc' ? -1 : 1;
      ths.forEach(h => delete h.dataset.dir);
      th.dataset.dir = dir === 1 ? 'asc' : 'desc';
      t.querySelectorAll('tbody.group').forEach(tb => {{
        const rows = Array.from(tb.querySelectorAll('tr[data-vendor]'));
        rows.sort((a, b) => {{
          const va = a.cells[ci].innerText.trim(), vb = b.cells[ci].innerText.trim();
          if (numeric) {{
            const na = parseFloat(va.replace(/[^0-9.\-]/g, ''));
            const nb = parseFloat(vb.replace(/[^0-9.\-]/g, ''));
            if (isNaN(na) && isNaN(nb)) return 0;
            if (isNaN(na)) return 1;
            if (isNaN(nb)) return -1;
            return (na - nb) * dir;
          }}
          return va.localeCompare(vb, 'zh') * dir;
        }});
        rows.forEach(r => tb.appendChild(r));
      }});
    }});
  }});
}});
</script>
</body>
</html>"""


def render_summary(results, meta, total_sec):
    ok = [r for r in results if r.get("ok")]
    bad = [r for r in results if not r.get("ok")]
    print("\n" + "=" * 100)
    print(f"汇总：可用 {len(ok)} / 不可用 {len(bad)}  |  总耗时 {total_sec:.0f}s")
    print("=" * 100)
    if ok:
        print(f"{'模型':<36}{'TTFT(首字)':<12}{'端到端TPS':<11}{'输出tok':<9}{'总耗时':<9}stop")
        print("-" * 100)
        for r in sorted(ok, key=lambda x: x["ttft_s"] if x.get("ttft_s") is not None else 9999):
            ttft = f"{r['ttft_s']}s" if r.get("ttft_s") is not None else "(无正文)"
            print(f"{r['model']:<36}{ttft:<12}{r['e2e_tps']:<11}{r['tokens']:<9}{r['total_s']}s  {r['stop_reason']}")
    if bad:
        print("\n不可用模型：")
        for r in bad:
            print(f"  ❌ {r['model']:<36} {classify_failure(r)}  {r.get('err','')[:80]}")
    if meta:
        print("\n模型元信息（来自 /model/info，仅第一部署记录）：")
        print(f"{'模型':<36}{'规模':<9}{'上下文':<9}{'视觉':<5}{'推理':<5}{'来源':<10}")
        for r in sorted(ok, key=lambda x: x["model"]):
            m = meta.get(r["model"])
            if not m:
                continue
            print(f"{r['model']:<36}{str(m.get('size') or ''):<9}{str(m.get('context') or ''):<9}"
                  f"{'✓' if m.get('vision') else '':<5}{'✓' if m.get('reasoning') else '':<5}"
                  f"{str(m.get('provider') or ''):<10}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="LiteLLM 网关全量模型测速")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--api-key", default=DEFAULT_API_KEY)
    ap.add_argument("--proxy", default=DEFAULT_PROXY, help="本地代理，空串禁用")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--timeout", type=int, default=90, help="连接/读超时(秒)")
    ap.add_argument("--list-only", action="store_true", help="只列模型清单，不测速")
    ap.add_argument("--models", default=None, help="只测指定模型（逗号分隔，子串匹配）")
    ap.add_argument("--report-dir", default=DEFAULT_REPORT_DIR,
                    help="HTML/JSON 报告输出目录（默认仓库根目录 data/litellm-model-speedtest）")
    ap.add_argument("--no-html", action="store_true", help="不生成 HTML 报告")
    ap.add_argument("--out", default=None, help="结果 JSON 输出路径（覆盖默认）")
    args = ap.parse_args(argv)

    proxies = build_proxies(args.proxy or None)
    headers = build_headers(args.api_key)

    log(f"gateway: {args.base_url}")
    log(f"proxy: {args.proxy or '(无)'}")

    ids = fetch_models(args.base_url, args.api_key, proxies)
    if args.models:
        pats = [p.strip() for p in args.models.split(",") if p.strip()]
        ids = [m for m in ids if any(p in m for p in pats)]
        log(f"按 --models 过滤后 {len(ids)} 个模型")
    else:
        log(f"共 {len(ids)} 个模型")

    meta = fetch_model_info(args.base_url, args.api_key, proxies)
    if args.list_only:
        log(f"\n{'模型':<36}{'规模':<9}{'上下文':<9}{'视觉':<5}{'推理':<5}{'来源':<10}tags")
        log("-" * 110)
        for mid in ids:
            m = meta.get(mid)
            if not m:
                log(f"{mid}")
                continue
            log(f"{mid:<36}{str(m.get('size') or ''):<9}{str(m.get('context') or ''):<9}"
                f"{'✓' if m.get('vision') else '':<5}{'✓' if m.get('reasoning') else '':<5}"
                f"{str(m.get('provider') or ''):<10}{','.join(m.get('tags') or [])}")
        return 0

    log(f"并发 {args.concurrency}，每模型 max_tokens={args.max_tokens}，超时 {args.timeout}s")
    log("=" * 100)

    results = []
    done = 0
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(test_model, args.base_url, headers, proxies, m,
                          args.max_tokens, args.prompt, args.timeout): m
                for m in ids}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            if r.get("ok"):
                ttft = f"{r['ttft_s']}s" if r.get("ttft_s") is not None else "-"
                log(f"[{done:2d}/{len(ids)}] ✅ {r['model']:<32} TTFT {ttft:<8} "
                    f"E2E {r['e2e_tps']:>7} tok/s  {r['tokens']}tok  stop={r['stop_reason']}")
            else:
                log(f"[{done:2d}/{len(ids)}] ❌ {r['model']:<32} {classify_failure(r)}")

    results.sort(key=lambda x: x["model"])
    total_sec = time.perf_counter() - t0
    render_summary(results, meta, total_sec)

    # 报告落盘：默认 data/<技能名>/speedtest_YYYYMMDD.{json,html}（同日自动覆盖）
    stamp = time.strftime("%Y%m%d")
    os.makedirs(args.report_dir, exist_ok=True)
    out_path = args.out or os.path.join(args.report_dir, f"speedtest_{stamp}.json")
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log(f"\nJSON 结果: {out_path}")

    if not args.no_html:
        params = {"concurrency": args.concurrency, "max_tokens": args.max_tokens}
        html_path = os.path.join(args.report_dir, f"speedtest_{stamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render_html(results, meta, args.base_url, params, total_sec))
        log(f"HTML 报告: {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
