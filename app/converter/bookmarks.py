"""Bookmark / Table of Contents extraction."""

from __future__ import annotations

import fitz


class BookmarkExtractor:
    """Extract the PDF bookmark tree and render as a Markdown TOC."""

    @staticmethod
    def extract(doc: fitz.Document) -> str:
        """Return a Markdown TOC section built from the PDF's outline, or empty string."""
        toc = doc.get_toc(simple=True)  # [(level, title, page), ...]
        if not toc:
            return ""

        lines: list[str] = ["## 📑 Table of Contents\n"]
        for level, title, page in toc:
            indent = "  " * (level - 1)
            lines.append(f"{indent}- [{title}](#page-{page})")
        lines.append("")  # trailing newline
        return "\n".join(lines)
