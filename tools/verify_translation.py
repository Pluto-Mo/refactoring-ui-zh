#!/usr/bin/env python3
"""Structural QA: compare the English source with the Chinese translation.

The translation must preserve the document structure exactly, so the checks
that matter are the ones that survive any later formatting cleanup: heading
levels 2 and 3, image references, paragraphs and list items. Level-1 headings
and ``<!-- pN -->`` page anchors are reported for information only, because
they are deliberately stripped from the shipped chapters.

Example:
    python verify_translation.py --en work/en --zh work/zh
"""

from __future__ import annotations

import argparse
import pathlib
import re

from chapters import CHAPTER_STEMS, chapter_paths

IMAGE_LINK = re.compile(r"!\[\]\(assets/[^)]+\)")
ANCHOR = re.compile(r"<!-- p\d+ -->")

# Pairs that are heuristically suspicious when both appear. Some of them are
# legitimately distinct in this book (hierarchy vs. depth, line-height vs. the
# author's looser "line spacing"), so treat a hit as "go look at it", not as a
# failure. See docs/翻译规范与术语表.md for the reasoning.
VARIANTS = {
    "blank/whitespace": (r"\u7559\u767d", r"\u7a7a\u767d"),
    "shade/tone": (r"\u8272\u9636", r"\u8272\u8c03"),
    "weight/thickness": (r"\u5b57\u91cd", r"\u7c97\u7ec6"),
    "hierarchy/depth": (r"\u5c42\u7ea7", r"\u5c42\u6b21"),
    "inner-padding": (r"\u5185\u8fb9\u8ddd", r"\u5185\u886c"),
    "outer-margin": (r"\u5916\u8fb9\u8ddd", r"\u5916\u8ddd"),
    "grid": (r"\u6805\u683c", r"\u7f51\u683c"),
    "line-height": (r"\u884c\u9ad8", r"\u884c\u8ddd"),
}

REQUIRED_KEYS = ("h2", "h3", "img", "para", "list")


def stats(path: pathlib.Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    body = IMAGE_LINK.sub("", ANCHOR.sub("", text))
    paragraphs = [
        line
        for line in body.splitlines()
        if line.strip() and not line.startswith("#") and line.strip() != "---"
    ]
    return {
        "h1": len(re.findall(r"(?m)^# ", text)),
        "h2": len(re.findall(r"(?m)^## ", text)),
        "h3": len(re.findall(r"(?m)^### ", text)),
        "img": text.count("![](assets/"),
        "anchor": len(ANCHOR.findall(text)),
        "para": len(paragraphs),
        "list": len([p for p in paragraphs if re.match(r"^(- |\d+\. )", p)]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--en", type=pathlib.Path, required=True, help="folder with the per-chapter English sources")
    parser.add_argument("--zh", type=pathlib.Path, required=True, help="folder with the translated chapters")
    args = parser.parse_args(argv)

    problems = 0
    totals: dict[str, list[int]] = {k: [0, 0] for k in REQUIRED_KEYS}
    header = f"{'chapter':10s} {'h2':>12s} {'h3':>12s} {'img':>12s} {'para':>12s} {'list':>12s}  status"
    print(header)
    print("-" * len(header))

    for stem, en_path, zh_path in zip(CHAPTER_STEMS, chapter_paths(args.en), chapter_paths(args.zh)):
        if not zh_path.exists():
            print(f"{stem:10s}  MISSING {zh_path}")
            problems += 1
            continue
        en, zh = stats(en_path), stats(zh_path)
        flags = []
        cells = []
        for key in REQUIRED_KEYS:
            totals[key][0] += en[key]
            totals[key][1] += zh[key]
            cells.append(f"{zh[key]:5d}/{en[key]:<5d}")
            if en[key] != zh[key]:
                flags.append(f"{key} {zh[key]}!={en[key]}")
        if flags:
            problems += 1
        print(f"{stem:10s} " + " ".join(cells) + ("  OK" if not flags else "  MISMATCH " + ", ".join(flags)))

    print()
    print("totals (zh/en):", {k: f"{v[1]}/{v[0]}" for k, v in totals.items()})
    print()

    whole = "\n".join(
        path.read_text(encoding="utf-8")
        for path in chapter_paths(args.zh)
        if path.exists()
    )
    print("competing term usage (heuristic - review any pair where both are used):")
    for label, pats in VARIANTS.items():
        counts = [len(re.findall(p, whole)) for p in pats]
        mark = "  <-- both used, review" if min(counts) else ""
        print(f"   {label:18s} {counts}{mark}")

    print()
    print("leftover English body lines:")
    found = 0
    for path in chapter_paths(args.zh):
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            text = line.strip()
            if not text or text.startswith(("#", "!", "<!--", "---", "- ", "*")):
                continue
            words = re.findall(r"[A-Za-z]+", text)
            if len(words) >= 6 and len(words) / max(len(text), 1) > 0.35:
                print(f"   {path.name}:{number}  {text[:80]}")
                found += 1
    print(f"   {found} suspicious line(s)")
    print()
    print("PROBLEMS:", problems)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
