"""
根据成员列表生成组织架构树 HTML（离线单文件，供抓取流程内部调用）
"""
import json
from datetime import datetime
from html import escape
from pathlib import Path


def _build_tree(members: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    """
    根据 superior -> name 构建树
    返回根节点列表和节点映射
    """
    nodes = []
    name_to_nodes = {}

    for idx, member in enumerate(members):
        node = {
            "node_id": f"n{idx}",
            "name": str(member.get("name", "")).strip(),
            "id": str(member.get("id", "")).strip(),
            "dept_name": str(member.get("deptName", "")).strip(),
            "superior": str(member.get("superior", "")).strip(),
            "member": member,
            "children": [],
            "parent_id": "",
            "is_virtual": bool(member.get("is_virtual", False)),
        }
        nodes.append(node)
        if node["name"]:
            name_to_nodes.setdefault(node["name"], []).append(node)

    roots = []
    node_map = {node["node_id"]: node for node in nodes}

    for node in nodes:
        superior = node["superior"]
        parent = None
        if superior and superior in name_to_nodes:
            # 最小实现：同名上级取第一条
            parent = name_to_nodes[superior][0]

        if parent and parent["node_id"] != node["node_id"]:
            node["parent_id"] = parent["node_id"]
            parent["children"].append(node)
        else:
            roots.append(node)

    return roots, node_map


def _node_search_text(node: dict) -> str:
    """用于前端搜索的文本"""
    member = node.get("member", {})
    return " ".join(
        [
            node.get("name", ""),
            node.get("id", ""),
            node.get("dept_name", ""),
            str(member.get("role_desc", "")),
            str(member.get("bpName", "")),
            str(member.get("workPlaceName", "")),
            str(node.get("superior", "")),
        ]
    ).lower()


def _serialize_nodes_for_frontend(roots: list[dict], node_map: dict[str, dict]) -> tuple[str, str]:
    """序列化前端使用的数据"""
    root_ids = [node["node_id"] for node in roots]
    nodes = []
    for node_id in node_map:
        node = node_map[node_id]
        member = node.get("member", {})
        nodes.append(
            {
                "node_id": node["node_id"],
                "name": node.get("name", ""),
                "id": node.get("id", ""),
                "dept_name": node.get("dept_name", ""),
                "superior": node.get("superior", ""),
                "parent_id": node.get("parent_id", ""),
                "children": [child["node_id"] for child in node.get("children", [])],
                "search_text": _node_search_text(node),
                "is_virtual": bool(node.get("is_virtual", False)),
                "role_desc": str(member.get("role_desc", "")).strip(),
                "bp_name": str(member.get("bpName", "")).strip(),
                "work_place_name": str(member.get("workPlaceName", "")).strip(),
                "user_name": str(member.get("userName", "")).strip(),
                "sex_desc": str(member.get("sex_desc", "")).strip(),
            }
        )

    nodes_json = json.dumps(nodes, ensure_ascii=False).replace("</", "<\\/")
    roots_json = json.dumps(root_ids, ensure_ascii=False)
    return nodes_json, roots_json


def _render_html(roots: list[dict], node_map: dict[str, dict], total_count: int, fetched_date: str) -> str:
    """生成完整 HTML"""
    fetched_date_safe = escape(fetched_date)
    nodes_json, roots_json = _serialize_nodes_for_frontend(roots, node_map)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Teams 组织架构树</title>
  <style>
    :root {{
      --bg: #f4f6fb;
      --bg-soft: #eef2f8;
      --surface: rgba(255, 255, 255, 0.88);
      --surface-strong: #ffffff;
      --surface-muted: #f6f8fc;
      --text: #18212f;
      --muted: #667085;
      --line: #d8dee9;
      --line-strong: #c5cedb;
      --accent: #2f6fed;
      --accent-soft: #e8f0ff;
      --match: #eef6ff;
      --match-line: #73a6ff;
      --active: #dbeafe;
      --active-line: #2563eb;
      --selected: #eef4ff;
      --selected-line: #1d4ed8;
      --virtual-bg: #fff6ea;
      --virtual-line: #f2a766;
      --shadow: 0 18px 50px rgba(21, 34, 50, 0.08);
      --shadow-soft: 0 8px 20px rgba(21, 34, 50, 0.06);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(47, 111, 237, 0.08), transparent 28%),
        linear-gradient(180deg, #fbfcff 0%, var(--bg) 100%);
    }}
    .container {{
      max-width: 1520px;
      margin: 0 auto;
      padding: 18px;
    }}
    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 16px;
      align-items: start;
    }}
    .panel, .detail-panel {{
      background: var(--surface);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}
    .panel {{
      padding: 18px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 28px;
      line-height: 1.2;
      letter-spacing: -0.02em;
      font-weight: 700;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
      color: var(--muted);
      font-size: 13px;
    }}
    .meta-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid rgba(197, 206, 219, 0.7);
      background: rgba(255, 255, 255, 0.75);
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .search-group {{
      display: flex;
      align-items: center;
      flex: 1 1 420px;
      min-width: 260px;
      gap: 8px;
      padding: 8px;
      border-radius: 16px;
      border: 1px solid rgba(197, 206, 219, 0.85);
      background: rgba(255, 255, 255, 0.82);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
    }}
    .search-box {{
      flex: 1;
      min-width: 120px;
      border: none;
      background: transparent;
      outline: none;
      font-size: 14px;
      color: var(--text);
      padding: 4px 2px;
    }}
    .search-box::placeholder {{ color: #98a2b3; }}
    .search-status {{
      white-space: nowrap;
      font-size: 12px;
      color: var(--muted);
      padding: 5px 8px;
      border-radius: 999px;
      background: var(--bg-soft);
    }}
    .drag-control {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-height: 40px;
      padding: 7px 10px;
      border-radius: 14px;
      border: 1px solid rgba(197, 206, 219, 0.85);
      background: rgba(255, 255, 255, 0.82);
      color: var(--muted);
      font-size: 12px;
    }}
    .drag-control label {{
      white-space: nowrap;
      font-weight: 600;
      color: #526074;
    }}
    .drag-control input[type="range"] {{
      width: 120px;
      accent-color: var(--accent);
    }}
    .drag-value {{
      min-width: 42px;
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--text);
      font-weight: 600;
    }}
    .filter-select {{
      min-height: 40px;
      max-width: 240px;
      border: 1px solid rgba(197, 206, 219, 0.9);
      background: rgba(255, 255, 255, 0.82);
      color: var(--text);
      border-radius: 12px;
      font-size: 13px;
      padding: 8px 10px;
      outline: none;
    }}
    .btn-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .btn {{
      border: 1px solid rgba(197, 206, 219, 0.9);
      background: rgba(255, 255, 255, 0.82);
      color: var(--text);
      border-radius: 12px;
      font-size: 13px;
      line-height: 1;
      min-height: 40px;
      padding: 10px 12px;
      cursor: pointer;
      transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    }}
    .btn:hover {{
      background: #ffffff;
      border-color: #b9c5d8;
      transform: translateY(-1px);
    }}
    .btn:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
      transform: none;
    }}
    .btn.is-active {{
      background: var(--accent-soft);
      border-color: rgba(47, 111, 237, 0.35);
      color: #1742a0;
    }}
    .tip {{
      margin-bottom: 12px;
      font-size: 12px;
      line-height: 1.6;
      color: var(--muted);
    }}
    .canvas-wrap {{
      border: 1px solid rgba(216, 222, 233, 0.9);
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(244,247,252,0.95) 100%),
        linear-gradient(90deg, rgba(47,111,237,0.02) 1px, transparent 1px),
        linear-gradient(rgba(47,111,237,0.02) 1px, transparent 1px);
      background-size: auto, 24px 24px, 24px 24px;
      height: 76vh;
      min-height: 560px;
      overflow: hidden;
      position: relative;
      cursor: default;
    }}
    .canvas-wrap.drag-ready {{ cursor: grab; }}
    .canvas-wrap.dragging {{ cursor: grabbing; }}
    .canvas-wrap.dragging, .canvas-wrap.dragging * {{
      user-select: none !important;
      -webkit-user-select: none !important;
      cursor: grabbing;
    }}
    #treeSvg {{
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
    }}
    .link {{
      stroke: #aeb8c7;
      stroke-width: 1.35;
      fill: none;
      opacity: 0.92;
    }}
    .node-card {{
      fill: #ffffff;
      stroke: #d7ddea;
      stroke-width: 1.15;
      rx: 18;
      ry: 18;
      filter: drop-shadow(0 10px 22px rgba(29, 78, 216, 0.06));
    }}
    .node-bg-band {{
      fill: #f8faff;
    }}
    .node.node-match .node-card {{
      fill: var(--match);
      stroke: var(--match-line);
      stroke-width: 1.3;
    }}
    .node.node-active-match .node-card {{
      fill: var(--active);
      stroke: var(--active-line);
      stroke-width: 1.6;
    }}
    .node.node-selected .node-card {{
      fill: var(--selected);
      stroke: var(--selected-line);
      stroke-width: 1.7;
    }}
    .node.node-selected.node-active-match .node-card {{
      stroke: #1e40af;
    }}
    .node.node-virtual .node-card {{
      fill: var(--virtual-bg);
      stroke: var(--virtual-line);
      stroke-dasharray: 6 4;
    }}
    .node.node-virtual .node-bg-band {{
      fill: rgba(242, 167, 102, 0.12);
    }}
    .node text {{
      user-select: text;
      -webkit-user-select: text;
      cursor: text;
      pointer-events: none;
    }}
    .node .node-name {{
      font-size: 13px;
      font-weight: 700;
      fill: #162033;
      letter-spacing: -0.01em;
    }}
    .node .node-dept {{
      font-size: 10.5px;
      font-weight: 500;
      fill: #526074;
    }}
    .node .node-badge {{
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.03em;
      fill: #8a5a1f;
    }}
    .node-main-hitbox, .node-toggle-hitbox {{
      fill: transparent;
      pointer-events: all;
    }}
    .node-main-hitbox {{ cursor: pointer; }}
    .node-toggle-hitbox {{ cursor: pointer; }}
    .node-toggle-bg {{
      fill: #ffffff;
      stroke: #b7c4d8;
      stroke-width: 1.1;
    }}
    .node-toggle-mark {{
      font-size: 13px;
      font-weight: 700;
      fill: #2858c5;
      text-anchor: middle;
      dominant-baseline: middle;
      pointer-events: none;
    }}
    .detail-panel {{
      position: sticky;
      top: 18px;
      padding: 18px;
      min-height: 320px;
    }}
    .detail-title {{
      margin: 0 0 6px;
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: -0.02em;
    }}
    .detail-subtitle {{
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .detail-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }}
    .detail-badge {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--bg-soft);
      color: #415166;
      font-size: 12px;
      border: 1px solid rgba(197, 206, 219, 0.75);
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
    }}
    .detail-item {{
      padding: 12px 13px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(216, 222, 233, 0.8);
      box-shadow: var(--shadow-soft);
    }}
    .detail-label {{
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #7a8798;
      text-transform: uppercase;
    }}
    .detail-value {{
      font-size: 13px;
      line-height: 1.6;
      color: var(--text);
      word-break: break-word;
    }}
    .empty-note {{
      color: #8a95a5;
    }}
    .hover-trail {{
      position: absolute;
      display: none;
      max-width: 320px;
      min-width: 210px;
      padding: 12px 13px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid rgba(197, 206, 219, 0.8);
      box-shadow: 0 14px 32px rgba(15, 23, 42, 0.14);
      font-size: 12px;
      line-height: 1.55;
      color: var(--text);
      pointer-events: none;
      z-index: 5;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }}
    .hover-trail.show {{ display: block; }}
    .trail-title {{
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 11px;
    }}
    .trail-item {{
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .trail-empty {{ color: #8a95a5; }}
    @media (max-width: 1180px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}
      .detail-panel {{
        position: static;
      }}
    }}
    @media (max-width: 720px) {{
      .container {{ padding: 12px; }}
      .panel, .detail-panel {{ border-radius: 20px; }}
      h1 {{ font-size: 24px; }}
      .canvas-wrap {{ min-height: 420px; height: 58vh; }}
      .toolbar {{ align-items: stretch; }}
      .search-group {{ flex: 1 1 100%; width: 100%; }}
      .btn-row {{ width: 100%; }}
      .btn {{ flex: 1 1 auto; min-width: 88px; min-height: 44px; }}
      .detail-panel {{
        border-radius: 20px 20px 0 0;
      }}
    }}
    @media (hover: none) {{
      .hover-trail {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="shell">
      <div class="panel">
        <h1>Teams 组织架构树</h1>
        <div class="meta-row">
          <span class="meta-chip">数据抓取日期：{fetched_date_safe}</span>
          <span class="meta-chip">总人数：{total_count}</span>
        </div>
        <div class="toolbar">
          <div class="search-group">
            <select id="lineFilterSelect" class="filter-select" aria-label="筛选业务条线"></select>
            <input id="searchInput" class="search-box" placeholder="搜索姓名 / 工号 / 部门" />
            <button id="clearSearchBtn" class="btn" type="button">清空</button>
            <span id="searchStatus" class="search-status">0 / 0</span>
          </div>
          <div class="btn-row">
            <button id="prevMatchBtn" class="btn" type="button">上一个</button>
            <button id="nextMatchBtn" class="btn" type="button">下一个</button>
            <div class="drag-control">
              <label for="dragSensitivityInput">拖拽灵敏度</label>
              <input id="dragSensitivityInput" type="range" min="0.6" max="2.4" step="0.1" value="1.4" />
              <span id="dragSensitivityValue" class="drag-value">1.4x</span>
            </div>
            <button id="resetViewBtn" class="btn" type="button">重置视图</button>
          </div>
        </div>
        <div class="tip">说明：节点卡片仅展示姓名与部门；点击卡片主体可选中节点，点击右上角控件展开或收起直属下级；拖动画布仅在空白背景区域触发；搜索会高亮姓名 / 工号 / 部门命中，切换结果时再自动居中。</div>
        <div id="canvasWrap" class="canvas-wrap drag-ready">
          <svg id="treeSvg" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid meet">
            <g id="viewport"></g>
          </svg>
          <div id="hoverTrail" class="hover-trail" aria-hidden="true"></div>
        </div>
      </div>

      <aside id="detailPanel" class="detail-panel" aria-live="polite">
        <div id="detailContent"></div>
      </aside>
    </div>
  </div>

  <script>
    const NODES = {nodes_json};
    const ROOT_IDS = {roots_json};
    const DENSITY_PRESETS = {{
      compact: {{ NODE_W: 156, NODE_H: 48, H_STEP: 184, V_STEP: 62, ROOT_GAP_UNITS: 0.12, SUBTREE_GAP_UNITS: 0.04 }},
    }};
    const HOVER_DELAY_MS = 1000;
    const SEARCH_DEBOUNCE_MS = 180;
    const DRAG_THRESHOLD = 4;

    const byId = new Map(NODES.map((n) => [n.node_id, n]));
    const expanded = new Set();
    const highlightMatches = new Set();
    const rootDescendantsCache = new Map();

    let density = "compact";
    let scale = 1;
    let tx = 40;
    let ty = 60;
    let selectedNodeId = ROOT_IDS[0] || (NODES[0] ? NODES[0].node_id : "");
    let latestPositions = new Map();
    let searchMatches = [];
    let activeSearchIndex = -1;
    let searchDebounceTimer = null;
    let hoverTimer = null;
    let hoverNodeId = "";
    let hoverPoint = {{ x: 0, y: 0 }};
    let pendingDrag = null;
    let dragging = false;
    let dragSensitivity = 1.4;
    let currentRootFilter = "all";

    const svg = document.getElementById("treeSvg");
    const viewport = document.getElementById("viewport");
    const canvasWrap = document.getElementById("canvasWrap");
    const lineFilterSelect = document.getElementById("lineFilterSelect");
    const searchInput = document.getElementById("searchInput");
    const searchStatus = document.getElementById("searchStatus");
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    const prevMatchBtn = document.getElementById("prevMatchBtn");
    const nextMatchBtn = document.getElementById("nextMatchBtn");
    const resetViewBtn = document.getElementById("resetViewBtn");
    const dragSensitivityInput = document.getElementById("dragSensitivityInput");
    const dragSensitivityValue = document.getElementById("dragSensitivityValue");
    const hoverTrail = document.getElementById("hoverTrail");
    const detailContent = document.getElementById("detailContent");

    function cfg() {{
      return DENSITY_PRESETS.compact;
    }}

    function truncate(text, maxLen = 22) {{
      if (!text) return "-";
      return text.length > maxLen ? `${{text.slice(0, maxLen)}}…` : text;
    }}

    function getVisibleRootIds() {{
      return currentRootFilter === "all" ? ROOT_IDS : ROOT_IDS.filter((rootId) => rootId === currentRootFilter);
    }}

    function buildRootDescendantSet(rootId) {{
      if (rootDescendantsCache.has(rootId)) return rootDescendantsCache.get(rootId);
      const visited = new Set();
      const stack = [rootId];
      while (stack.length) {{
        const currentId = stack.pop();
        if (!currentId || visited.has(currentId)) continue;
        visited.add(currentId);
        const currentNode = byId.get(currentId);
        if (!currentNode) continue;
        (currentNode.children || []).forEach((childId) => stack.push(childId));
      }}
      rootDescendantsCache.set(rootId, visited);
      return visited;
    }}

    function isNodeVisibleInFilter(nodeId) {{
      if (currentRootFilter === "all") return true;
      return buildRootDescendantSet(currentRootFilter).has(nodeId);
    }}

    function getFilteredNodes() {{
      return NODES.filter((node) => isNodeVisibleInFilter(node.node_id));
    }}

    function escapeHtml(text) {{
      return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function clearHoverTrailTimer() {{
      if (!hoverTimer) return;
      clearTimeout(hoverTimer);
      hoverTimer = null;
    }}

    function hideHoverTrail() {{
      clearHoverTrailTimer();
      hoverTrail.classList.remove("show");
      hoverTrail.setAttribute("aria-hidden", "true");
      hoverTrail.innerHTML = "";
    }}

    function listAncestorTrail(nodeId) {{
      const trail = [];
      let current = byId.get(nodeId);
      while (current && current.parent_id) {{
        const parent = byId.get(current.parent_id);
        if (!parent) break;
        trail.push(parent);
        current = parent;
      }}
      return trail.reverse();
    }}

    function renderTrailHtml(nodeId) {{
      const trail = listAncestorTrail(nodeId);
      if (!trail.length) {{
        return '<div class="trail-empty">无上游祖先节点</div>';
      }}
      return trail
        .map((node) => `<div class="trail-item">${{escapeHtml(node.name || "-")}} · ${{escapeHtml(node.dept_name || "-")}}</div>`)
        .join("");
    }}

    function placeHoverTrail(clientX, clientY) {{
      const wrapRect = canvasWrap.getBoundingClientRect();
      let left = clientX - wrapRect.left + 12;
      let top = clientY - wrapRect.top + 14;
      const maxLeft = canvasWrap.clientWidth - hoverTrail.offsetWidth - 10;
      const maxTop = canvasWrap.clientHeight - hoverTrail.offsetHeight - 10;
      left = Math.max(10, Math.min(left, maxLeft));
      top = Math.max(10, Math.min(top, maxTop));
      hoverTrail.style.left = `${{left}}px`;
      hoverTrail.style.top = `${{top}}px`;
    }}

    function showHoverTrail(nodeId, clientX, clientY) {{
      if (window.matchMedia("(hover: none)").matches) return;
      hoverTrail.innerHTML = `<div class="trail-title">上游祖先链（根 -> 父级）</div>${{renderTrailHtml(nodeId)}}`;
      hoverTrail.classList.add("show");
      hoverTrail.setAttribute("aria-hidden", "false");
      placeHoverTrail(clientX, clientY);
    }}

    function scheduleHoverTrail(nodeId, clientX, clientY) {{
      if (window.matchMedia("(hover: none)").matches) return;
      clearHoverTrailTimer();
      hoverNodeId = nodeId;
      hoverPoint = {{ x: clientX, y: clientY }};
      hoverTimer = setTimeout(() => {{
        if (hoverNodeId !== nodeId || dragging) return;
        showHoverTrail(nodeId, hoverPoint.x, hoverPoint.y);
      }}, HOVER_DELAY_MS);
    }}

    function updateMatchButtons() {{
      const total = searchMatches.length;
      const hasMatches = total > 0;
      prevMatchBtn.disabled = !hasMatches;
      nextMatchBtn.disabled = !hasMatches;
      searchStatus.textContent = hasMatches && activeSearchIndex >= 0
        ? `${{activeSearchIndex + 1}} / ${{total}}`
        : `0 / ${{total}}`;
    }}

    function isActiveMatch(nodeId) {{
      if (activeSearchIndex < 0) return false;
      return searchMatches[activeSearchIndex] === nodeId;
    }}

    function findNameMatches(keyword) {{
      const exact = [];
      const includes = [];
      getFilteredNodes().forEach((node) => {{
        const name = (node.name || "").trim().toLowerCase();
        if (!name) return;
        if (name === keyword) {{
          exact.push(node.node_id);
          return;
        }}
        if (name.includes(keyword)) {{
          includes.push(node.node_id);
        }}
      }});
      return exact.length ? exact : includes;
    }}

    function expandAncestors(nodeId) {{
      let current = byId.get(nodeId);
      while (current && current.parent_id) {{
        expanded.add(current.parent_id);
        current = byId.get(current.parent_id);
      }}
    }}

    function getVisibleChildren(nodeId) {{
      const node = byId.get(nodeId);
      if (!node) return [];
      if (!expanded.has(nodeId)) return [];
      return node.children || [];
    }}

    function computeHeight(nodeId, heightCache) {{
      const {{ SUBTREE_GAP_UNITS }} = cfg();
      if (heightCache.has(nodeId)) return heightCache.get(nodeId);
      const children = getVisibleChildren(nodeId);
      if (!children.length) {{
        heightCache.set(nodeId, 1);
        return 1;
      }}
      let sum = 0;
      children.forEach((childId, idx) => {{
        sum += computeHeight(childId, heightCache);
        if (idx > 0) sum += SUBTREE_GAP_UNITS;
      }});
      heightCache.set(nodeId, Math.max(1, sum));
      return heightCache.get(nodeId);
    }}

    function layoutTree() {{
      const {{ H_STEP, V_STEP, ROOT_GAP_UNITS }} = cfg();
      const heightCache = new Map();
      const positions = new Map();
      const edges = [];

      function assign(nodeId, topUnit, depth) {{
        const heightUnits = computeHeight(nodeId, heightCache);
        const centerUnit = topUnit + heightUnits / 2;
        positions.set(nodeId, {{
          x: depth * H_STEP,
          y: centerUnit * V_STEP,
        }});

        const children = getVisibleChildren(nodeId);
        let cursor = topUnit;
        children.forEach((childId, idx) => {{
          const childH = computeHeight(childId, heightCache);
          assign(childId, cursor, depth + 1);
          edges.push([nodeId, childId]);
          cursor += childH;
          if (idx < children.length - 1) cursor += cfg().SUBTREE_GAP_UNITS;
        }});
      }}

      let cursor = 0;
      const visibleRootIds = getVisibleRootIds();
      visibleRootIds.forEach((rootId, idx) => {{
        const rootH = computeHeight(rootId, heightCache);
        assign(rootId, cursor, 0);
        cursor += rootH;
        if (idx < visibleRootIds.length - 1) cursor += ROOT_GAP_UNITS;
      }});

      return {{ positions, edges }};
    }}

    function applyTransform() {{
      viewport.setAttribute("transform", `translate(${{tx}} ${{ty}}) scale(${{scale}})`);
    }}

    function centerNode(nodeId) {{
      const pos = latestPositions.get(nodeId);
      if (!pos) return;
      const {{ NODE_W }} = cfg();
      const targetX = (pos.x + NODE_W / 2) * scale;
      const targetY = pos.y * scale;
      tx = canvasWrap.clientWidth / 2 - targetX;
      ty = canvasWrap.clientHeight / 2 - targetY;
      applyTransform();
    }}

    function focusNode(nodeId, shouldCenter = false) {{
      if (!byId.has(nodeId)) return;
      selectedNodeId = nodeId;
      expandAncestors(nodeId);
      render();
      if (shouldCenter) centerNode(nodeId);
    }}

    function updateDetailPanel() {{
      const node = byId.get(selectedNodeId);
      if (!node) {{
        detailContent.innerHTML = `
          <h2 class="detail-title">未选中节点</h2>
          <p class="detail-subtitle">点击任意节点卡片主体查看详细信息。</p>
        `;
        return;
      }}

      const trail = listAncestorTrail(node.node_id);
      const trailText = trail.length
        ? trail.map((item) => `${{item.name || "-"}}（${{item.dept_name || "-"}}）`).join(" → ")
        : "当前节点为根节点";
      const childCount = (node.children || []).length;
      const virtualText = node.is_virtual
        ? "该节点由补齐逻辑生成，用于承接当前数据集中缺失的直属上级。"
        : "真实成员节点";
      const badges = [
        node.is_virtual ? "虚拟节点" : "真实成员",
        node.role_desc || "未标注角色",
        `${{childCount}} 个直属下级`,
      ];

      detailContent.innerHTML = `
        <h2 class="detail-title">${{escapeHtml(node.name || "未命名")}}</h2>
        <p class="detail-subtitle">${{escapeHtml(node.dept_name || "未填写部门")}}</p>
        <div class="detail-badges">
          ${{badges.map((badge) => `<span class="detail-badge">${{escapeHtml(badge)}}</span>`).join("")}}
        </div>
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">工号</span><div class="detail-value">${{escapeHtml(node.id || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">直属上级</span><div class="detail-value">${{escapeHtml(node.superior || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">角色</span><div class="detail-value">${{escapeHtml(node.role_desc || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">办公地点</span><div class="detail-value">${{escapeHtml(node.work_place_name || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">BP</span><div class="detail-value">${{escapeHtml(node.bp_name || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">账号</span><div class="detail-value">${{escapeHtml(node.user_name || "-")}}</div></div>
          <div class="detail-item"><span class="detail-label">祖先链</span><div class="detail-value">${{escapeHtml(trailText)}}</div></div>
          <div class="detail-item"><span class="detail-label">虚拟节点说明</span><div class="detail-value">${{escapeHtml(virtualText)}}</div></div>
        </div>
      `;
    }}

    function toggleNode(nodeId) {{
      if (expanded.has(nodeId)) expanded.delete(nodeId);
      else expanded.add(nodeId);
      render();
    }}

    function setDensity() {{
      density = "compact";
      render();
      if (selectedNodeId) centerNode(selectedNodeId);
    }}

    function renderNode(node, pos) {{
      const {{ NODE_W, NODE_H }} = cfg();
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const hasChildren = (node.children || []).length > 0;
      const classNames = ["node"];
      if (node.is_virtual) classNames.push("node-virtual");
      if (highlightMatches.has(node.node_id)) classNames.push("node-match");
      if (isActiveMatch(node.node_id)) classNames.push("node-active-match");
      if (selectedNodeId === node.node_id) classNames.push("node-selected");
      g.setAttribute("class", classNames.join(" "));
      g.setAttribute("transform", `translate(${{pos.x}} ${{pos.y - NODE_H / 2}})`);

      const card = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      card.setAttribute("class", "node-card");
      card.setAttribute("width", NODE_W);
      card.setAttribute("height", NODE_H);
      g.appendChild(card);

      const band = document.createElementNS("http://www.w3.org/2000/svg", "path");
      band.setAttribute("class", "node-bg-band");
      band.setAttribute("d", `M 18 1 H ${{NODE_W - 18}} A 17 17 0 0 1 ${{NODE_W - 1}} 18 V 22 H 1 V 18 A 17 17 0 0 1 18 1 Z`);
      g.appendChild(band);

      const mainHitbox = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      mainHitbox.setAttribute("class", "node-main-hitbox");
      mainHitbox.setAttribute("x", 0);
      mainHitbox.setAttribute("y", 0);
      mainHitbox.setAttribute("width", hasChildren ? NODE_W - 24 : NODE_W);
      mainHitbox.setAttribute("height", NODE_H);
      g.appendChild(mainHitbox);

      const name = document.createElementNS("http://www.w3.org/2000/svg", "text");
      name.setAttribute("x", 10);
      name.setAttribute("y", 17);
      name.setAttribute("class", "node-name");
      name.textContent = truncate(node.name || "-", 10);
      g.appendChild(name);

      const dept = document.createElementNS("http://www.w3.org/2000/svg", "text");
      dept.setAttribute("x", 10);
      dept.setAttribute("y", 35);
      dept.setAttribute("class", "node-dept");
      dept.textContent = truncate(node.dept_name || "未填写部门", 12);
      g.appendChild(dept);

      if (node.is_virtual) {{
        const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
        badge.setAttribute("x", NODE_W - 10);
        badge.setAttribute("y", 17);
        badge.setAttribute("text-anchor", "end");
        badge.setAttribute("class", "node-badge");
        badge.textContent = "V";
        g.appendChild(badge);
      }}

      if (hasChildren) {{
        const toggleBg = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        toggleBg.setAttribute("class", "node-toggle-bg");
        toggleBg.setAttribute("cx", NODE_W - 13);
        toggleBg.setAttribute("cy", 13);
        toggleBg.setAttribute("r", 10);
        g.appendChild(toggleBg);

        const toggleHitbox = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        toggleHitbox.setAttribute("class", "node-toggle-hitbox");
        toggleHitbox.setAttribute("cx", NODE_W - 13);
        toggleHitbox.setAttribute("cy", 13);
        toggleHitbox.setAttribute("r", 14);
        g.appendChild(toggleHitbox);

        const toggleMark = document.createElementNS("http://www.w3.org/2000/svg", "text");
        toggleMark.setAttribute("x", NODE_W - 13);
        toggleMark.setAttribute("y", 13);
        toggleMark.setAttribute("class", "node-toggle-mark");
        toggleMark.textContent = expanded.has(node.node_id) ? "−" : "+";
        g.appendChild(toggleMark);

        toggleHitbox.addEventListener("click", (e) => {{
          e.stopPropagation();
          hideHoverTrail();
          toggleNode(node.node_id);
        }});
      }}

      mainHitbox.addEventListener("click", (e) => {{
        e.stopPropagation();
        hideHoverTrail();
        focusNode(node.node_id, false);
      }});

      g.addEventListener("mouseenter", (e) => {{
        scheduleHoverTrail(node.node_id, e.clientX, e.clientY);
      }});
      g.addEventListener("mousemove", (e) => {{
        hoverPoint = {{ x: e.clientX, y: e.clientY }};
        if (hoverNodeId === node.node_id && hoverTrail.classList.contains("show")) {{
          placeHoverTrail(e.clientX, e.clientY);
        }}
      }});
      g.addEventListener("mouseleave", () => {{
        if (hoverNodeId === node.node_id) hoverNodeId = "";
        hideHoverTrail();
      }});

      return g;
    }}

    function render() {{
      hoverNodeId = "";
      hideHoverTrail();
      const {{ positions, edges }} = layoutTree();
      latestPositions = positions;
      while (viewport.firstChild) viewport.removeChild(viewport.firstChild);

      const {{ NODE_W }} = cfg();
      edges.forEach(([fromId, toId]) => {{
        const from = positions.get(fromId);
        const to = positions.get(toId);
        if (!from || !to) return;
        const sx = from.x + NODE_W;
        const sy = from.y;
        const tx2 = to.x;
        const ty2 = to.y;
        const cx = sx + (tx2 - sx) * 0.44;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "link");
        path.setAttribute("d", `M ${{sx}} ${{sy}} C ${{cx}} ${{sy}}, ${{cx}} ${{ty2}}, ${{tx2}} ${{ty2}}`);
        viewport.appendChild(path);
      }});

      getFilteredNodes().forEach((node) => {{
        const pos = positions.get(node.node_id);
        if (!pos) return;
        viewport.appendChild(renderNode(node, pos));
      }});

      applyTransform();
      updateDetailPanel();
      updateMatchButtons();
    }}

    function applySearch(keyword, options = {{ centerOnActive: false, preserveActive: false }}) {{
      const kw = (keyword || "").trim().toLowerCase();
      const previousActiveNodeId = options.preserveActive && activeSearchIndex >= 0 ? searchMatches[activeSearchIndex] : "";
      highlightMatches.clear();
      searchMatches = [];
      activeSearchIndex = -1;

      if (!kw) {{
        render();
        return;
      }}

      getFilteredNodes().forEach((node) => {{
        if ((node.search_text || "").includes(kw)) {{
          highlightMatches.add(node.node_id);
          expandAncestors(node.node_id);
        }}
      }});

      searchMatches = findNameMatches(kw);
      if (!searchMatches.length) {{
        render();
        return;
      }}

      if (previousActiveNodeId) {{
        const existingIndex = searchMatches.indexOf(previousActiveNodeId);
        activeSearchIndex = existingIndex >= 0 ? existingIndex : 0;
      }} else {{
        activeSearchIndex = 0;
      }}

      const activeNodeId = searchMatches[activeSearchIndex];
      if (activeNodeId) expandAncestors(activeNodeId);
      render();
      if (options.centerOnActive && activeNodeId) {{
        focusNode(activeNodeId, true);
      }}
    }}

    function scheduleSearch(keyword) {{
      if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {{
        applySearch(keyword, {{ centerOnActive: false, preserveActive: true }});
      }}, SEARCH_DEBOUNCE_MS);
    }}

    function switchMatch(step) {{
      if (!searchMatches.length) return;
      activeSearchIndex = (activeSearchIndex + step + searchMatches.length) % searchMatches.length;
      const nodeId = searchMatches[activeSearchIndex];
      if (!nodeId) return;
      expandAncestors(nodeId);
      selectedNodeId = nodeId;
      render();
      centerNode(nodeId);
    }}

    function clearSearch() {{
      searchInput.value = "";
      if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
      applySearch("", {{ centerOnActive: false, preserveActive: false }});
    }}

    function resetView() {{
      scale = 1;
      tx = 40;
      ty = 60;
      applyTransform();
    }}

    function clearNativeSelection() {{
      const selection = window.getSelection();
      if (selection && selection.removeAllRanges) {{
        selection.removeAllRanges();
      }}
    }}

    function getSvgPoint(clientX, clientY) {{
      const point = svg.createSVGPoint();
      point.x = clientX;
      point.y = clientY;
      const ctm = svg.getScreenCTM();
      if (!ctm) return {{ x: 0, y: 0 }};
      return point.matrixTransform(ctm.inverse());
    }}

    function syncSelectionToFilter() {{
      if (selectedNodeId && isNodeVisibleInFilter(selectedNodeId)) return;
      selectedNodeId = getVisibleRootIds()[0] || (getFilteredNodes()[0] ? getFilteredNodes()[0].node_id : "");
    }}

    function populateRootFilterOptions() {{
      lineFilterSelect.innerHTML = [
        '<option value="all">全部业务条线</option>',
        ...ROOT_IDS.map((rootId) => {{
          const node = byId.get(rootId);
          const name = node ? `${{node.name || "未命名"}} · ${{node.dept_name || "未填写部门"}}` : rootId;
          return `<option value="${{escapeHtml(rootId)}}">${{escapeHtml(name)}}</option>`;
        }}),
      ].join("");
      lineFilterSelect.value = currentRootFilter;
    }}

    function applyRootFilter(rootId) {{
      currentRootFilter = rootId || "all";
      highlightMatches.clear();
      searchMatches = [];
      activeSearchIndex = -1;
      syncSelectionToFilter();
      if (searchInput.value.trim()) {{
        applySearch(searchInput.value, {{ centerOnActive: false, preserveActive: false }});
        return;
      }}
      render();
      if (selectedNodeId) centerNode(selectedNodeId);
    }}

    function updateDragSensitivityLabel() {{
      dragSensitivityValue.textContent = `${{dragSensitivity.toFixed(1)}}x`;
    }}

    function beginPointerDrag(e) {{
      if (e.button !== 0) return;
      if (e.target !== svg) return;
      e.preventDefault();
      pendingDrag = {{ startX: e.clientX, startY: e.clientY, lastX: e.clientX, lastY: e.clientY }};
      canvasWrap.classList.add("drag-ready");
    }}

    function movePointerDrag(e) {{
      if (!pendingDrag && !dragging) return;
      const state = pendingDrag || {{ lastX: e.clientX, lastY: e.clientY, startX: e.clientX, startY: e.clientY }};
      const dxFromStart = e.clientX - state.startX;
      const dyFromStart = e.clientY - state.startY;

      if (!dragging) {{
        if (Math.hypot(dxFromStart, dyFromStart) < DRAG_THRESHOLD) return;
        dragging = true;
        hideHoverTrail();
        clearNativeSelection();
        canvasWrap.classList.remove("drag-ready");
        canvasWrap.classList.add("dragging");
      }}

      e.preventDefault();
      tx += ((e.clientX - state.lastX) / scale) * dragSensitivity;
      ty += ((e.clientY - state.lastY) / scale) * dragSensitivity;
      state.lastX = e.clientX;
      state.lastY = e.clientY;
      pendingDrag = state;
      applyTransform();
    }}

    function endPointerDrag() {{
      pendingDrag = null;
      dragging = false;
      canvasWrap.classList.remove("dragging");
      canvasWrap.classList.add("drag-ready");
    }}

    lineFilterSelect.addEventListener("change", (e) => applyRootFilter(e.target.value));
    searchInput.addEventListener("input", (e) => scheduleSearch(e.target.value));
    clearSearchBtn.addEventListener("click", clearSearch);
    prevMatchBtn.addEventListener("click", () => switchMatch(-1));
    nextMatchBtn.addEventListener("click", () => switchMatch(1));
    resetViewBtn.addEventListener("click", resetView);
    dragSensitivityInput.addEventListener("input", (e) => {{
      dragSensitivity = Number(e.target.value) || 1;
      updateDragSensitivityLabel();
    }});

    svg.addEventListener("wheel", (e) => {{
      e.preventDefault();
      const pointer = getSvgPoint(e.clientX, e.clientY);
      const worldX = (pointer.x - tx) / scale;
      const worldY = (pointer.y - ty) / scale;
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      const nextScale = Math.max(0.35, Math.min(2.8, scale * factor));
      tx = pointer.x - worldX * nextScale;
      ty = pointer.y - worldY * nextScale;
      scale = nextScale;
      applyTransform();
    }}, {{ passive: false }});

    svg.addEventListener("mousedown", beginPointerDrag);
    window.addEventListener("mousemove", movePointerDrag);
    window.addEventListener("mouseup", endPointerDrag);

    NODES.forEach((node) => {{
      if (!node.parent_id) expanded.add(node.node_id);
    }});

    populateRootFilterOptions();
    syncSelectionToFilter();
    updateDragSensitivityLabel();
    render();
  </script>
</body>
</html>
"""


def render_org_tree_html(members: list[dict], output_path: str, fetched_date: str = "") -> str:
    """
    根据成员列表生成组织树 HTML（内部调用）
    """
    if not isinstance(members, list):
        raise ValueError("members 必须是 list[dict] 结构")

    normalized_members = [item for item in members if isinstance(item, dict)]
    roots, node_map = _build_tree(normalized_members)

    used_date = fetched_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = _render_html(
        roots=roots,
        node_map=node_map,
        total_count=len(normalized_members),
        fetched_date=used_date,
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")
    return output_file.as_posix()


if __name__ == "__main__":
    raise SystemExit("该脚本仅供内部调用，请使用 fetch_group_members.py 进行抓取并自动生成HTML。")
