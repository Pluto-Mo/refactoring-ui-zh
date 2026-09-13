"""Single source of truth for the chapter file names used by the pipeline.

Every stage (split -> translate -> verify -> cleanup -> merge) refers to
chapters by the same stem, so the list lives here and nowhere else.

The English source files produced by ``split_markdown.py`` and the Chinese
files produced by the translators intentionally share these stems.
"""

from __future__ import annotations

import pathlib

CHAPTER_STEMS = [
    "01 从零开始",
    "02 层级就是一切",
    "03 布局与间距",
    "04 文字设计",
    "05 色彩的运用",
    "06 营造层次感",
    "07 图片的运用",
    "08 收尾打磨",
    "09 持续进阶",
]


def chapter_paths(directory: pathlib.Path) -> list[pathlib.Path]:
    """Return the chapter files that exist in ``directory``, in book order."""
    return [directory / f"{stem}.md" for stem in CHAPTER_STEMS]


def missing(directory: pathlib.Path) -> list[str]:
    """Return the stems whose files are absent from ``directory``."""
    return [stem for stem, path in zip(CHAPTER_STEMS, chapter_paths(directory)) if not path.exists()]
