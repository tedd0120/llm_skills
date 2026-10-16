#!/usr/bin/env python3
"""汇总 Claude Code 近 7 天与近 30 天的 token 用量。

数据来自 ccusage 的 `claude daily` 报表，它读取 ~/.claude/projects 下的会话记录，
已归档和已删除的会话只要记录文件还在都会计入。
"""
import datetime as dt
import json
import shutil
import subprocess
import sys

FIELDS = ("inputTokens", "outputTokens", "cacheCreationTokens", "cacheReadTokens", "totalTokens", "totalCost")


def load_daily():
    npx = shutil.which("npx")
    if not npx:
        sys.exit("未找到 npx，请先安装 Node.js。")
    proc = subprocess.run(
        [npx, "-y", "ccusage@latest", "claude", "daily", "--json", "--offline"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        sys.exit(f"ccusage 运行失败：\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)["daily"]


def total(rows, since):
    sums = dict.fromkeys(FIELDS, 0)
    for row in rows:
        if row["date"] >= since:
            for k in FIELDS:
                sums[k] += row.get(k) or 0
    return sums


def fmt(n):
    if n >= 1e8:
        return f"{n / 1e8:.2f} 亿"
    if n >= 1e4:
        return f"{n / 1e4:.0f} 万"
    return f"{n:,.0f}"


def main():
    rows = [{**r, "date": r.get("date") or r["period"]} for r in load_daily()]
    if not rows:
        print("本机没有 Claude Code 用量记录。")
        return
    today = dt.date.today()
    periods = [
        (f"近 7 天（{today - dt.timedelta(days=6):%m/%d} 起）", (today - dt.timedelta(days=6)).isoformat()),
        (f"近 30 天（{today - dt.timedelta(days=29):%m/%d} 起）", (today - dt.timedelta(days=29)).isoformat()),
    ]
    print(f"运行时点：{dt.datetime.now():%Y-%m-%d %H:%M:%S}\n")
    print("| 时段 | 总 token | 输入 | 输出 | 写入缓存 | 读取缓存 | 估算费用 |")
    print("|---|---|---|---|---|---|---|")
    for label, since in periods:
        s = total(rows, since)
        print(f"| {label} | {fmt(s['totalTokens'])} | {fmt(s['inputTokens'])} | {fmt(s['outputTokens'])} "
              f"| {fmt(s['cacheCreationTokens'])} | {fmt(s['cacheReadTokens'])} | ${s['totalCost']:,.0f} |")


if __name__ == "__main__":
    main()
