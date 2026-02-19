"""Bookmark / Table of Contents extraction."""

from __future__ import annotations

import fitz


class BookmarkExtractor:
    """Extract the PDF bookmark tree and render as a Markdown TOC."""

    @staticmethod
    def extract_raw(doc: fitz.Document) -> list[str]:
        """Return bookmark titles as a plain list (for metadata), or empty list."""
        toc = doc.get_toc(simple=True)
        if not toc:
            return []
        return [title.strip() for _, title, _ in toc if title and title.strip()]

    @staticmethod
    def extract(doc: fitz.Document) -> str:
        """Return a Markdown TOC section built from the PDF's outline, or empty string."""
        toc = doc.get_toc(simple=True)  # [(level, title, page), ...]
        if not toc:
            return ""

        # Filter out entries with empty / whitespace-only titles
        toc = [(lvl, title.strip(), pg) for lvl, title, pg in toc if title and title.strip()]
        if not toc:
            return ""

        lines: list[str] = ["## 📑 Table of Contents\n"]
        for level, title, page in toc:
            indent = "  " * (level - 1)
            lines.append(f"{indent}- [{title}](#page-{page})")
        lines.append("")  # trailing newline
        return "\n".join(lines)

