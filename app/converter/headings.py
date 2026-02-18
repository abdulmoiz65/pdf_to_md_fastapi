"""Heading-level detection based on font-size ratios."""

from __future__ import annotations


class HeadingDetector:
    """Detect heading levels from font sizes relative to page average."""

    @staticmethod
    def detect_heading(font_size: float, avg_size: float, is_bold: bool = False) -> str:
        """Return a Markdown heading prefix or empty string.

        Rules:
          - ratio >= 1.8  → h1 (``# ``)
          - ratio >= 1.35 → h2 (``## ``)
          - ratio >= 1.15 and bold → h3 (``### ``)
        """
        if avg_size <= 0:
            return ""
        ratio = font_size / avg_size
        if ratio >= 1.8:
            return "# "
        if ratio >= 1.35:
            return "## "
        if ratio >= 1.15 and is_bold:
            return "### "
        return ""
