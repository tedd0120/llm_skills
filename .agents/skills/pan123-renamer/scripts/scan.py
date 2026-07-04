# -*- coding: utf-8 -*-
"""扫描 123 云盘目录树，输出视频文件清单 JSON。

用法:
    python scan.py                     # 全盘扫描
    python scan.py --parent 12345     # 只扫描指定目录（试跑用）
    python scan.py --out output/pan123_tree.json

输出 JSON 结构:
{
  "scannedAt": "...", "rootId": 0,
  "files": [ {"fileId", "name", "path", "parentFileId", "size", "isVideo"} ... ],
  "dirs":  [ {"fileId", "name", "path", "parentFileId"} ... ]
}
files 只含视频及同目录的字幕/nfo 等相关文件；空目录与无关文件不输出。
"""
import argparse
import json
import sys
import time
from pathlib import Path

from pan123_client import Pan123Client

VIDEO_EXT = {"mkv", "mp4", "ts", "m2ts", "avi", "iso", "rmvb", "rm", "wmv",
             "flv", "mov", "mpg", "mpeg", "webm", "vob", "m4v", "3gp", "strm"}
SIDECAR_EXT = {"srt", "ass", "ssa", "sub", "sup", "idx", "nfo", "jpg", "png"}


def ext_of(name):
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", type=int, default=0, help="起始目录 fileId，默认 0=根目录")
    ap.add_argument("--out", default=str(Path(__file__).parent / "output" / "pan123_tree.json"))
    args = ap.parse_args()

    c = Pan123Client()
    files, dirs = [], []
    queue = [(args.parent, "")]  # (fileId, 路径前缀)
    scanned = 0
    while queue:
        parent_id, prefix = queue.pop(0)
        try:
            items = c.list_dir(parent_id)
        except RuntimeError as e:
            print(f"警告：列目录 {prefix or '/'} 失败：{e}", file=sys.stderr)
            continue
        scanned += 1
        if scanned % 20 == 0:
            print(f"  已扫描 {scanned} 个目录，发现视频 {sum(f['isVideo'] for f in files)} 个...")
        dir_files = []
        for f in items:
            path = f"{prefix}/{f['filename']}"
            if f.get("type") == 1:
                dirs.append({"fileId": f["fileId"], "name": f["filename"],
                             "path": path, "parentFileId": parent_id})
                queue.append((f["fileId"], path))
            else:
                e = ext_of(f["filename"])
                if e in VIDEO_EXT or e in SIDECAR_EXT:
                    dir_files.append({"fileId": f["fileId"], "name": f["filename"],
                                      "path": path, "parentFileId": parent_id,
                                      "size": f.get("size", 0), "isVideo": e in VIDEO_EXT})
        files.extend(dir_files)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "scannedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rootId": args.parent, "files": files, "dirs": dirs,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    n_video = sum(f["isVideo"] for f in files)
    print(f"完成：扫描 {scanned} 个目录，视频 {n_video} 个，附属文件 {len(files) - n_video} 个")
    print(f"结果已写入 {out}")


if __name__ == "__main__":
    main()
