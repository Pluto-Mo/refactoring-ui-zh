#!/usr/bin/env python3
"""Convert a text-based PDF into a Markdown file plus an assets/ folder.

Tuned for the layout of "Refactoring UI" (single text column, GraphikApp font
family, images placed as separate full-width blocks), but every classification
threshold is a parameter so it can be retargeted to a similar PDF.

Usage:
    python pdf_to_markdown.py input.pdf -o OUTPUT_DIR [--pages 8-30]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass

import pymupdf

# --- classification thresholds (point sizes / y positions in the PDF) --------
HEADER_SIZE = 8.0  # running header / page number
HEADER_BAND = 60.0  # y range in which the running header lives
CODE_MAX_SIZE = 8.5  # monospaced snippets below body size
H3_MIN_SIZE = 11.5  # size-12 semibold subheads
H2_MIN_SIZE = 18.0  # size-22 section titles
H1_MIN_SIZE = 24.0  # size-28 chapter titles
PARA_GAP = 19.0  # vertical gap (pt) between lines that starts a new paragraph

BULLET_RE = re.compile(r"^([\u2022\u25cf\u25aa\u00b7])\s+")
NUMBERED_RE = re.compile(r"^(\d{1,2})[.)]\s+\S")
# the bullet glyph is sometimes its own text line inside the paragraph block
LONE_MARKER_RE = re.compile(r"^[\u2022\u25cf\u25aa\u00b7]$|^\d{1,2}[.)]$")
TOC_DOT_RE = re.compile(r"\.\s?\.\s?\.")
TERMINAL_CHARS = ".!?:\u201d\u2019\"')"


def list_kind_of(text: str) -> str:
    text = text.strip()
    if BULLET_RE.match(text) or LONE_MARKER_RE.match(text):
        return "ul" if not text[0].isdigit() else "ol"
    if NUMBERED_RE.match(text):
        return "ol"
    return ""


@dataclass
class Item:
    kind: str  # "text" | "image" | "heading" | "code"
    markdown: str
    y0: float
    page: int
    end_page: int = 0
    image_bytes: bytes | None = None
    image_ext: str = "png"
    level: int = 0
    list_kind: str = ""

    def __post_init__(self) -> None:
        if not self.end_page:
            self.end_page = self.page


def span_is_bold(span) -> bool:
    name = span["font"].lower()
    return "bold" in name or "semibold" in name


def span_is_italic(span) -> bool:
    name = span["font"].lower()
    return "italic" in name or "oblique" in name


def escape_text(text: str) -> str:
    """Minimal escaping so Markdown syntax characters in the book survive."""
    text = text.replace("\\", "\\\\")
    return re.sub(r"([*_`\[\]])", r"\\\1", text)


def line_to_markdown(line) -> str:
    """Render one PDF text line, preserving bold/italic spans as Markdown."""
    parts: list[str] = []
    for span in line["spans"]:
        text = span["text"]
        if not text:
            continue
        stripped = text.strip()
        if not stripped:
            parts.append(text)
            continue
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        body = escape_text(stripped)
        bold, italic = span_is_bold(span), span_is_italic(span)
        if bold and italic:
            body = f"***{body}***"
        elif bold:
            body = f"**{body}**"
        elif italic:
            body = f"*{body}*"
        parts.append(lead + body + trail)
    return "".join(parts).strip()


def classify(line, page_height: float) -> str:
    spans = [s for s in line["spans"] if s["text"].strip()]
    if not spans:
        return "skip"
    size = max(s["size"] for s in spans)
    y0 = line["bbox"][1]
    in_margin = y0 < HEADER_BAND or y0 > page_height - HEADER_BAND
    if abs(size - HEADER_SIZE) < 0.2 and in_margin:
        return "skip"  # running header / page number
    if size >= H1_MIN_SIZE:
        return "heading1"
    if size >= H2_MIN_SIZE:
        return "heading2"
    if size >= H3_MIN_SIZE:
        return "heading3"
    if size <= CODE_MAX_SIZE:
        return "code"
    return "text"


def collect_items(doc, pages: list[int]) -> tuple[list[Item], list[int]]:
    items: list[Item] = []
    skipped_toc: list[int] = []

    for page_no in pages:
        page = doc[page_no]
        raw = page.get_text()
        # printed table of contents: dot leaders everywhere -> rebuilt from the outline
        if TOC_DOT_RE.search(raw) and raw.count(".") > 40:
            skipped_toc.append(page_no + 1)
            continue

        blocks = page.get_text("dict")["blocks"]
        blocks = sorted(blocks, key=lambda b: (round(b["bbox"][1], 1), b["bbox"][0]))

        for block in blocks:
            if block["type"] == 1:
                items.append(
                    Item(
                        kind="image",
                        markdown="",
                        y0=block["bbox"][1],
                        page=page_no + 1,
                        image_bytes=block.get("image"),
                        image_ext=block.get("ext", "png"),
                    )
                )
                continue

            for line in block["lines"]:
                kind = classify(line, page.rect.height)
                if kind == "skip":
                    continue
                md = line_to_markdown(line)
                if not md:
                    continue
                level = {"heading1": 1, "heading2": 2, "heading3": 3}.get(kind, 0)
                items.append(
                    Item(
                        kind="heading" if level else kind,
                        markdown=md,
                        y0=line["bbox"][1],
                        page=page_no + 1,
                        level=level,
                    )
                )
    return items, skipped_toc


def _ends_sentence(text: str) -> bool:
    stripped = text.rstrip()
    return bool(stripped) and stripped[-1] in TERMINAL_CHARS


def merge_into_blocks(items: list[Item]) -> list[Item]:
    """Merge consecutive body/code lines into paragraphs; keep lists itemised."""
    merged: list[Item] = []
    current: Item | None = None
    prev_y0 = 0.0

    def flush() -> None:
        nonlocal current
        if current is not None:
            current.list_kind = list_kind_of(current.markdown)
            merged.append(current)
            current = None

    for item in items:
        if item.kind in ("image", "heading"):
            flush()
            merged.append(item)
            continue

        item.list_kind = list_kind_of(item.markdown)

        if current is None:
            current, prev_y0 = item, item.y0
            continue

        same_kind = current.kind == item.kind
        same_page = item.page == current.end_page
        new_list_item = item.list_kind != ""
        too_far = same_page and (item.y0 - prev_y0) > PARA_GAP
        crosses_pages = (not same_page) and item.page == current.end_page + 1
        joinable = crosses_pages and not _ends_sentence(current.markdown) and not current.list_kind

        if not same_kind or new_list_item or too_far or (not same_page and not joinable):
            flush()
            current = item
        else:
            joiner = "" if current.markdown.endswith("-") else " "
            current.markdown = current.markdown.rstrip() + joiner + item.markdown.lstrip()
            current.end_page = item.page

        prev_y0 = item.y0

    flush()
    return merged


def render(blocks: list[Item], out_dir: pathlib.Path) -> str:
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    counters: dict[int, int] = {}
    out: list[str] = []
    last_page = 0

    def page_anchor(item: Item) -> None:
        nonlocal last_page
        if item.page != last_page:
            out.append(f"<!-- p{item.page} -->")
            out.append("")
            last_page = item.page

    for idx, item in enumerate(blocks):
        nxt = blocks[idx + 1] if idx + 1 < len(blocks) else None

        if item.kind == "image" and item.image_bytes:
            page_anchor(item)
            counters[item.page] = counters.get(item.page, 0) + 1
            name = f"p{item.page:03d}-{counters[item.page]:02d}.{item.image_ext}"
            (assets_dir / name).write_bytes(item.image_bytes)
            out.append(f"![](assets/{name})")
            out.append("")
            continue

        if item.kind == "heading":
            page_anchor(item)
            text = item.markdown.replace("**", "").replace("*", "")
            out.append("#" * item.level + " " + text)
            out.append("")
            continue

        if item.kind == "code":
            page_anchor(item)
            out.append("`" + item.markdown.replace("`", "") + "`")
            out.append("")
            continue

        page_anchor(item)
        text = item.markdown.strip()
        if item.list_kind == "ul":
            text = BULLET_RE.sub("- ", text)
        out.append(text)
        if item.end_page > item.page:
            out[-1] += f" <!-- p{item.end_page} -->"
            last_page = item.end_page
        next_same_list = nxt is not None and nxt.list_kind == item.list_kind and item.list_kind != ""
        if not next_same_list:
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def build_front_matter(doc) -> str:
    lines = [
        "---",
        'title: "Refactoring UI"',
        'authors: ["Adam Wathan", "Steve Schoger"]',
        'source: "Refactoring UI.pdf"',
        "---",
        "",
    ]
    toc = doc.get_toc()
    if toc:
        lines += ["## Contents", ""]
        for level, title, page in toc:
            if level == 1:
                lines.append(f"- **{title}** — p{page}")
            elif level == 2:
                lines.append(f"  - {title} — p{page}")
        lines.append("")
    return "\n".join(lines) + "\n"


def parse_pages(spec: str, total: int) -> list[int]:
    if not spec:
        return list(range(total))
    pages: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            pages.extend(range(int(a) - 1, int(b) if b else total))
        else:
            pages.append(int(chunk) - 1)
    return [p for p in pages if 0 <= p < total]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=pathlib.Path)
    parser.add_argument("-o", "--out", type=pathlib.Path, required=True)
    parser.add_argument("--pages", default="", help='e.g. "8-30" or "1,4,9-12" (1-based, inclusive)')
    parser.add_argument("--name", default=None, help="output markdown file stem")
    args = parser.parse_args(argv)

    doc = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, doc.page_count)
    out_dir, stem = args.out, args.name or args.pdf.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    items, skipped_toc = collect_items(doc, pages)
    blocks = merge_into_blocks(items)
    body = render(blocks, out_dir)
    header = build_front_matter(doc) if not args.pages else ""
    (out_dir / f"{stem}.md").write_text(header + body, encoding="utf-8")

    print(f"pages converted : {len(pages) - len(skipped_toc)}")
    print(f"skipped (printed TOC pages): {skipped_toc or 'none'}")
    print(f"headings        : {sum(1 for b in blocks if b.kind == 'heading')}")
    print(f"paragraphs/list : {sum(1 for b in blocks if b.kind in ('text', 'code'))}")
    print(f"images          : {sum(1 for b in blocks if b.kind == 'image')}")
    print(f"markdown        : {out_dir / (stem + '.md')}")
    print(f"assets          : {out_dir / 'assets'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
