#!/usr/bin/env python3
"""Scan final text surfaces without echoing matched terms."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unicodedata


MAX_TERMS_BYTES = 1024 * 1024
MAX_TERMS = 4096
MAX_TERM_CHARS = 4096
MAX_SURFACE_BYTES = 16 * 1024 * 1024


class ScanError(ValueError):
    """A scan input failed a safety or format check."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def read_regular(path: Path, limit: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise ScanError("unreadable_file") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ScanError("not_regular_file")
    if before.st_size > limit:
        raise ScanError("file_too_large")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ScanError("unreadable_file") from exc

    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode):
            raise ScanError("not_regular_file")
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ScanError("file_changed_during_scan")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(limit + 1)
        if len(data) > limit:
            raise ScanError("file_too_large")
        return data
    except OSError as exc:
        raise ScanError("unreadable_file") from exc
    finally:
        os.close(descriptor)


def decode_utf8(path: Path, limit: int) -> str:
    try:
        return read_regular(path, limit).decode("utf-8-sig", errors="strict")
    except UnicodeError as exc:
        raise ScanError("invalid_utf8") from exc


def contains_review_chars(value: str) -> bool:
    bidi_controls = {"LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI", "BN"}
    return any(
        unicodedata.category(character) == "Cf"
        or unicodedata.bidirectional(character) in bidi_controls
        for character in value
    )


def load_terms(path: Path) -> list[str]:
    raw = [line.strip() for line in decode_utf8(path, MAX_TERMS_BYTES).splitlines()]
    raw = [term for term in raw if term]
    if not raw:
        raise ScanError("terms_file_empty")
    if len(raw) > MAX_TERMS:
        raise ScanError("too_many_terms")
    if any(len(term) > MAX_TERM_CHARS for term in raw):
        raise ScanError("term_too_long")
    if any(contains_review_chars(term) for term in raw):
        raise ScanError("unsafe_terms_characters")
    return list(dict.fromkeys(normalize(term) for term in raw))


def relative_surface(path: Path, root: Path | None) -> str:
    if root is None:
        return path.name
    absolute = Path(os.path.abspath(path))
    try:
        return absolute.relative_to(root).as_posix()
    except ValueError as exc:
        raise ScanError("path_outside_root") from exc


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check final text files and paths for exact terms.")
    parser.add_argument("--terms-file", required=True, type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    try:
        terms = load_terms(args.terms_file)
        root = Path(os.path.abspath(args.root)) if args.root else None
        if root is not None and not root.is_dir():
            raise ScanError("scan_root_not_directory")
    except ScanError as exc:
        emit({"status": "ERROR", "reason_code": exc.code})
        return 2

    failures: list[dict[str, object]] = []
    reviews: list[dict[str, object]] = []
    checked = 0

    for index, path in enumerate(args.paths, start=1):
        try:
            surface_path = relative_surface(path, root)
            content = decode_utf8(path, MAX_SURFACE_BYTES)
        except ScanError as exc:
            emit({"status": "ERROR", "files_checked": checked, "file_index": index, "reason_code": exc.code})
            return 2

        checked += 1
        normalized_content = normalize(content)
        normalized_path = normalize(surface_path)
        content_matches = {term for term in terms if term in normalized_content}
        path_matches = {term for term in terms if term in normalized_path}
        matched = content_matches | path_matches

        if matched:
            surfaces = []
            if content_matches:
                surfaces.append("content")
            if path_matches:
                surfaces.append("relative_path" if root else "filename")
            failures.append({"file_index": index, "matched_term_count": len(matched), "surfaces": surfaces})

        review_surfaces = []
        if contains_review_chars(content):
            review_surfaces.append("content")
        if contains_review_chars(surface_path):
            review_surfaces.append("relative_path" if root else "filename")
        if review_surfaces:
            reviews.append({"file_index": index, "reason_code": "default_ignorable_or_bidi", "surfaces": review_surfaces})

    if failures:
        emit({"status": "FAIL", "files_checked": checked, "failures": failures, "reviews": reviews})
        return 1
    if reviews:
        emit({"status": "REVIEW", "files_checked": checked, "failures": [], "reviews": reviews})
        return 1
    emit({"status": "PASS", "files_checked": checked, "failures": [], "reviews": []})
    return 0


if __name__ == "__main__":
    sys.exit(main())
