# -*- coding: utf-8 -*-
"""执行重命名方案：建目录 → 移动 → 改名，逐条写回滚日志。

用法:
    python apply.py output/rename_plan.json --dry-run   # 只打印将执行的操作
    python apply.py output/rename_plan.json             # 实际执行（支持断点续跑）

方案 JSON 格式:
{
  "rootId": 0,                      # newPath 相对哪个目录（与 scan --parent 一致）
  "entries": [
    {"fileId": 111, "oldPath": "/【韩综】豆豆笑笑2025（韩国）/01期.mp4",
     "newPath": "/豆豆笑笑 (2025)/Season 01/豆豆笑笑 (2025) S01E01.mp4"}
  ]
}

回滚日志为 JSONL（output/rollback_log.jsonl），每完成一步追加一行。
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from pan123_client import Pan123Client

ILLEGAL = re.compile(r'["*:<>?/\\|]')


def sanitize(name):
    return ILLEGAL.sub("", name).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", help="rename_plan.json 路径")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log", default=str(Path(__file__).parent / "output" / "rollback_log.jsonl"))
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    root_id = plan.get("rootId", 0)
    entries = plan["entries"]

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if log_path.is_file():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("action") == "done":
                done.add(rec["fileId"])

    def log(rec):
        rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(rec, ensure_ascii=False) + "\n")

    c = None if args.dry_run else Pan123Client()

    # 第一步：目录原地改名（可选 dirRenames: [{fileId, oldPath, newName}]）
    for d in plan.get("dirRenames", []):
        key = f"dir:{d['fileId']}"
        if key in done:
            continue
        old_name = d["oldPath"].rsplit("/", 1)[-1]
        new_name = sanitize(d["newName"])
        print(f"[目录] {d['oldPath']} → {new_name}")
        if not args.dry_run and old_name != new_name:
            try:
                c.rename(d["fileId"], new_name)
                log({"action": "rename", "fileId": d["fileId"],
                     "fromName": old_name, "toName": new_name})
                log({"action": "done", "fileId": key})
            except RuntimeError as err:
                print(f"  目录改名失败：{err}", file=sys.stderr)
                log({"action": "error", "fileId": d["fileId"], "error": str(err)})

    dir_cache = {"": root_id}  # 相对路径 -> fileId
    # 可选 dirIds: {"新路径": fileId}，已知目录直接命中，省去逐层列目录
    dir_cache.update(plan.get("dirIds", {}))

    def ensure_path(dir_path):
        """确保 newPath 的父目录链存在，返回末级目录 fileId"""
        if dir_path in dir_cache:
            return dir_cache[dir_path]
        parent_path, _, name = dir_path.rpartition("/")
        parent_id = ensure_path(parent_path)
        if args.dry_run:
            fid = f"<new:{dir_path}>"
        else:
            existed = c.find_child_dir(parent_id, name)
            fid = existed if existed is not None else c.mkdir(parent_id, name)
            if existed is None:
                log({"action": "mkdir", "dirId": fid, "path": dir_path})
        dir_cache[dir_path] = fid
        return fid

    ok = skipped = failed = 0
    for i, e in enumerate(entries, 1):
        fid, old, new = e["fileId"], e["oldPath"], e["newPath"]
        if fid in done:
            skipped += 1
            continue
        dir_path, _, new_name = new.rpartition("/")
        new_name = sanitize(new_name)
        old_dir, _, old_name = old.rpartition("/")
        try:
            print(f"[{i}/{len(entries)}] {old}\n{'':>12}→ {dir_path}/{new_name}")
            target_dir = ensure_path(dir_path.strip("/"))
            if args.dry_run:
                ok += 1
                continue
            if old_dir.strip("/") != dir_path.strip("/"):
                old_parent = e.get("oldParentId")
                c.move(fid, target_dir)
                log({"action": "move", "fileId": fid, "fromParentPath": old_dir,
                     "fromParentId": old_parent, "toParentId": target_dir})
            if old_name != new_name:
                c.rename(fid, new_name)
                log({"action": "rename", "fileId": fid, "fromName": old_name, "toName": new_name})
            log({"action": "done", "fileId": fid})
            ok += 1
        except RuntimeError as err:
            failed += 1
            print(f"  失败：{err}", file=sys.stderr)
            log({"action": "error", "fileId": fid, "error": str(err)})

    mode = "（dry-run，未实际执行）" if args.dry_run else ""
    print(f"\n完成{mode}：成功 {ok}，跳过(已完成) {skipped}，失败 {failed}")
    if not args.dry_run:
        print(f"回滚日志：{log_path}")


if __name__ == "__main__":
    main()
