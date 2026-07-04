# -*- coding: utf-8 -*-
"""按回滚日志逆向恢复重命名/移动操作。

用法:
    python rollback.py output/rollback_log.jsonl [--dry-run]

- rename → 改回原名
- move   → 移回原目录（需日志中有 fromParentId，方案条目里带 oldParentId 才会记录）
- mkdir  → 不删除（新建的目录留空即可，避免误删）
"""
import argparse
import json
import sys
from pathlib import Path

from pan123_client import Pan123Client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", help="rollback_log.jsonl 路径")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    records = [json.loads(x) for x in Path(args.log).read_text(encoding="utf-8").splitlines() if x.strip()]
    c = None if args.dry_run else Pan123Client()
    ok = skipped = failed = 0

    for rec in reversed(records):
        act = rec.get("action")
        try:
            if act == "rename":
                print(f"改回：[{rec['fileId']}] {rec['toName']} → {rec['fromName']}")
                if not args.dry_run:
                    c.rename(rec["fileId"], rec["fromName"])
                ok += 1
            elif act == "move":
                if not rec.get("fromParentId"):
                    print(f"跳过 move 回滚（缺少 fromParentId）：fileId={rec['fileId']} "
                          f"原目录 {rec.get('fromParentPath')}", file=sys.stderr)
                    skipped += 1
                    continue
                print(f"移回：[{rec['fileId']}] → {rec.get('fromParentPath')}")
                if not args.dry_run:
                    c.move(rec["fileId"], rec["fromParentId"])
                ok += 1
            else:
                skipped += 1
        except RuntimeError as e:
            failed += 1
            print(f"  失败：{e}", file=sys.stderr)

    print(f"\n回滚完成{'（dry-run）' if args.dry_run else ''}：成功 {ok}，跳过 {skipped}，失败 {failed}")
    if failed == 0 and not args.dry_run:
        print(f"建议将 {args.log} 改名归档，避免影响下次 apply 的断点续跑判断")


if __name__ == "__main__":
    main()
