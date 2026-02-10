"""
根据成员 JSON 生成组织架构树 HTML（离线单文件）
"""
import argparse
import json
from datetime import datetime
from html import escape
from pathlib import Path


def _load_members(input_path: Path) -> list[dict]:
    """读取成员 JSON 列表"""
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("输入 JSON 必须是 list[dict] 结构")

    members = [item for item in data if isinstance(item, dict)]
    return members


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
      --bg: #f3f5f9;
      --surface: #ffffff;
      --text: #0f172a;
      --muted: #6b7280;
      --line: #cbd5e1;
      --accent: #0c4a6e;
      --highlight: #fef08a;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: radial-gradient(circle at 10% 0%, #e0f2fe 0%, var(--bg) 48%);
      color: var(--text);
    }}
    .container {{
      max-width: 1360px;
      margin: 20px auto;
      padding: 0 16px 24px;
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      padding: 16px;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 24px;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      color: var(--muted);
      margin-bottom: 12px;
      font-size: 14px;
    }}
    .toolbar {{
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }}
    .search-box {{
      width: 100%;
      max-width: 380px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      outline: none;
    }}
    .search-box:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
    }}
    .canvas-wrap {{
      margin-top: 10px;
      border: 1px solid #dbeafe;
      border-radius: 12px;
      background: linear-gradient(180deg, #f8fbff 0%, #f5f7fb 100%);
      height: 72vh;
      min-height: 580px;
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
      border: 1px solid #bfdbfe;
      background: #eff6ff;
      color: #1e3a8a;
      border-radius: 8px;
      font-size: 12px;
      padding: 6px 10px;
      cursor: pointer;
    }}
    .link {{
      stroke: #94a3b8;
      stroke-width: 1.3;
      fill: none;
    }}
    .node rect {{
      fill: #ffffff;
      stroke: #cbd5e1;
      stroke-width: 1.2;
      border-radius: 10px;
      rx: 10;
      ry: 10;
    }}
    .node .name {{
      font-size: 13px;
      font-weight: 700;
      fill: #0f172a;
    }}
    .node .meta {{
      font-size: 11px;
      fill: #475569;
    }}
    .node.highlight rect {{
      background: var(--highlight);
      fill: #fef9c3;
      stroke: #f59e0b;
      stroke-width: 1.6;
    }}
    .node.virtual rect {{
      fill: #fff7ed;
      stroke: #f59e0b;
      stroke-dasharray: 4 3;
    }}
    .node.virtual .name {{
      fill: #9a3412;
    }}
    .node.expandable .toggle {{
      fill: #0c4a6e;
      font-size: 12px;
      font-weight: 700;
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
        <button id="resetViewBtn" class="btn" type="button">重置视图</button>
      </div>
      <div class="tip">说明：树自左向右展开；首屏只显示根节点；点击节点展开直属下级；支持滚轮缩放和拖动画布。</div>
      <div id="canvasWrap" class="canvas-wrap">
        <svg id="treeSvg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid meet">
          <g id="viewport"></g>
        </svg>
      </div>
    </div>
  </div>

  <script>
    const NODES = {nodes_json};
    const ROOT_IDS = {roots_json};
    const NODE_W = 166;
    const NODE_H = 62;
    const H_STEP = 210;
    const V_STEP = 94;
    const ROOT_GAP_UNITS = 0.28;
    const SUBTREE_GAP_UNITS = 0.18;

    const byId = new Map(NODES.map((n) => [n.node_id, n]));
    const expanded = new Set();
    const highlights = new Set();

    let scale = 1;
    let tx = 40;
    let ty = 60;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;

    const svg = document.getElementById("treeSvg");
    const viewport = document.getElementById("viewport");
    const canvasWrap = document.getElementById("canvasWrap");
    const searchInput = document.getElementById("searchInput");
    const resetViewBtn = document.getElementById("resetViewBtn");

    function truncate(text, maxLen = 16) {{
      if (!text) return "-";
      return text.length > maxLen ? `${{text.slice(0, maxLen)}}...` : text;
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
      name.setAttribute("y", 18);
      name.setAttribute("class", "name");
      name.textContent = truncate(node.name || "-", 12);
      g.appendChild(name);

      const idText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      idText.setAttribute("x", 8);
      idText.setAttribute("y", 34);
      idText.setAttribute("class", "meta");
      idText.textContent = `工号: ${{truncate(node.id || "-", 18)}}`;
      g.appendChild(idText);

      const deptText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      deptText.setAttribute("x", 8);
      deptText.setAttribute("y", 50);
      deptText.setAttribute("class", "meta");
      deptText.textContent = `部门: ${{truncate(node.dept_name || "-", 12)}}`;
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
          if (expanded.has(node.node_id)) expanded.delete(node.node_id);
          else expanded.add(node.node_id);
          render();
        }});
      }}

      return g;
    }}

    function render() {{
      const {{ positions, edges }} = layoutTree();
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
      if (!kw) {{
        render();
        return;
      }}

      NODES.forEach((node) => {{
        if ((node.search_text || "").includes(kw)) {{
          highlights.add(node.node_id);
          expandAncestors(node.node_id);
        }}
      }});

      render();
    }}

    function resetView() {{
      scale = 1;
      tx = 40;
      ty = 60;
      applyTransform();
    }}

    searchInput.addEventListener("input", (e) => handleSearch(e.target.value));
    resetViewBtn.addEventListener("click", () => resetView());

    svg.addEventListener("wheel", (e) => {{
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      const next = Math.max(0.35, Math.min(2.8, scale * factor));
      scale = next;
      applyTransform();
    }}, {{ passive: false }});

    svg.addEventListener("mousedown", (e) => {{
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

    render();
  </script>
</body>
</html>
"""


def generate_org_tree_html(input_path: str, output_path: str, fetched_date: str = "") -> str:
    """
    从成员 JSON 生成组织架构树 HTML
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_file.as_posix()}")

    members = _load_members(input_file)
    roots, node_map = _build_tree(members)

    if fetched_date:
        used_date = fetched_date
    else:
        mtime = datetime.fromtimestamp(input_file.stat().st_mtime)
        used_date = mtime.strftime("%Y-%m-%d %H:%M:%S")

    html_content = _render_html(
        roots=roots,
        node_map=node_map,
        total_count=len(members),
        fetched_date=used_date,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")
    return output_file.as_posix()


def main():
    parser = argparse.ArgumentParser(description="根据成员JSON生成组织架构树HTML")
    parser.add_argument("--input", "-i", required=True, help="输入成员 JSON 文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出 HTML 文件路径")
    parser.add_argument(
        "--fetched-date",
        default="",
        help="数据抓取日期（可选，如 2026-02-10 18:30:00）",
    )
    args = parser.parse_args()

    out = generate_org_tree_html(
        input_path=args.input,
        output_path=args.output,
        fetched_date=args.fetched_date,
    )
    print(f"组织架构树 HTML 已生成: {out}")


if __name__ == "__main__":
    main()
