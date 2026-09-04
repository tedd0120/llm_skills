from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_org_tree_html as tree_module  # noqa: E402


class GenerateOrgTreeHtmlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_members = [
            {
                "id": "1001",
                "name": "张三",
                "deptName": "研发部",
                "superior": "",
                "role_desc": "部门主管",
                "bpName": "李HR",
                "workPlaceName": "北京",
                "userName": "zhangsan",
                "sex_desc": "男",
                "is_virtual": False,
            },
            {
                "id": "1002",
                "name": "李四",
                "deptName": "研发一组",
                "superior": "张三",
                "role_desc": "工程师",
                "bpName": "李HR",
                "workPlaceName": "北京",
                "userName": "lisi",
                "sex_desc": "男",
                "is_virtual": False,
            },
            {
                "id": "1003",
                "name": "王五",
                "deptName": "研发一组",
                "superior": "李四",
                "role_desc": "初级工程师",
                "bpName": "李HR",
                "workPlaceName": "上海",
                "userName": "wangwu",
                "sex_desc": "女",
                "is_virtual": False,
            },
            {
                "id": "1004",
                "name": "赵六",
                "deptName": "测试部",
                "superior": "",
                "role_desc": "测试主管",
                "bpName": "李HR",
                "workPlaceName": "深圳",
                "userName": "zhaoliu",
                "sex_desc": "男",
                "is_virtual": False,
            },
            {
                "id": "1005",
                "name": "虚拟负责人",
                "deptName": "待分配部",
                "superior": "",
                "role_desc": "虚拟上级",
                "bpName": "",
                "workPlaceName": "北京",
                "userName": "v_leader",
                "sex_desc": "",
            },
        ]

    def test_build_tree_populates_depth_root_id_and_subtree_size(self) -> None:
        roots, node_map = tree_module._build_tree(self.sample_members)
        self.assertEqual(len(roots), 3)

        root_ids = {r["node_id"] for r in roots}
        for node in node_map.values():
            self.assertIn("depth", node)
            self.assertIn("root_id", node)
            self.assertIn("subtree_size", node)
            self.assertIn(node["root_id"], root_ids)
            self.assertGreaterEqual(node["depth"], 0)
            self.assertGreaterEqual(node["subtree_size"], 1)

        zhang = next(n for n in node_map.values() if n["name"] == "张三")
        li = next(n for n in node_map.values() if n["name"] == "李四")
        wang = next(n for n in node_map.values() if n["name"] == "王五")
        zhao = next(n for n in node_map.values() if n["name"] == "赵六")
        virtual = next(n for n in node_map.values() if n["name"] == "虚拟负责人")

        self.assertEqual(zhang["depth"], 0)
        self.assertEqual(zhang["root_id"], zhang["node_id"])
        self.assertEqual(zhang["subtree_size"], 3)

        self.assertEqual(li["depth"], 1)
        self.assertEqual(li["root_id"], zhang["node_id"])
        self.assertEqual(li["subtree_size"], 2)

        self.assertEqual(wang["depth"], 2)
        self.assertEqual(wang["root_id"], zhang["node_id"])
        self.assertEqual(wang["subtree_size"], 1)

        self.assertEqual(zhao["depth"], 0)
        self.assertEqual(zhao["root_id"], zhao["node_id"])
        self.assertEqual(zhao["subtree_size"], 1)

        self.assertEqual(virtual["depth"], 0)
        self.assertEqual(virtual["root_id"], virtual["node_id"])
        self.assertEqual(virtual["subtree_size"], 1)

    def test_roots_sorted_by_subtree_size_descending(self) -> None:
        roots, _ = tree_module._build_tree(self.sample_members)
        sizes = [r["subtree_size"] for r in roots]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(roots[0]["name"], "张三")
        self.assertEqual(roots[0]["subtree_size"], 3)

    def test_detects_virtual_nodes(self) -> None:
        members = [
            {"name": "显式标记", "superior": "", "is_virtual": True, "role_desc": "总监"},
            {"name": "角色标记", "superior": "", "is_virtual": False, "role_desc": "虚拟上级"},
            {"name": "真实成员", "superior": "", "is_virtual": False, "role_desc": "开发"},
        ]
        _, node_map = tree_module._build_tree(members)
        v1 = next(n for n in node_map.values() if n["name"] == "显式标记")
        v2 = next(n for n in node_map.values() if n["name"] == "角色标记")
        v3 = next(n for n in node_map.values() if n["name"] == "真实成员")
        self.assertTrue(v1["is_virtual"])
        self.assertTrue(v2["is_virtual"])
        self.assertFalse(v3["is_virtual"])

    def test_serialize_nodes_for_frontend_c_keys_and_values(self) -> None:
        roots, node_map = tree_module._build_tree(self.sample_members)
        nodes_data, roots_data, meta = tree_module._serialize_nodes_for_frontend_c(
            node_map,
            roots,
            fetched_date="2026-03-31",
        )

        expected_keys = {
            "depth",
            "subtree_size",
            "root_index",
            "parent_index",
            "name",
            "id",
            "dept_name",
            "superior",
            "role_desc",
            "bp_name",
            "work_place_name",
            "user_name",
            "sex_desc",
            "is_virtual",
            "search_text",
            "children",
        }

        self.assertEqual(len(nodes_data), len(self.sample_members))
        for item in nodes_data:
            self.assertTrue(expected_keys.issubset(item.keys()))
            self.assertIsInstance(item["depth"], int)
            self.assertIsInstance(item["subtree_size"], int)
            self.assertIsInstance(item["root_index"], int)
            self.assertIsInstance(item["parent_index"], int)
            self.assertIsInstance(item["is_virtual"], bool)
            self.assertIsInstance(item["children"], list)
            self.assertIn(item["root_index"], roots_data)

        self.assertEqual(len(roots_data), 3)
        self.assertEqual(meta["total"], len(self.sample_members))
        self.assertEqual(meta["lines"], 3)
        self.assertEqual(meta["date"], "2026-03-31")

        zhang = next(item for item in nodes_data if item["name"] == "张三")
        li = next(item for item in nodes_data if item["name"] == "李四")
        wang = next(item for item in nodes_data if item["name"] == "王五")

        zhang_index = nodes_data.index(zhang)
        li_index = nodes_data.index(li)
        wang_index = nodes_data.index(wang)

        self.assertEqual(zhang["parent_index"], -1)
        self.assertEqual(zhang["root_index"], zhang_index)
        self.assertIn(li_index, zhang["children"])

        self.assertEqual(li["parent_index"], zhang_index)
        self.assertEqual(li["root_index"], zhang_index)
        self.assertIn(wang_index, li["children"])

        self.assertEqual(wang["parent_index"], li_index)
        self.assertEqual(wang["root_index"], zhang_index)
        self.assertEqual(wang["children"], [])

    def test_serialize_nodes_for_frontend_c_accepts_list_of_nodes(self) -> None:
        roots, node_map = tree_module._build_tree(self.sample_members)
        nodes_list = list(node_map.values())
        nodes_data, roots_data, meta = tree_module._serialize_nodes_for_frontend_c(
            nodes_list,
            roots,
            fetched_date="2026-03-31",
        )
        self.assertEqual(len(nodes_data), len(nodes_list))
        self.assertEqual(meta["total"], len(nodes_list))
        self.assertEqual(meta["lines"], len(roots))

    def test_legacy_serialize_nodes_for_frontend_backward_compatibility(self) -> None:
        roots, node_map = tree_module._build_tree(self.sample_members)
        nodes_json, roots_json = tree_module._serialize_nodes_for_frontend(roots, node_map)
        nodes = json.loads(nodes_json)
        root_ids = json.loads(roots_json)

        self.assertEqual(len(nodes), len(self.sample_members))
        self.assertEqual(len(root_ids), len(roots))
        self.assertIn("node_id", nodes[0])
        self.assertIn("parent_id", nodes[0])

    def test_render_org_tree_html_generates_file_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "output.html"
            result_path = tree_module.render_org_tree_html(
                self.sample_members,
                str(out_file),
                fetched_date="2026-03-31",
            )
            self.assertTrue(out_file.exists())
            self.assertEqual(result_path, out_file.as_posix())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("张三", content)

    def test_empty_members_handling(self) -> None:
        roots, node_map = tree_module._build_tree([])
        self.assertEqual(roots, [])
        self.assertEqual(node_map, {})
        nodes_data, roots_data, meta = tree_module._serialize_nodes_for_frontend_c(node_map, roots)
        self.assertEqual(nodes_data, [])
        self.assertEqual(roots_data, [])
        self.assertEqual(meta["total"], 0)
        self.assertEqual(meta["lines"], 0)

    def test_single_member_handling(self) -> None:
        roots, node_map = tree_module._build_tree([{"name": "独苗"}])
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0]["depth"], 0)
        self.assertEqual(roots[0]["subtree_size"], 1)
        nodes_data, roots_data, meta = tree_module._serialize_nodes_for_frontend_c(node_map, roots)
        self.assertEqual(len(nodes_data), 1)
        self.assertEqual(roots_data, [0])
        self.assertEqual(nodes_data[0]["parent_index"], -1)
        self.assertEqual(nodes_data[0]["root_index"], 0)
        self.assertEqual(meta["total"], 1)
        self.assertEqual(meta["lines"], 1)

    def test_real_dataset_metrics_and_serialization(self) -> None:
        members_path = Path(__file__).resolve().parents[4] / "data" / "teams-group-members" / "members.json"
        if not members_path.exists():
            self.skipTest("真实数据文件 members.json 未就绪")

        members = json.loads(members_path.read_text(encoding="utf-8"))
        roots, node_map = tree_module._build_tree(members)
        self.assertEqual(len(node_map), 996)
        self.assertEqual(len(roots), 73)

        sizes = [r["subtree_size"] for r in roots]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(sum(sizes), 996)

        nodes_data, roots_data, meta = tree_module._serialize_nodes_for_frontend_c(
            node_map,
            roots,
            fetched_date="2026-03-31",
        )
        self.assertEqual(meta["total"], 996)
        self.assertEqual(meta["lines"], 73)
        self.assertEqual(meta["date"], "2026-03-31")
        self.assertEqual(len(nodes_data), 996)
        self.assertEqual(len(roots_data), 73)


if __name__ == "__main__":
    unittest.main()
