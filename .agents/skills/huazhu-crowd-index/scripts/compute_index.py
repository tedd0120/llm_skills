"""
华住人流量指数 - 计算与报告脚本（v2：每城一家汉庭）

读取 fetch_prices.py 产出的 raw.json。每个城市只锚定一家「汉庭」，计算：
  - 涨价倍数 = 该汉庭 目标日价 / 平日价
按涨价倍数降序给城市排名，倍数越高 → 该城节假日相对平日溢价越猛 → 人流越旺。
（每城单酒店，故不再有售罄率列；若首选汉庭节日售罄已在抓取阶段顺延，并以标注体现。）

输出 Markdown 报告（默认与 raw.json 同目录的 report.md），并打印到 stdout。
"""

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def compute_city(city_obj: dict) -> dict:
    """对单个城市（一家汉庭）计算涨价倍数。"""
    hotels = city_obj.get("hotels", [])
    h = hotels[0] if hotels else {}
    tp = h.get("target_price")
    bp = h.get("baseline_price")
    surge = (tp / bp) if (tp and bp and bp > 0) else None
    return {
        "city": city_obj.get("city", ""),
        "hotel": h.get("name", ""),
        "target_price": tp,
        "baseline_price": bp,
        "surge": surge,
        "sold_out": h.get("sold_out", False),
        "flagship_sold_out": h.get("flagship_sold_out", False),
        "has_data": bool(hotels),
    }


def build_report(raw: dict) -> str:
    target = raw.get("target_date", "?")
    baseline = raw.get("baseline_date", "?")
    rows = [compute_city(c) for c in raw.get("cities", [])]

    # 按涨价倍数降序（None 垫底）
    rows.sort(key=lambda r: r["surge"] if r["surge"] is not None else -1, reverse=True)

    lines = []
    lines.append("# 汉庭酒店涨价 → 城市人流量排名报告\n")
    lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 目标日期（节假日）：**{target}**")
    lines.append(f"- 平日基准日（节后第一个非节假周二）：**{baseline}**")
    lines.append("- 方法：每城锚定欢迎度最高的一家「汉庭」，对比同一家在两日的价格")
    lines.append("- 数据来源：携程（汉庭最低可订价）\n")

    lines.append("## 城市排名（按涨价倍数）\n")
    lines.append("| 排名 | 城市 | 涨价倍数 | 节日价 | 平日价 | 锚定汉庭 | 备注 |")
    lines.append("|:----:|:----|:----:|:----:|:----:|:----|:----|")
    for i, r in enumerate(rows, 1):
        surge = f"{r['surge']:.2f}×" if r["surge"] is not None else "—"
        tp = r["target_price"] if r["target_price"] else "—"
        bp = r["baseline_price"] if r["baseline_price"] else "—"
        note = []
        if not r["has_data"]:
            note.append("无数据")
        if r["flagship_sold_out"]:
            note.append("首选汉庭节日售罄,已顺延")
        if r["sold_out"]:
            note.append("售罄")
        lines.append(
            f"| {i} | {r['city']} | {surge} | {tp} | {bp} "
            f"| {r['hotel'] or '—'} | {'；'.join(note)} |"
        )

    lines.append("\n## 说明\n")
    lines.append("- **涨价倍数** = 该城欢迎度最高的一家汉庭「节假日最低价 ÷ 节后平日最低价」。"
                 "倍数越高，说明该城节假日相对平日溢价越猛 → 需求/人流越旺。")
    lines.append("- 每城固定锚定**同一家汉庭**两日对比（汉庭是华住最基础、每城必有的系列，跨城最可比）。")
    lines.append("- 若某城欢迎度最高的汉庭在节假日当天售罄/无报价，抓取阶段已自动顺延到下一家有报价的汉庭，"
                 "并在备注标「首选汉庭节日售罄」——这本身也是高需求信号。")
    lines.append("- 平日价取「节后第一个非节假日的周二」，作为需求回落的参照。\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="计算华住人流量指数并生成报告")
    parser.add_argument("--input", required=True, help="raw.json 路径")
    parser.add_argument("--output", default="", help="报告输出路径；留空则写到 raw.json 同目录 report.md")
    args = parser.parse_args()

    raw_path = Path(args.input)
    if not raw_path.exists():
        print(f"[✗] 输入文件不存在: {raw_path}", file=sys.stderr, flush=True)
        sys.exit(1)

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    report = build_report(raw)

    out_path = Path(args.output) if args.output else raw_path.parent / "report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    print(report, flush=True)
    print(f"\n[✓] 报告已保存 → {out_path}", flush=True)


if __name__ == "__main__":
    main()
