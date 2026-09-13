#!/usr/bin/env python3
"""Merge the chapter files into a single Markdown book (optional step).

The shipped translation keeps one file per chapter; this script is only for
producing a combined file when you want one. The table of contents is rebuilt
from the chapter files, so heading wording always matches the body text.

Example:
    python merge_book.py --dir work/zh --cover assets/p001-01.png
"""

from __future__ import annotations

import argparse
import pathlib
import re

from chapters import chapter_paths

ANCHOR = re.compile(r"<!-- p(\d+) -->")

HEADER = """---
title: "Refactoring UI（中文版）"
original_title: "Refactoring UI"
authors: ["Adam Wathan", "Steve Schoger"]
language: "zh-CN"
---

> 本中文版由机器翻译流程生成（分章翻译 + 术语表统一 + 全书一致性校对），仅供个人学习阅读。
> 原书版权归 Adam Wathan 与 Steve Schoger 所有。

"""


def build_toc(paths: list[pathlib.Path]) -> str:
    lines = ["## 目录", ""]
    for path in paths:
        body = path.read_text(encoding="utf-8").splitlines()
        anchors = [int(m.group(1)) for m in (ANCHOR.fullmatch(line.strip()) for line in body) if m]
        page = anchors[0] if anchors else 0
        for line in body:
            match = ANCHOR.fullmatch(line.strip())
            if match:
                page = int(match.group(1))
            elif line.startswith("## "):
                lines.append(f"- {line[3:].strip()} —— 第 {page} 页")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=pathlib.Path, required=True, help="folder holding the chapter files")
    parser.add_argument("--out", type=pathlib.Path, help="output file; defaults to <dir>/Refactoring UI (中文版).md")
    parser.add_argument("--cover", default="", help="optional cover image path relative to --dir")
    args = parser.parse_args(argv)

    paths = chapter_paths(args.dir)
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"missing chapter files: {missing}")

    header = HEADER + (f"![]({args.cover})\n\n" if args.cover else "")
    body = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in paths)
    merged = header + build_toc(paths) + "\n" + body + "\n"

    out = args.out or args.dir / "Refactoring UI (中文版).md"
    out.write_text(merged, encoding="utf-8")
    print(f"merged -> {out}")
    print(f"size: {len(merged.encode('utf-8'))/1024:.1f} KB, chapters: {len(paths)}")
    print("headings:", {n: len(re.findall(r"(?m)^#{%d} " % n, merged)) for n in (1, 2, 3)})
    print("images:", merged.count("![](assets/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
