#!/usr/bin/env python3
"""Strip the leading level-1 heading and all page anchors from chapter files.

The chapter title is already carried by the file name, and the ``<!-- pN -->``
comments only mattered while cross-checking the translation against the PDF.

Example:
    python cleanup_chapters.py --dir work/zh
"""

from __future__ import annotations

import argparse
import pathlib
import re

from chapters import chapter_paths

STANDALONE_ANCHOR = re.compile(r"^<!-- p\d+ -->$")
INLINE_ANCHOR = re.compile(r"\s*<!-- p\d+ -->")


def clean(text: str) -> tuple[str, int, int]:
    lines = text.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)
    dropped_heading = 0
    if lines and lines[0].startswith("# "):
        lines.pop(0)
        dropped_heading = 1
        while lines and not lines[0].strip():
            lines.pop(0)

    anchors = 0
    kept: list[str] = []
    for line in lines:
        if STANDALONE_ANCHOR.fullmatch(line.strip()):
            anchors += 1
            continue
        if INLINE_ANCHOR.search(line):
            anchors += len(INLINE_ANCHOR.findall(line))
            line = INLINE_ANCHOR.sub("", line)
        kept.append(line.rstrip())

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip() + "\n"
    return text, dropped_heading, anchors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=pathlib.Path, required=True, help="folder holding the chapter files")
    parser.add_argument("--dry-run", action="store_true", help="report what would change without writing")
    args = parser.parse_args(argv)

    for path in chapter_paths(args.dir):
        if not path.exists():
            print(f"{path.name}: missing, skipped")
            continue
        original = path.read_text(encoding="utf-8")
        cleaned, heading, anchors = clean(original)
        if not args.dry_run:
            path.write_text(cleaned, encoding="utf-8")
        action = "would remove" if args.dry_run else "removed"
        print(
            f"{path.name:16s} {action} h1={heading} anchors={anchors:3d} "
            f"images={cleaned.count('![](assets/'):3d} {len(original):6d} -> {len(cleaned):6d} chars"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
