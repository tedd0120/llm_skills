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
    return " ".join(
        [
            node.get("name", ""),
            node.get("id", ""),
            node.get("dept_name", ""),
        ]
    ).lower()


def _serialize_nodes_for_frontend(roots: list[dict], node_map: dict[str, dict]) -> tuple[str, str]:
    """序列化前端使用的数据"""
    root_ids = [node["node_id"] for node in roots]
    nodes = []
    for node_id in node_map:
        node = node_map[node_id]
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
      --bg: #f5f5f7;
      --surface: #ffffff;
      --surface-soft: #fafafc;
      --text: #1d1d1f;
      --muted: #6e6e73;
      --line: #d2d2d7;
      --accent: #0071e3;
      --highlight: #d8ecff;
      --shadow: rgba(17, 17, 17, 0.08);
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
      background: linear-gradient(180deg, #fbfbfd 0%, var(--bg) 100%);
      color: var(--text);
    }}
    .container {{
      max-width: 1240px;
      margin: 16px auto;
      padding: 0 14px 20px;
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid #ececf0;
      border-radius: 20px;
      padding: 14px;
      box-shadow: 0 10px 26px var(--shadow);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 22px;
      font-weight: 600;
      letter-spacing: -0.01em;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      color: var(--muted);
      margin-bottom: 10px;
      font-size: 13px;
    }}
    .toolbar {{
      display: flex;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }}
    .search-box {{
      width: 100%;
      max-width: 340px;
      border: 1px solid #dcdce2;
      border-radius: 12px;
      padding: 9px 11px;
      font-size: 13px;
      background: var(--surface-soft);
      outline: none;
    }}
    .search-box:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.16);
      background: var(--surface);
    }}
    .canvas-wrap {{
      margin-top: 8px;
      border: 1px solid #e4e4ea;
      border-radius: 16px;
      background: linear-gradient(180deg, #fbfbfd 0%, #f3f4f7 100%);
      height: 72vh;
      min-height: 540px;
      overflow: hidden;
      position: relative;
      cursor: grab;
    }}
    .canvas-wrap.dragging {{
      cursor: grabbing;
    }}
    #treeSvg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .tip {{
      font-size: 12px;
      color: var(--muted);
    }}
    .btn {{
      border: 1px solid #dcdce2;
      background: var(--surface-soft);
      color: #1d1d1f;
      border-radius: 10px;
      font-size: 12px;
      padding: 6px 10px;
      cursor: pointer;
    }}
    .btn:hover {{
      background: #f0f0f4;
    }}
    .btn:disabled {{
      opacity: 0.45;
      cursor: not-allowed;
    }}
    .link {{
      stroke: #b4b4bd;
      stroke-width: 1.15;
      fill: none;
    }}
    .node rect {{
      fill: #ffffff;
      stroke: #d7d7df;
      stroke-width: 1.05;
      rx: 12;
      ry: 12;
    }}
    .node .name {{
      font-size: 12.5px;
      font-weight: 600;
      fill: #1d1d1f;
    }}
    .node .meta {{
      font-size: 10.5px;
      fill: #5e5e66;
    }}
    .node text {{
      user-select: text;
      -webkit-user-select: text;
      cursor: text;
    }}
    .node.highlight rect {{
      fill: var(--highlight);
      stroke: #3395ff;
      stroke-width: 1.25;
    }}
    .node.virtual rect {{
      fill: #fff6ed;
      stroke: #e89b46;
      stroke-dasharray: 4 3;
    }}
    .node.virtual .name {{
      fill: #8b4a18;
    }}
    .node.expandable .toggle {{
      fill: #0a67c8;
      font-size: 11px;
      font-weight: 600;
    }}
    .hover-trail {{
      position: absolute;
      display: none;
      max-width: 300px;
      min-width: 190px;
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid #dcdce3;
      border-radius: 12px;
      box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
      padding: 10px 11px;
      font-size: 12px;
      color: #2b2b2f;
      line-height: 1.45;
      pointer-events: none;
      z-index: 5;
      backdrop-filter: blur(8px);
    }}
    .hover-trail.show {{
      display: block;
    }}
    .trail-title {{
      font-size: 11px;
      color: #73737b;
      margin-bottom: 6px;
    }}
    .trail-item {{
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .trail-empty {{
      color: #8b8b92;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <h1>Teams 组织架构树</h1>
      <div class="meta-row">
        <span>数据抓取日期：{fetched_date_safe}</span>
        <span>总人数：{total_count}</span>
      </div>
      <div class="toolbar">
        <input id="searchInput" class="search-box" placeholder="搜索姓名 / 工号 / 部门" />
        <button id="prevMatchBtn" class="btn" type="button">pre</button>
        <button id="nextMatchBtn" class="btn" type="button">next</button>
        <button id="resetViewBtn" class="btn" type="button">重置视图</button>
      </div>
      <div class="tip">说明：树自左向右展开；首屏只显示根节点；按姓名搜索将自动居中命中节点；可用 pre/next 切换同名结果；节点文本支持框选；空白处支持拖动画布。</div>
      <div id="canvasWrap" class="canvas-wrap">
        <svg id="treeSvg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet">
          <g id="viewport"></g>
        </svg>
        <div id="hoverTrail" class="hover-trail" aria-hidden="true"></div>
      </div>
    </div>
  </div>

  <script>
    const NODES = {nodes_json};
    const ROOT_IDS = {roots_json};
    const NODE_W = 146;
    const NODE_H = 56;
    const H_STEP = 176;
    const V_STEP = 78;
    const ROOT_GAP_UNITS = 0.18;
    const SUBTREE_GAP_UNITS = 0.12;
    const HOVER_DELAY_MS = 1000;

    const byId = new Map(NODES.map((n) => [n.node_id, n]));
    const expanded = new Set();
    const highlights = new Set();

    let scale = 1;
    let tx = 40;
    let ty = 60;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let hoverTimer = null;
    let hoverNodeId = "";
    let hoverPoint = {{ x: 0, y: 0 }};
    let latestPositions = new Map();
    let nameMatches = [];
    let activeMatchIndex = -1;

    const svg = document.getElementById("treeSvg");
    const viewport = document.getElementById("viewport");
    const canvasWrap = document.getElementById("canvasWrap");
    const searchInput = document.getElementById("searchInput");
    const prevMatchBtn = document.getElementById("prevMatchBtn");
    const nextMatchBtn = document.getElementById("nextMatchBtn");
    const resetViewBtn = document.getElementById("resetViewBtn");
    const hoverTrail = document.getElementById("hoverTrail");

    function truncate(text, maxLen = 16) {{
      if (!text) return "-";
      return text.length > maxLen ? `${{text.slice(0, maxLen)}}...` : text;
    }}

    function escapeHtml(text) {{
      return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
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
        .map((node) => `<div class="trail-item">${{escapeHtml(node.name || "-")}}-${{escapeHtml(node.dept_name || "-")}}</div>`)
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
      hoverTrail.innerHTML = `<div class="trail-title">上游祖先链（根 -> 父级）</div>${{renderTrailHtml(nodeId)}}`;
      hoverTrail.classList.add("show");
      hoverTrail.setAttribute("aria-hidden", "false");
      placeHoverTrail(clientX, clientY);
    }}

    function scheduleHoverTrail(nodeId, clientX, clientY) {{
      clearHoverTrailTimer();
      hoverNodeId = nodeId;
      hoverPoint = {{ x: clientX, y: clientY }};
      hoverTimer = setTimeout(() => {{
        if (hoverNodeId !== nodeId) return;
        showHoverTrail(nodeId, hoverPoint.x, hoverPoint.y);
      }}, HOVER_DELAY_MS);
    }}

    function isInsideNode(target) {{
      let current = target;
      while (current && current !== svg) {{
        if (current.classList && current.classList.contains("node")) return true;
        current = current.parentNode;
      }}
      return false;
    }}

    function hasTextSelection() {{
      const selection = window.getSelection();
      return !!selection && String(selection).length > 0;
    }}

    function updateMatchButtons() {{
      const usable = nameMatches.length > 1;
      prevMatchBtn.disabled = !usable;
      nextMatchBtn.disabled = !usable;
    }}

    function findNameMatches(keyword) {{
      const exact = [];
      const includes = [];

      NODES.forEach((node) => {{
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

    function centerNode(nodeId) {{
      const pos = latestPositions.get(nodeId);
      if (!pos) return;

      const targetX = (pos.x + NODE_W / 2) * scale;
      const targetY = pos.y * scale;
      tx = canvasWrap.clientWidth / 2 - targetX;
      ty = canvasWrap.clientHeight / 2 - targetY;
      applyTransform();
    }}

    function focusActiveMatch() {{
      updateMatchButtons();
      if (!nameMatches.length || activeMatchIndex < 0) return;
      const nodeId = nameMatches[activeMatchIndex];
      if (!nodeId) return;

      expandAncestors(nodeId);
      highlights.add(nodeId);
      render();
      centerNode(nodeId);
    }}

    function switchMatch(step) {{
      if (!nameMatches.length) return;
      const total = nameMatches.length;
      activeMatchIndex = (activeMatchIndex + step + total) % total;
      focusActiveMatch();
    }}

    function getVisibleChildren(nodeId) {{
      const node = byId.get(nodeId);
      if (!node) return [];
      if (!expanded.has(nodeId)) return [];
      return node.children || [];
    }}

    function computeHeight(nodeId, heightCache) {{
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
          if (idx < children.length - 1) cursor += SUBTREE_GAP_UNITS;
        }});
      }}

      let cursor = 0;
      ROOT_IDS.forEach((rootId, idx) => {{
        const rootH = computeHeight(rootId, heightCache);
        assign(rootId, cursor, 0);
        cursor += rootH;
        if (idx < ROOT_IDS.length - 1) cursor += ROOT_GAP_UNITS;
      }});

      return {{ positions, edges }};
    }}

    function applyTransform() {{
      viewport.setAttribute("transform", `translate(${{tx}} ${{ty}}) scale(${{scale}})`);
    }}

    function buildNodeElement(node, pos) {{
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const hasChildren = (node.children || []).length > 0;
      g.setAttribute("class", `node${{highlights.has(node.node_id) ? " highlight" : ""}}${{hasChildren ? " expandable" : ""}}${{node.is_virtual ? " virtual" : ""}}`);
      g.setAttribute("transform", `translate(${{pos.x}} ${{pos.y - NODE_H / 2}})`);
      g.style.cursor = hasChildren ? "pointer" : "default";

      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("width", NODE_W);
      rect.setAttribute("height", NODE_H);
      g.appendChild(rect);

      const name = document.createElementNS("http://www.w3.org/2000/svg", "text");
      name.setAttribute("x", 8);
      name.setAttribute("y", 17);
      name.setAttribute("class", "name");
      name.textContent = truncate(node.name || "-", 10);
      g.appendChild(name);

      const idText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      idText.setAttribute("x", 8);
      idText.setAttribute("y", 31);
      idText.setAttribute("class", "meta");
      idText.textContent = `工号: ${{truncate(node.id || "-", 14)}}`;
      g.appendChild(idText);

      const deptText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      deptText.setAttribute("x", 8);
      deptText.setAttribute("y", 45);
      deptText.setAttribute("class", "meta");
      deptText.textContent = `部门: ${{truncate(node.dept_name || "-", 10)}}`;
      g.appendChild(deptText);

      if (hasChildren) {{
        const toggle = document.createElementNS("http://www.w3.org/2000/svg", "text");
        toggle.setAttribute("x", NODE_W - 12);
        toggle.setAttribute("y", 16);
        toggle.setAttribute("text-anchor", "middle");
        toggle.setAttribute("class", "toggle");
        toggle.textContent = expanded.has(node.node_id) ? "-" : "+";
        g.appendChild(toggle);
      }}

      if (hasChildren) {{
        g.addEventListener("click", (e) => {{
          e.stopPropagation();
          if (hasTextSelection()) return;
          hideHoverTrail();
          if (expanded.has(node.node_id)) expanded.delete(node.node_id);
          else expanded.add(node.node_id);
          render();
        }});
      }}

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
        if (hoverNodeId === node.node_id) {{
          hoverNodeId = "";
        }}
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

      edges.forEach(([fromId, toId]) => {{
        const from = positions.get(fromId);
        const to = positions.get(toId);
        if (!from || !to) return;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const sx = from.x + NODE_W;
        const sy = from.y;
        const tx2 = to.x;
        const ty2 = to.y;
        const cx = sx + (tx2 - sx) * 0.45;
        path.setAttribute("class", "link");
        path.setAttribute("d", `M ${{sx}} ${{sy}} C ${{cx}} ${{sy}}, ${{cx}} ${{ty2}}, ${{tx2}} ${{ty2}}`);
        viewport.appendChild(path);
      }});

      NODES.forEach((node) => {{
        const pos = positions.get(node.node_id);
        if (!pos) return;
        viewport.appendChild(buildNodeElement(node, pos));
      }});

      applyTransform();
    }}

    function expandAncestors(nodeId) {{
      let current = byId.get(nodeId);
      while (current && current.parent_id) {{
        expanded.add(current.parent_id);
        current = byId.get(current.parent_id);
      }}
    }}

    function handleSearch(keyword) {{
      const kw = (keyword || "").trim().toLowerCase();
      highlights.clear();
      nameMatches = [];
      activeMatchIndex = -1;
      if (!kw) {{
        updateMatchButtons();
        render();
        return;
      }}

      NODES.forEach((node) => {{
        if ((node.search_text || "").includes(kw)) {{
          highlights.add(node.node_id);
          expandAncestors(node.node_id);
        }}
      }});

      nameMatches = findNameMatches(kw);
      updateMatchButtons();
      if (!nameMatches.length) {{
        render();
        return;
      }}

      activeMatchIndex = 0;
      focusActiveMatch();
    }}

    function resetView() {{
      scale = 1;
      tx = 40;
      ty = 60;
      applyTransform();
    }}

    searchInput.addEventListener("input", (e) => handleSearch(e.target.value));
    prevMatchBtn.addEventListener("click", () => switchMatch(-1));
    nextMatchBtn.addEventListener("click", () => switchMatch(1));
    resetViewBtn.addEventListener("click", () => resetView());

    svg.addEventListener("wheel", (e) => {{
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      const next = Math.max(0.35, Math.min(2.8, scale * factor));
      scale = next;
      applyTransform();
    }}, {{ passive: false }});

    svg.addEventListener("mousedown", (e) => {{
      if (e.button !== 0) return;
      if (isInsideNode(e.target)) return;
      if (hasTextSelection()) return;
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      canvasWrap.classList.add("dragging");
    }});

    window.addEventListener("mousemove", (e) => {{
      if (!dragging) return;
      tx += e.clientX - lastX;
      ty += e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      applyTransform();
    }});

    window.addEventListener("mouseup", () => {{
      dragging = false;
      canvasWrap.classList.remove("dragging");
    }});

    updateMatchButtons();
    render();
  </script>
</body>
</html>
"""


def render_org_tree_html(members: list[dict], output_path: str, fetched_date: str = "") -> str:
    """
    根据成员列表生成组织架构树 HTML（内部调用）
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
