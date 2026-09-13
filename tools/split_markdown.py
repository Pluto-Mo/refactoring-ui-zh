#!/usr/bin/env python3
"""Split the converted book Markdown into one source file per chapter.

Reads the English Markdown produced by ``pdf_to_markdown.py`` and writes one
file per level-1 heading, so translators can work on chapters independently.

Example:
    python split_markdown.py --book "out/Refactoring UI.md" \
        --out-en work/en --out-zh work/zh
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil

from chapters import CHAPTER_STEMS


def split(book: pathlib.Path) -> tuple[str, list[str]]:
    text = book.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=# )", text)
    return parts[0], parts[1:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--book", type=pathlib.Path, required=True, help="converted English Markdown")
    parser.add_argument("--out-en", type=pathlib.Path, required=True, help="where the per-chapter English sources go")
    parser.add_argument("--out-zh", type=pathlib.Path, help="output folder for the translation (assets get copied here)")
    parser.add_argument("--assets", type=pathlib.Path, help="assets folder to copy; defaults to <book dir>/assets")
    args = parser.parse_args(argv)

    front, chapters = split(args.book)
    if len(chapters) != len(CHAPTER_STEMS):
        raise SystemExit(f"expected {len(CHAPTER_STEMS)} chapters, found {len(chapters)}")

    args.out_en.mkdir(parents=True, exist_ok=True)
    (args.out_en / "00-frontmatter.md").write_text(front, encoding="utf-8")

    for stem, chapter in zip(CHAPTER_STEMS, chapters):
        title = chapter.splitlines()[0].lstrip("# ").strip()
        (args.out_en / f"{stem}.md").write_text(chapter, encoding="utf-8")
        print(
            f"{stem:16s} title={title:34s} "
            f"words={len(re.findall(r'[A-Za-z]+', chapter)):5d} "
            f"images={chapter.count('![](assets/'):3d}"
        )

    if args.out_zh:
        args.out_zh.mkdir(parents=True, exist_ok=True)
        assets_src = args.assets or args.book.parent / "assets"
        assets_dst = args.out_zh / "assets"
        if not assets_dst.exists():
            shutil.copytree(assets_src, assets_dst)
        print(f"\nassets copied to {assets_dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
