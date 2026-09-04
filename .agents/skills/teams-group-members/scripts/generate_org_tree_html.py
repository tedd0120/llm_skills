"""
根据成员列表生成组织架构树 HTML（离线单文件，供抓取流程内部调用）
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _build_tree(members: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    """
    根据 superior -> name 构建树结构。
    返回按 subtree_size 降序排列的根节点列表与节点字典。
    """
    nodes = []
    name_to_nodes = {}

    for idx, member in enumerate(members):
        is_virtual = bool(member.get("is_virtual", False)) or str(member.get("role_desc", "")).strip() == "虚拟上级"
        node = {
            "node_id": f"n{idx}",
            "name": str(member.get("name", "")).strip(),
            "id": str(member.get("id", "")).strip(),
            "dept_name": str(member.get("deptName", "")).strip(),
            "superior": str(member.get("superior", "")).strip(),
            "member": member,
            "children": [],
            "parent_id": "",
            "is_virtual": is_virtual,
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

    for root in roots:
        stack = [(root, 0)]
        visited = set()
        while stack:
            curr, depth = stack.pop()
            if curr["node_id"] in visited:
                continue
            visited.add(curr["node_id"])
            curr["depth"] = depth
            curr["root_id"] = root["node_id"]
            for child in curr["children"]:
                if child["node_id"] not in visited:
                    stack.append((child, depth + 1))

    for node in nodes:
        node.setdefault("depth", 0)
        node.setdefault("root_id", node["node_id"])

    nodes_by_depth_desc = sorted(nodes, key=lambda n: n.get("depth", 0), reverse=True)
    for node in nodes_by_depth_desc:
        node["subtree_size"] = 1 + sum(child.get("subtree_size", 1) for child in node["children"])

    roots.sort(key=lambda r: r.get("subtree_size", 1), reverse=True)

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


def _serialize_nodes_for_frontend(
    nodes: dict[str, dict] | list[dict],
    roots: list[dict],
    fetched_date: str = "",
) -> tuple[list[dict], list[int], dict[str, Any]]:
    """
    序列化分栏钻取前端数据。
    返回节点数组、根索引数组和元信息字典。
    """
    if isinstance(nodes, dict):
        node_list = list(nodes.values())
    elif isinstance(nodes, list):
        node_list = list(nodes)
    else:
        raise TypeError("nodes 必须是 dict[str, dict] 或 list[dict]")

    if not isinstance(roots, list):
        raise TypeError("roots 必须是 list[dict]")

    node_id_to_index = {}
    for idx, node in enumerate(node_list):
        if not isinstance(node, dict):
            raise TypeError("nodes 元素必须是 dict")
        nid = node.get("node_id", f"n{idx}")
        node_id_to_index[nid] = idx

    nodes_data = []
    for idx, node in enumerate(node_list):
        member = node.get("member", {})
        parent_id = node.get("parent_id", "")
        parent_index = node_id_to_index.get(parent_id, -1) if parent_id else -1
        root_id = node.get("root_id", "")
        root_index = node_id_to_index.get(root_id, idx) if root_id else idx

        children_indices = []
        for child in node.get("children", []):
            if isinstance(child, dict):
                cid = child.get("node_id", "")
                if cid in node_id_to_index:
                    children_indices.append(node_id_to_index[cid])

        role_desc = str(member.get("role_desc", "")).strip()
        bp_name = str(member.get("bpName", "")).strip()
        work_place_name = str(member.get("workPlaceName", "")).strip()
        user_name = str(member.get("userName", "")).strip()
        sex_desc = str(member.get("sex_desc", "")).strip()
        is_virtual = bool(node.get("is_virtual", False))

        nodes_data.append(
            {
                "depth": int(node.get("depth", 0)),
                "subtree_size": int(node.get("subtree_size", 1)),
                "root_index": root_index,
                "parent_index": parent_index,
                "name": str(node.get("name", "")).strip(),
                "id": str(node.get("id", "")).strip(),
                "dept_name": str(node.get("dept_name", "")).strip(),
                "superior": str(node.get("superior", "")).strip(),
                "role_desc": role_desc,
                "bp_name": bp_name,
                "work_place_name": work_place_name,
                "user_name": user_name,
                "sex_desc": sex_desc,
                "is_virtual": is_virtual,
                "search_text": _node_search_text(node),
                "children": children_indices,
            }
        )

    roots_data = []
    for r in roots:
        if not isinstance(r, dict):
            raise TypeError("roots 元素必须是 dict")
        rid = r.get("node_id", "")
        if rid in node_id_to_index:
            roots_data.append(node_id_to_index[rid])
        else:
            raise ValueError(f"根节点 '{rid}' 不在 nodes 中")

    meta = {
        "total": len(nodes_data),
        "lines": len(roots_data),
        "date": fetched_date or datetime.now().strftime("%Y-%m-%d"),
    }

    return nodes_data, roots_data, meta


_serialize_nodes_for_frontend_c = _serialize_nodes_for_frontend


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Teams 组织架构</title>
  <style>
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      overflow: hidden;
      background: #eaeef3;
    }

    .org-app {
      position: absolute; inset: 0; display: flex; flex-direction: column; color: #0f172a;
    }

    .org-head {
      display: flex; align-items: center; gap: 18px; padding: 0 20px; height: 62px;
      background: #fff; border-bottom: 1px solid #d7dee8; flex: none;
    }
    .org-head h1 { margin: 0; font-size: 15px; font-weight: 700; letter-spacing: -.01em; }
    .org-kpi { display: flex; gap: 18px; }
    .org-kpi div { font-size: 11px; color: #64748b; }
    .org-kpi b { display: block; font-size: 16px; color: #0f172a; font-variant-numeric: tabular-nums; }

    .org-search { margin-left: auto; position: relative; width: 300px; }
    .org-search input {
      width: 100%; height: 36px; border-radius: 9px; border: 1px solid #cbd5e1; background: #f8fafc;
      padding: 0 12px; font-size: 13px; outline: none;
    }
    .org-search input:focus { border-color: #4f46e5; background: #fff; box-shadow: 0 0 0 3px rgba(79,70,229,.13); }
    .org-dropdown {
      position: absolute; top: 42px; left: 0; right: 0; background: #fff; border: 1px solid #d7dee8;
      border-radius: 10px; box-shadow: 0 20px 44px rgba(15,23,42,.16); max-height: 320px; overflow: auto; display: none; z-index: 20;
    }
    .org-dropdown.show { display: block; }
    .org-drop-item { padding: 9px 12px; font-size: 13px; cursor: pointer; display: flex; gap: 8px; align-items: baseline; }
    .org-drop-item:hover { background: #eef2ff; }
    .org-drop-item small { color: #64748b; font-size: 11px; }
    .org-drop-empty { padding: 12px; font-size: 13px; color: #94a3b8; text-align: center; }

    .org-path {
      flex: none; display: flex; align-items: center; gap: 6px; padding: 9px 20px;
      background: #f8fafc; border-bottom: 1px solid #e2e8f0; overflow-x: auto; white-space: nowrap;
    }
    .org-path::-webkit-scrollbar { height: 0; }
    .org-path-label { flex: none; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: #94a3b8; margin-right: 4px; }
    .org-path button {
      flex: none; display: inline-flex; align-items: center; gap: 7px; cursor: pointer;
      border: 1px solid #d7dee8; background: #fff; border-radius: 8px; padding: 5px 11px;
      font-size: 12px; color: #0f172a;
    }
    .org-path button:hover { border-color: #4f46e5; color: #4f46e5; }
    .org-path button.on { background: #4f46e5; border-color: #4f46e5; color: #fff; }
    .org-path button small { font-size: 10px; color: #94a3b8; }
    .org-path button.on small { color: rgba(255,255,255,.7); }
    .org-path-sep { flex: none; color: #cbd5e1; font-size: 11px; }

    .org-cols { flex: 1; display: flex; overflow-x: auto; overflow-y: hidden; min-height: 0; scroll-behavior: smooth; }
    .org-col { width: 262px; flex: none; border-right: 1px solid #d7dee8; display: flex; flex-direction: column; background: #fff; min-height: 0; }
    .org-col:nth-child(even) { background: #fbfcfe; }
    .org-col-head {
      padding: 11px 14px; font-size: 11px; color: #64748b; border-bottom: 1px solid #e6ebf2;
      display: flex; justify-content: space-between; letter-spacing: .04em; flex: none;
    }
    .org-col-head b { color: #0f172a; font-weight: 600; }
    .org-col-body { overflow: auto; flex: 1; padding: 6px; }
    .org-col:last-child { flex: 1 1 auto; min-width: 262px; }
    .org-col:last-child .org-col-body { display: grid; grid-template-columns: repeat(auto-fill, minmax(238px, 1fr)); gap: 3px; align-content: start; }

    .org-item {
      display: flex; align-items: center; gap: 8px; padding: 7px 9px; border-radius: 7px;
      cursor: pointer; font-size: 13px;
    }
    .org-item:hover { background: #f1f5f9; }
    .org-item.on { background: #4f46e5; color: #fff; }
    .org-item.on .org-sub, .org-item.on .org-count { color: rgba(255,255,255,.76); }
    .org-text { flex: 1; min-width: 0; }
    .org-text b { display: block; font-weight: 600; }
    .org-sub { display: block; font-size: 11px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .org-count { font-size: 11px; color: #94a3b8; font-variant-numeric: tabular-nums; }
    .org-item.vir b { color: #b45309; }
    .org-item.on.vir b { color: #fde68a; }

    .org-strip {
      flex: none; background: #fff; border-top: 1px solid #d7dee8; padding: 14px 20px 48px;
      display: flex; gap: 30px; align-items: flex-start; min-height: 108px;
    }
    .org-strip-id { min-width: 190px; }
    .org-strip-id b { font-size: 20px; letter-spacing: -.01em; display: block; }
    .org-strip-id span { display: block; font-size: 11px; color: #64748b; margin-top: 3px; font-variant-numeric: tabular-nums; }
    .org-strip-id.vir b { color: #b45309; }
    .org-strip dl { display: flex; gap: 26px; margin: 0; flex-wrap: wrap; }
    .org-strip dt { font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: #94a3b8; }
    .org-strip dd { margin: 4px 0 0; font-size: 13px; }
    .org-hint { color: #94a3b8; font-size: 13px; }
  </style>
</head>
<body>
  <div class="org-app">
    <div class="org-head">
      <h1>Teams 组织架构</h1>
      <div class="org-kpi" id="orgKpi"></div>
      <div class="org-search">
        <input id="orgSearch" placeholder="搜索姓名 / 工号 / 部门 / 办公地" />
        <div class="org-dropdown" id="orgDrop"></div>
      </div>
    </div>
    <div class="org-path" id="orgPath"></div>
    <div class="org-cols" id="orgCols"></div>
    <div class="org-strip" id="orgStrip"></div>
  </div>

  <script>
    const N = __NODES_JSON__;
    const ROOTS = __ROOTS_JSON__;
    const META = __META_JSON__;

    const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
    const cut = (s, n) => { s = s || "-"; return s.length > n ? s.slice(0, n) + "…" : s; };

    function ancestorIndices(i) {
      const out = [];
      const visited = new Set([i]);
      let cur = N[i];
      while (cur && cur.parent_index >= 0 && !visited.has(cur.parent_index)) {
        visited.add(cur.parent_index);
        out.unshift(cur.parent_index);
        cur = N[cur.parent_index];
      }
      return out;
    }

    const find = (q) => {
      q = q.trim().toLowerCase();
      if (!q) return [];
      const hits = [];
      for (let i = 0; i < N.length; i++) {
        if (N[i].search_text && N[i].search_text.indexOf(q) >= 0) {
          hits.push(i);
        }
      }
      return hits;
    };

    const C = {
      path: (ROOTS && ROOTS.length) ? [ROOTS[0]] : [],
      scroll: new Map()
    };

    function cRender(follow) {
      const cols0 = document.querySelectorAll("#orgCols .org-col");
      cols0.forEach((el) => {
        const key = el.dataset.key;
        const body = el.querySelector(".org-col-body");
        if (key && body) C.scroll.set(key, body.scrollTop);
      });
      const prevCount = cols0.length;

      const cols = [{ key: "root", title: "业务条线", sub: (META.lines || 0) + " 条", items: ROOTS || [] }];
      C.path.forEach((i) => {
        if (N[i] && N[i].children && N[i].children.length) {
          cols.push({
            key: "n" + i,
            title: N[i].name,
            sub: N[i].children.length + " 名直属",
            items: N[i].children
          });
        }
      });

      document.getElementById("orgCols").innerHTML = cols.map((col, k) => `
        <div class="org-col" data-key="${col.key}">
          <div class="org-col-head"><b>${esc(col.title)}</b><span>${esc(col.sub)}</span></div>
          <div class="org-col-body">${col.items.map((i) => {
            const n = N[i];
            if (!n) return "";
            const isSelected = C.path[k] === i;
            const isVir = n.is_virtual;
            const countLabel = n.children && n.children.length ? n.subtree_size : "";
            return `<div class="org-item ${isSelected ? "on" : ""} ${isVir ? "vir" : ""}" data-k="${k}" data-i="${i}">
              <span class="org-text"><b>${esc(n.name)}</b><span class="org-sub">${esc(n.dept_name || n.role_desc)}</span></span>
              <span class="org-count">${countLabel}</span>
            </div>`;
          }).join("")}</div>
        </div>`).join("");

      document.querySelectorAll("#orgCols .org-col").forEach((el, k) => {
        if (cols[k]) {
          const memo = C.scroll.get(cols[k].key);
          const body = el.querySelector(".org-col-body");
          if (body) {
            if (memo != null) {
              body.scrollTop = memo;
            }
            if (follow === "end") {
              const onEl = el.querySelector(".org-item.on");
              if (onEl) onEl.scrollIntoView({ block: "nearest" });
            }
          }
        }
      });

      if (!C.path.length) {
        document.getElementById("orgPath").innerHTML = '<span class="org-path-label">路径</span><span class="org-hint">暂无数据</span>';
      } else {
        document.getElementById("orgPath").innerHTML = '<span class="org-path-label">路径</span>' +
          C.path.map((i, k) => {
            const n = N[i];
            if (!n) return "";
            const isLast = k === C.path.length - 1;
            const sub = esc(cut(n.dept_name || n.role_desc, 8));
            return `<button data-col="${k}" class="${isLast ? "on" : ""}">
              <span>${esc(n.name)}</span>
              <small>${sub}</small></button>`;
          }).join('<span class="org-path-sep">›</span>');

        const activeBtn = document.querySelector("#orgPath button.on");
        if (activeBtn) activeBtn.scrollIntoView({ block: "nearest", inline: "nearest" });
      }

      const last = C.path.length ? C.path[C.path.length - 1] : -1;
      const cur = (last >= 0 && N[last]) ? N[last] : null;
      if (!cur) {
        document.getElementById("orgStrip").innerHTML = '<div class="org-hint">暂无选中成员</div>';
      } else {
        const idText = [cur.id || "无工号", cur.role_desc].filter(Boolean).join(" · ");
        const dlFields = [
          ["部门", cur.dept_name],
          ["上级", cur.superior],
          ["HRBP", cur.bp_name],
          ["办公地", cur.work_place_name],
          ["账号", cur.user_name],
          ["直属下级", cur.children ? cur.children.length : 0],
          ["团队规模", (cur.subtree_size || 1) - 1],
          ["层级", (cur.depth || 0) + 1]
        ];
        document.getElementById("orgStrip").innerHTML = `
          <div class="org-strip-id ${cur.is_virtual ? "vir" : ""}">
            <b>${esc(cur.name)}</b>
            <span>${esc(idText)}</span>
          </div>
          <dl>${dlFields.map(([k, v]) => {
            const displayVal = (v === 0 || (v != null && String(v).trim() !== "")) ? v : "-";
            return `<div><dt>${k}</dt><dd>${esc(displayVal)}</dd></div>`;
          }).join("")}</dl>`;
      }

      const box = document.getElementById("orgCols");
      if (follow === "end" || cols.length > prevCount) {
        box.scrollLeft = box.scrollWidth;
      }
    }

    function cGoto(i) {
      if (!N[i]) return;
      C.path = ancestorIndices(i).concat([i]);
      cRender("end");
    }

    function cInitUI() {
      document.getElementById("orgKpi").innerHTML = [
        ["总人数", META.total],
        ["业务条线", META.lines],
        ["抓取日期", META.date]
      ].map(([k, v]) => `<div><b>${esc(v)}</b>${k}</div>`).join("");

      document.getElementById("orgCols").addEventListener("click", (ev) => {
        const it = ev.target.closest("[data-i]");
        if (!it) return;
        const k = Number(it.dataset.k);
        C.path = C.path.slice(0, k);
        C.path[k] = Number(it.dataset.i);
        cRender();
      });

      document.getElementById("orgPath").addEventListener("click", (ev) => {
        const b = ev.target.closest("[data-col]");
        if (!b) return;
        const cols = document.querySelectorAll("#orgCols .org-col");
        const col = cols[Number(b.dataset.col)];
        if (col) document.getElementById("orgCols").scrollLeft = col.offsetLeft;
      });

      const inp = document.getElementById("orgSearch");
      const drop = document.getElementById("orgDrop");
      let timer = null;

      inp.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          const val = inp.value.trim();
          if (!val) {
            drop.className = "org-dropdown";
            drop.innerHTML = "";
            return;
          }
          const hits = find(val).slice(0, 40);
          drop.className = "org-dropdown" + (hits.length ? " show" : "");
          drop.innerHTML = hits.length
            ? hits.map((i) => {
                const n = N[i];
                const sub = [n.dept_name || n.role_desc, n.id].filter(Boolean).join(" · ");
                return `<div class="org-drop-item" data-i="${i}">${esc(n.name)}<small>${esc(sub)}</small></div>`;
              }).join("")
            : '<div class="org-drop-empty">无匹配成员</div>';
        }, 140);
      });

      drop.addEventListener("click", (ev) => {
        const el = ev.target.closest("[data-i]");
        if (!el) return;
        cGoto(Number(el.dataset.i));
        drop.className = "org-dropdown";
        inp.value = "";
      });

      inp.addEventListener("blur", () => {
        setTimeout(() => { drop.className = "org-dropdown"; }, 180);
      });

      inp.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape") {
          drop.className = "org-dropdown";
        } else if (ev.key === "Enter") {
          const first = drop.querySelector("[data-i]");
          if (first) {
            cGoto(Number(first.dataset.i));
            drop.className = "org-dropdown";
            inp.value = "";
          }
        }
      });
    }

    cInitUI();
    cRender();
  </script>
</body>
</html>
"""


def _render_html(roots: list[dict], node_map: dict[str, dict], fetched_date: str) -> str:
    """生成分栏钻取组织架构 HTML。"""
    nodes_data, roots_data, meta = _serialize_nodes_for_frontend(node_map, roots, fetched_date)
    nodes_json = json.dumps(nodes_data, ensure_ascii=False).replace("</", "<\\/")
    roots_json = json.dumps(roots_data, ensure_ascii=False)
    meta_json = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")

    return (
        _HTML_TEMPLATE
        .replace("__NODES_JSON__", nodes_json)
        .replace("__ROOTS_JSON__", roots_json)
        .replace("__META_JSON__", meta_json)
    )


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
        fetched_date=used_date,
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")
    return output_file.as_posix()


if __name__ == "__main__":
    raise SystemExit("该脚本仅供内部调用，请使用 fetch_group_members.py 进行抓取并自动生成HTML。")
