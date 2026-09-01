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

输出：终端汇总 + 默认生成仓库根目录 data/litellm-model-speedtest/speedtest.json
与同目录同名 speedtest.html 自包含报告（每次运行直接覆盖，--no-html 关闭）。

配置优先级：命令行参数 > 环境变量 > 内置默认值。
环境变量：LLM_BASE_URL / LLM_API_KEY / LLM_PROXY / LLM_HTTP_PROXY
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ---- 默认值（360 LiteLLM Gateway）----
def _repo_root():
    """定位仓库根目录（向上找 .git），找不到则回退到当前工作目录。"""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def load_env():
    """从仓库根目录 .env 读入环境变量（不覆盖已有值）。"""
    env = _repo_root() / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


load_env()

def load_pi_configured_models(provider_name="360"):
    """读取 ~/.pi/agent/models.json 中指定 provider 配置的模型 ID 集合。"""
    config_dir = os.environ.get("PI_CONFIG_DIR")
    if config_dir:
        models_file = Path(config_dir) / "models.json"
    else:
        models_file = Path.home() / ".pi" / "agent" / "models.json"
    if not models_file.is_file():
        return set()
    try:
        data = json.loads(models_file.read_text(encoding="utf-8"))
        providers = data.get("providers", {})
        p = providers.get(provider_name)
        if not p:
            for k, v in providers.items():
                if k.lower() == provider_name.lower():
                    p = v
                    break
        if not p:
            return set()
        return {m["id"] for m in p.get("models", []) if isinstance(m, dict) and "id" in m}
    except Exception:
        return set()

DEFAULT_BASE_URL = os.environ.get(
    "LLM_BASE_URL", "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net")
# API key 只从环境变量 / .env 读取，不再硬编码（缺失时脚本会报错提示）
DEFAULT_API_KEY = os.environ.get("LLM_API_KEY", "")
# 该域名仅能通过本地代理解析（与 pi settings 的 httpProxy 一致）
DEFAULT_PROXY = os.environ.get("LLM_PROXY") or os.environ.get(
    "LLM_HTTP_PROXY", "http://127.0.0.1:7897")


# 报告默认输出到仓库根目录 data/litellm-model-speedtest/（与 cwd 无关）
DEFAULT_REPORT_DIR = os.environ.get(
    "LLM_REPORT_DIR", str(_repo_root() / "data" / "litellm-model-speedtest"))

# 远程服务器部署配置（支持 SCP 推送）
DEFAULT_DEPLOY_TARGET = os.environ.get("SPEEDTEST_DEPLOY_TARGET", "")
DEFAULT_DEPLOY_PORT = int(os.environ.get("SPEEDTEST_DEPLOY_PORT", "0")) or None
DEFAULT_DEPLOY_KEY = os.environ.get("SPEEDTEST_DEPLOY_KEY", "")
DEFAULT_DEPLOY_URL = os.environ.get("SPEEDTEST_DEPLOY_URL", "")

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


def fetch_models_dev(proxies=None):
    """从 models.dev 抓取全球模型元数据（上下文、输出上限、发布时间、推理、模态等）。
    优先请求 models.dev API，失败降级到 raw GitHub，均失败返回空 dict（不影响主流程）。"""
    urls = [
        "https://models.dev/models.json",
        "https://raw.githubusercontent.com/anomalyco/models.dev/main/models.json",
    ]
    for url in urls:
        try:
            r = requests.get(url, proxies=proxies, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data:
                    return data
        except Exception:
            continue
    return {}


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
    "Doubao / 字节", "MiniMax", "360 / 智脑",
    "ChatGPT / OpenAI", "Claude / Anthropic", "Gemini / Google",
    "Embedding / 向量", "Image / 图像", "其他",
]


def detect_vendor(model_id):
    """从模型名推断供应商，用于分组与筛选。"""
    m = (model_id or "").lower().split("/")[-1]   # 去路由前缀 m1/ m2/ 360/
    m = re.sub(r"-openai$", "", m)                 # 去 -openai 后缀变体
    if m.startswith("360-"):
        m = m[4:]
    if any(k in m for k in ("embedding", "bge", "rerank")):
        return "Embedding / 向量"
    if any(k in m for k in ("dall-e", "flux", "sdxl", "stable-diffusion")):
        return "Image / 图像"
    families = [
        ("GLM / 智谱", ["glm", "chatglm", "zhipu"]),
        ("Kimi / 月之暗面", ["kimi", "moonshot"]),
        ("DeepSeek", ["deepseek"]),
        ("Qwen / 阿里", ["qwen"]),
        ("360 / 智脑", ["360", "zhinao", "qihoo"]),
        ("Doubao / 字节", ["doubao", "skylark", "bytedance", "volcengine"]),
        ("MiniMax", ["minimax", "abab"]),
        ("ChatGPT / OpenAI", ["gpt", "chatgpt", "openai", "o1", "o3", "o4"]),
        ("Claude / Anthropic", ["claude", "anthropic"]),
        ("Gemini / Google", ["gemini", "google"]),
    ]
    for vendor, keys in families:
        if any(k in m for k in keys):
            return vendor
    if "image" in m:
        return "Image / 图像"
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


def normalize_model_version(mid):
    """从网关模型 ID 提取归一化的版本 key 与基础展示名。
    例如：
      m3/glm-5.3-flash-openai -> glm-5.3-flash
      360/deepseek-v4-pro-openai -> deepseek-v4-pro
      m1/deepseek-v4-flash -> deepseek-v4-flash
      360/deepseek-r1-0528 -> deepseek-r1
      360/360-qwen3-coder-480b-a35b -> qwen3-coder-480b-a35b
    """
    raw = (mid or "").split("/")[-1]
    # 去除 -openai / _openai
    v = re.sub(r"[-_]openai$", "", raw, flags=re.IGNORECASE)
    # 去除 360- 前缀
    if v.lower().startswith("360-"):
        v = v[4:]
    v_clean = v
    # deepseek-r1-0528 / deepseek-v3-250324 -> deepseek-r1 / deepseek-v3
    if re.match(r"^(deepseek-[rv]\d+(\.\d+)?)-(\d{4,6})$", v_clean, re.I):
        v_clean = re.sub(r"-(\d{4,6})$", "", v_clean, flags=re.I)
    # kimi-k2-instruct-0905 -> kimi-k2
    elif re.match(r"^(kimi-k\d+(\.\d+)?)-instruct-\d+$", v_clean, re.I):
        v_clean = re.sub(r"-instruct-\d+$", "", v_clean, flags=re.I)
    # glm-5.2-codex -> glm-5.2
    elif v_clean.lower() == "glm-5.2-codex":
        v_clean = "glm-5.2"
    # 去除 -instruct 后缀
    elif v_clean.lower().endswith("-instruct"):
        v_clean = v_clean[:-9]
    return v_clean.lower(), v


def match_models_dev(canon_key, models_dev):
    """在 models.dev 中检索对应的官方规格数据。"""
    if not models_dev:
        return None
    # 1. 直接 slug 匹配
    norm_k = canon_key.replace(".", "-").replace("_", "-")
    for k, info in models_dev.items():
        slug = k.split("/")[-1].lower().replace(".", "-").replace("_", "-")
        if slug == norm_k:
            return info
    # 2. 纯字母数字匹配
    clean_k = re.sub(r"[^a-z0-9]", "", canon_key)
    for k, info in models_dev.items():
        slug_clean = re.sub(r"[^a-z0-9]", "", k.split("/")[-1].lower())
        if clean_k == slug_clean:
            return info
    # 3. 边界前缀匹配
    for k, info in models_dev.items():
        slug = k.split("/")[-1].lower()
        if slug.startswith(canon_key + "-") or canon_key.startswith(slug + "-"):
            return info
    return None


def format_token_count(n):
    """格式化 token 数量：1000000 -> 1M (1,000,000), 131072 -> 131K (131,072)"""
    if not n or not isinstance(n, (int, float)):
        return "-"
    n = int(n)
    if n >= 1_000_000:
        val = f"{n/1_000_000:.1f}M".replace(".0M", "M")
    elif n >= 1_000:
        val = f"{n/1_000:.0f}K"
    else:
        val = str(n)
    return f"{val} ({n:,})"


def render_html(results, meta, base_url, params, total_sec, models_dev=None):
    """生成自包含 HTML 报告：
    - 按供应商分组
    - 每个供应商下按模型版本合并（Version Block）
    - 优先展示最新发布的版本（release_date 降序）
    - 每个版本内各部署节点按 TPS 降序排序
    - 显示上下文窗口、最大输出 token 等元信息（无价格）
    """
    models_dev = models_dev or {}

    stamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. 结构化归类：Vendor -> Canonical Version -> List of models
    vendor_dict = {}
    for r in results:
        mid = r["model"]
        vendor = detect_vendor(mid)
        cv_key, cv_raw = normalize_model_version(mid)
        dev_meta = match_models_dev(cv_key, models_dev) or {}
        local_m = meta.get(mid) or {}

        v_group = vendor_dict.setdefault(vendor, {})
        if cv_key not in v_group:
            disp_name = dev_meta.get("name") or cv_raw
            rel_date = dev_meta.get("release_date") or dev_meta.get("last_updated") or ""
            ctx = dev_meta.get("limit", {}).get("context") or local_m.get("context")
            out = dev_meta.get("limit", {}).get("output")
            is_reason = dev_meta.get("reasoning") if "reasoning" in dev_meta else local_m.get("reasoning", False)
            modalities = dev_meta.get("modalities", {}) or {}
            is_vision = ("image" in (modalities.get("input") or [])) or local_m.get("vision", False)
            v_group[cv_key] = {
                "key": cv_key,
                "name": disp_name,
                "release_date": rel_date,
                "context": ctx,
                "output": out,
                "reasoning": bool(is_reason),
                "vision": bool(is_vision),
                "models": [],
            }
        v_group[cv_key]["models"].append(r)

    def version_sort_key(ver):
        rel = ver.get("release_date") or ""
        if re.match(r"^\d{4}(-\d{2})?(-\d{2})?$", rel):
            return (2, rel, ver["key"])
        m = re.search(r"(\d+(?:\.\d+)?)", ver["key"])
        if m:
            try:
                return (1, f"{float(m.group(1)):08.2f}", ver["key"])
            except Exception:
                pass
        return (0, rel, ver["key"])

    # 2. 生成 HTML 块
    vendor_sections = []
    total_version_count = 0
    for vendor in sorted(vendor_dict.keys(), key=lambda v: (0, VENDOR_ORDER.index(v)) if v in VENDOR_ORDER else (1, v)):
        v_versions = vendor_dict[vendor]
        sorted_versions = sorted(v_versions.values(), key=version_sort_key, reverse=True)
        total_version_count += len(sorted_versions)

        v_blocks_html = []
        for ver in sorted_versions:
            # 组内排序：可用模型按 TPS 降序，不可用排在后面
            ok_models = [m for m in ver["models"] if m.get("ok")]
            bad_models = [m for m in ver["models"] if not m.get("ok")]
            ok_models.sort(key=lambda x: x.get("e2e_tps", 0), reverse=True)
            bad_models.sort(key=lambda x: x["model"])
            sorted_models = ok_models + bad_models

            # 版本规格标签
            specs = []
            if ver["release_date"]:
                specs.append(f'<span class="spec-tag date" title="发布时间">📅 {html.escape(ver["release_date"])}</span>')
            if ver["context"]:
                specs.append(f'<span class="spec-tag ctx" title="上下文上限">🗂️ 上下文: {format_token_count(ver["context"])}</span>')
            if ver["output"]:
                specs.append(f'<span class="spec-tag out" title="最大输出 Tokens">📤 最大输出: {format_token_count(ver["output"])}</span>')
            if ver["reasoning"]:
                specs.append('<span class="spec-tag feat" title="支持思考推理">🧠 思考推理</span>')
            if ver["vision"]:
                specs.append('<span class="spec-tag feat" title="支持视觉/多模态输入">👁️ 视觉能力</span>')
            specs.append(f'<span class="spec-tag count">{len(sorted_models)} 个部署</span>')

            # 表格行
            tbody_rows = []
            for i, r in enumerate(sorted_models):
                mid = r["model"]
                is_ok = r.get("ok", False)

                if is_ok:
                    status_badge = '<span class="status-ok">✅ 可用</span>'
                    ttft = r.get("ttft_s")
                    ttft_cls = "dim" if ttft is None else ("fast" if ttft < 2 else ("mid" if ttft < 15 else "slow"))
                    tps = r.get("e2e_tps", 0)
                    tps_cls = "fast bold" if tps >= 60 else (("mid bold" if tps >= 25 else "slow bold"))
                    first_think = _fmt(r.get("first_think_s"), "s")
                    e2e_tps = _fmt(r.get("e2e_tps"))
                    toks = str(r.get("tokens") or "")
                    total_t = _fmt(r.get("total_s"), "s")
                    reason_or_err = html.escape(str(r.get("stop_reason") or ""))
                else:
                    status_badge = f'<span class="status-bad">❌ {html.escape(classify_failure(r))}</span>'
                    ttft_cls = "dim"
                    tps_cls = "dim"
                    ttft = "-"
                    first_think = "-"
                    e2e_tps = "-"
                    toks = "-"
                    total_t = "-"
                    reason_or_err = f'<span class="err-text" title="{html.escape(r.get("err") or "")}">{html.escape((r.get("err") or "")[:80])}</span>'

                ttft_str = _fmt(ttft, "s") if isinstance(ttft, (int, float)) else str(ttft)

                tbody_rows.append(
                    f'<tr data-vendor="{html.escape(vendor)}">'
                    f'<td class="num">{i + 1}</td>'
                    f'<td class="mono"><span class="model-name" title="点击复制模型 ID">{html.escape(mid)}</span></td>'
                    f'<td>{status_badge}</td>'
                    f'<td class="mono {ttft_cls}">{ttft_str}</td>'
                    f'<td class="mono dim">{first_think}</td>'
                    f'<td class="mono {tps_cls}">{e2e_tps}</td>'
                    f'<td class="mono dim">{toks}</td>'
                    f'<td class="mono dim">{total_t}</td>'
                    f'<td class="dim">{reason_or_err}</td>'
                    f'</tr>'
                )

            v_blocks_html.append(
                f'<div class="version-card" data-vendor="{html.escape(vendor)}" data-vname="{html.escape(ver["name"].lower())}">'
                f'  <div class="version-header">'
                f'    <div class="version-title">'
                f'      <span class="vname">{html.escape(ver["name"])}</span>'
                f'      <span class="vkey mono dim">({html.escape(ver["key"])})</span>'
                f'    </div>'
                f'    <div class="version-specs">{" ".join(specs)}</div>'
                f'  </div>'
                f'  <div class="version-table-wrap">'
                f'    <table>'
                f'      <thead><tr>'
                f'        <th data-n="num" style="width:36px">#</th>'
                f'        <th>部署模型 ID</th>'
                f'        <th>状态</th>'
                f'        <th data-n="num">TTFT·首字</th>'
                f'        <th data-n="num">首个思考</th>'
                f'        <th data-n="num">端到端 TPS</th>'
                f'        <th data-n="num">输出 Tokens</th>'
                f'        <th data-n="num">总耗时</th>'
                f'        <th>Stop / 备注</th>'
                f'      </tr></thead>'
                f'      <tbody>{"".join(tbody_rows)}</tbody>'
                f'    </table>'
                f'  </div>'
                f'</div>'
            )

        vendor_sections.append(
            f'<div class="vendor-section" data-vendor="{html.escape(vendor)}">'
            f'  <div class="vendor-header">'
            f'    <span class="vendor-title">{html.escape(vendor)}</span>'
            f'    <span class="vendor-count">{len(sorted_versions)} 个版本 · {sum(len(v["models"]) for v in sorted_versions)} 个部署</span>'
            f'  </div>'
            f'  <div class="vendor-body">{"".join(v_blocks_html)}</div>'
            f'</div>'
        )

    # 供应商过滤 Chips
    chips = '<button class="chip active" data-v="">全部供应商</button>' + "".join(
        f'<button class="chip" data-v="{html.escape(v)}">{html.escape(v)} ({len(vendor_dict[v])})</button>'
        for v in sorted(vendor_dict.keys(), key=lambda x: (0, VENDOR_ORDER.index(x)) if x in VENDOR_ORDER else (1, x))
    )

    models_dev_status = "✅ 已同步 models.dev 元数据" if models_dev else "⚠️ models.dev 离线模式"

    return rf"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LiteLLM 模型测速与版本规格报告 · {html.escape(base_url)}</title>
<style>
  :root {{
    --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0; --text: #0f172a; --dim: #64748b;
    --accent: #2563eb; --accent-light: #eff6ff; --green: #16a34a; --green-bg: #dcfce7;
    --yellow: #d97706; --yellow-bg: #fef3c7; --red: #dc2626; --red-bg: #fee2e2;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
         font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:1380px; margin:0 auto; padding:32px 24px 80px; }}
  h1 {{ font-size:24px; margin:0 0 6px; font-weight:700; color:var(--text); letter-spacing:-0.3px; }}
  .sub {{ color:var(--dim); font-size:13px; margin-bottom:24px; display:flex; flex-wrap:wrap; gap:12px; align-items:center; }}
  .sub code {{ color:var(--accent); background:var(--accent-light); padding:2px 6px; border-radius:4px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
  .meta-tag {{ display:inline-block; padding:2px 8px; border-radius:6px; background:#f1f5f9; color:#475569; font-size:12px; }}

  .toolbar {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:28px; }}
  .toolbar input {{ padding:9px 14px; border:1px solid var(--border); border-radius:8px; font-size:14px;
                    background:var(--card); color:var(--text); width:280px; outline:none; transition:.15s; }}
  .toolbar input:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px rgba(37,99,235,.15); }}
  .chips {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .chip {{ padding:6px 13px; border:1px solid var(--border); border-radius:999px; background:var(--card);
           color:var(--dim); font-size:13px; cursor:pointer; transition:.15s; user-select:none; }}
  .chip:hover {{ color:var(--accent); border-color:var(--accent); }}
  .chip.active {{ background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }}
  .chip-cfg {{ border-color:#93c5fd; color:var(--accent); font-weight:600; background:var(--accent-light); }}
  .chip-cfg.active {{ background:var(--accent); border-color:var(--accent); color:#fff; }}

  .vendor-section {{ margin-bottom:36px; }}
  .vendor-header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;
                    padding-bottom:8px; border-bottom:2px solid var(--border); }}
  .vendor-title {{ font-size:18px; font-weight:700; color:var(--text); }}
  .vendor-count {{ font-size:13px; color:var(--dim); }}

  .version-card {{ background:var(--card); border:1px solid var(--border); border-radius:12px;
                   margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.03); overflow:hidden; transition:box-shadow .15s; }}
  .version-card:hover {{ box-shadow:0 4px 12px rgba(0,0,0,.06); }}
  .version-header {{ padding:12px 18px; background:#f8fafc; border-bottom:1px solid var(--border);
                    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .version-title {{ display:flex; align-items:center; gap:8px; }}
  .vname {{ font-size:15px; font-weight:700; color:var(--text); }}
  .vkey {{ font-size:12px; color:var(--dim); }}
  .version-specs {{ display:flex; gap:6px; flex-wrap:wrap; align-items:center; }}
  .spec-tag {{ display:inline-block; padding:3px 9px; border-radius:6px; font-size:12px; font-weight:500; }}
  .spec-tag.date {{ background:#fef3c7; color:#92400e; font-weight:600; }}
  .spec-tag.ctx {{ background:#e0f2fe; color:#0369a1; }}
  .spec-tag.out {{ background:#f3e8ff; color:#7e22ce; }}
  .spec-tag.feat {{ background:#f1f5f9; color:#334155; }}
  .spec-tag.count {{ background:#f8fafc; color:var(--dim); border:1px solid var(--border); }}

  .version-table-wrap {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; min-width:980px; }}
  th, td {{ padding:9px 16px; text-align:left; border-bottom:1px solid var(--border); white-space:nowrap; font-size:13px; }}
  th {{ background:#ffffff; color:var(--dim); font-size:12px; font-weight:600; user-select:none; }}
  tr:last-child td {{ border-bottom:none; }}
  tr:hover td {{ background:#f8fafc; }}

  .model-name {{ cursor:pointer; border-bottom:1px dashed var(--dim); transition:.15s; font-weight:500; }}
  .model-name:hover {{ color:var(--accent); border-bottom-color:var(--accent); }}

  .status-ok {{ color:var(--green); font-weight:600; font-size:12px; }}
  .status-bad {{ color:var(--red); font-size:12px; }}
  .err-text {{ color:var(--red); font-size:12px; }}

  .mono {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
  .num {{ color:var(--dim); font-size:12px; }}
  .dim {{ color:var(--dim); }}
  .bold {{ font-weight:700; }}
  .fast {{ color:var(--green); }} .mid {{ color:var(--yellow); }} .slow {{ color:var(--red); }}

  .toast {{ position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:#0f172a; color:#fff;
           padding:8px 16px; border-radius:8px; font-size:13px; opacity:0; pointer-events:none;
           transition:opacity .2s, transform .2s; z-index:999; box-shadow:0 4px 12px rgba(0,0,0,.15); }}
  .toast.show {{ opacity:1; transform:translate(-50%, -4px); }}
  footer {{ margin-top:48px; color:var(--dim); font-size:12px; text-align:center; padding-top:20px; border-top:1px solid var(--border); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>🛰️ 模型测速与版本规格报告</h1>
  <div class="sub">
    <span>Gateway: <code>{html.escape(base_url)}</code></span>
    <span class="meta-tag">生成于 {stamp}</span>
    <span class="meta-tag">并发: {params['concurrency']} · max_tokens: {params['max_tokens']} · 耗时: {total_sec:.0f}s</span>
    <span class="meta-tag">{models_dev_status}</span>
    <span class="meta-tag">聚合: {total_version_count} 个模型版本 · {len(results)} 个部署节点</span>
  </div>

  <div class="toolbar">
    <input id="search" type="text" placeholder="🔍 搜索模型名 / 版本名 / 供应商…">
    <div id="vendorChips" class="chips">{chips}</div>
  </div>

  <div id="sectionsContainer">
    {''.join(vendor_sections) or '<div class="dim" style="text-align:center;padding:48px;">无测速结果</div>'}
  </div>

  <footer>
    数据来源: LiteLLM Gateway (/v1/models, /model/info) + GitHub <a href="https://github.com/anomalyco/models.dev" target="_blank" style="color:var(--accent);">anomalyco/models.dev</a> · 组内已按端到端 TPS 降序排序
  </footer>
</div>

<script>
let activeVendor = '';
const search = document.getElementById('search');

function applyFilters() {{
  const q = search.value.trim().toLowerCase();

  document.querySelectorAll('.vendor-section').forEach(vSec => {{
    const vendorName = vSec.dataset.vendor;
    let vendorVisibleCards = 0;

    vSec.querySelectorAll('.version-card').forEach(vCard => {{
      const vName = vCard.dataset.vname || '';
      let cardVisibleRows = 0;

      vCard.querySelectorAll('tbody tr').forEach(row => {{
        const matchVendor = (activeVendor === '' || vendorName === activeVendor);
        const matchSearch = q === '' || row.innerText.toLowerCase().includes(q) || vName.includes(q) || vendorName.toLowerCase().includes(q);
        const ok = matchVendor && matchSearch;
        row.style.display = ok ? '' : 'none';
        if (ok) cardVisibleRows++;
      }});

      const cardOk = cardVisibleRows > 0;
      vCard.style.display = cardOk ? '' : 'none';
      if (cardOk) vendorVisibleCards++;
    }});

    vSec.style.display = vendorVisibleCards > 0 ? '' : 'none';
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

function showToast(msg) {{
  let t = document.getElementById('toast');
  if (!t) {{
    t = document.createElement('div');
    t.id = 'toast';
    t.className = 'toast';
    document.body.appendChild(t);
  }}
  t.innerText = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 1500);
}}

document.addEventListener('click', e => {{
  const el = e.target.closest('.model-name');
  if (!el) return;
  const text = el.innerText.trim();
  const notify = () => showToast('已复制: ' + text);
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(text).then(notify).catch(() => {{
      const inp = document.createElement('input');
      inp.value = text;
      document.body.appendChild(inp);
      inp.select();
      document.execCommand('copy');
      document.body.removeChild(inp);
      notify();
    }});
  }} else {{
    const inp = document.createElement('input');
    inp.value = text;
    document.body.appendChild(inp);
    inp.select();
    document.execCommand('copy');
    document.body.removeChild(inp);
    notify();
  }}
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


def deploy_to_server(html_path, target, port=None, key=None, public_url=None, open_browser=True):
    """通过 scp 将 HTML 报告推送到远程服务器。
    target 格式：'host:remote_path' 或 'user@host:remote_path'
    """
    if not target or ":" not in target:
        log("推送跳过：未配置有效部署目标（格式需为 'host:remote_path' 或 'user@host:remote_path'）")
        return False

    host_part, _, path_part = target.rpartition(":")
    log(f"\n正在推送 HTML 报告到远程服务器: {target} ...")

    # 1. 尝试在远程创建目标父目录 (mkdir -p)
    ssh_cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
    if port:
        ssh_cmd.extend(["-p", str(port)])
    if key:
        ssh_cmd.extend(["-i", os.path.expanduser(key)])
    ssh_cmd.extend([host_part, f"mkdir -p $(dirname '{path_part}')"])

    try:
        sub = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
        if sub.returncode != 0:
            err_msg = sub.stderr.strip() or sub.stdout.strip()
            log(f"⚠️ 远程目录预检提示: {err_msg}")
    except Exception as e:
        log(f"⚠️ SSH 目录预检跳过: {e}")

    # 2. 执行 scp 上传
    scp_cmd = ["scp", "-B", "-o", "ConnectTimeout=15"]
    if port:
        scp_cmd.extend(["-P", str(port)])
    if key:
        scp_cmd.extend(["-i", os.path.expanduser(key)])
    scp_cmd.extend([html_path, target])

    try:
        res = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            log(f"✅ 成功推送到服务器: {target}")
            if public_url:
                log(f"🌐 公网访问地址: {public_url}")
                if open_browser:
                    webbrowser.open(public_url)
            return True
        else:
            err = res.stderr.strip() or res.stdout.strip()
            log(f"❌ 推送失败 (scp 退出码 {res.returncode}):\n  {err}")
            log("提示：请确认服务器已配置 SSH 免密登录，并检查端口/私钥路径是否正确。")
            return False
    except FileNotFoundError:
        log("❌ 推送失败：系统中未找到 scp 命令，请确认 OpenSSH 客户端已安装。")
        return False
    except Exception as e:
        log(f"❌ 推送发生异常: {e}")
        return False


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
    ap.add_argument("--no-browser", action="store_true", help="不自动用默认浏览器打开 HTML 报告")
    ap.add_argument("--deploy", action="store_true", help="强制推送到远程服务器")
    ap.add_argument("--no-deploy", action="store_true", help="禁用推送到远程服务器")
    ap.add_argument("--deploy-only", action="store_true", help="不测速，仅将本地已有 HTML 报告推送到服务器")
    ap.add_argument("--deploy-target", default=DEFAULT_DEPLOY_TARGET,
                    help="远程部署目标（如 'aliyun:/var/www/speedtest/index.html'）")
    ap.add_argument("--deploy-port", type=int, default=DEFAULT_DEPLOY_PORT, help="SSH 端口（默认 22）")
    ap.add_argument("--deploy-key", default=DEFAULT_DEPLOY_KEY, help="SSH 私钥路径")
    ap.add_argument("--deploy-url", default=DEFAULT_DEPLOY_URL, help="公网访问 URL（如 'https://example.com/speedtest/'）")
    ap.add_argument("--out", default=None, help="结果 JSON 输出路径（覆盖默认）")
    args = ap.parse_args(argv)

    if args.deploy_only:
        html_path = os.path.join(args.report_dir, "speedtest.html")
        if not os.path.isfile(html_path):
            log(f"错误：本地 HTML 报告不存在: {html_path}，请先运行测速。")
            return 1
        target = args.deploy_target
        if not target:
            log("错误：未配置部署目标。请在 .env 中配置 SPEEDTEST_DEPLOY_TARGET 或通过 --deploy-target 传入。")
            return 1
        ok = deploy_to_server(html_path, target, port=args.deploy_port, key=args.deploy_key,
                              public_url=args.deploy_url, open_browser=not args.no_browser)
        return 0 if ok else 1

    if not args.api_key:
        log("错误：未提供 API key。请在仓库根目录 .env 中配置 LLM_API_KEY，或用 --api-key 传入。")
        return 1

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

    # 报告落盘：默认 data/<技能名>/speedtest.{json,html}（每次运行自动覆盖）
    os.makedirs(args.report_dir, exist_ok=True)
    out_path = args.out or os.path.join(args.report_dir, "speedtest.json")
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log(f"\nJSON 结果: {out_path}")

    if not args.no_html:
        models_dev = fetch_models_dev(proxies)
        params = {"concurrency": args.concurrency, "max_tokens": args.max_tokens}
        html_path = os.path.join(args.report_dir, "speedtest.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(render_html(results, meta, args.base_url, params, total_sec, models_dev=models_dev))
        log(f"HTML 报告: {html_path}")

        deployed = False
        should_deploy = (args.deploy or (bool(args.deploy_target) and not args.no_deploy))
        if should_deploy:
            deployed = deploy_to_server(html_path, args.deploy_target, port=args.deploy_port,
                                        key=args.deploy_key, public_url=args.deploy_url,
                                        open_browser=not args.no_browser)

        if not args.no_browser and not (deployed and args.deploy_url):
            webbrowser.open(Path(html_path).as_uri())
            log("已在默认浏览器打开本地 HTML 报告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
