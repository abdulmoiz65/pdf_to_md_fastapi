"""Bullet and numbered list detection and normalisation."""

from __future__ import annotations

import re


class ListDetector:
    """Detect and normalise list items in text lines."""

    _BULLET_RE = re.compile(r"^\s*[•●○◦▪▸‣⁃\-\*\+]\s+")
    _NUMBERED_RE = re.compile(r"^\s*(\d+[\.\)]\s+|[a-zA-Z][\.\)]\s+)")

    @staticmethod
    def is_bullet_item(text: str) -> bool:
        return bool(ListDetector._BULLET_RE.match(text))

    @staticmethod
    def is_numbered_item(text: str) -> bool:
        return bool(ListDetector._NUMBERED_RE.match(text))

    @staticmethod
    def normalize_bullet(text: str) -> str:
        """Replace any bullet marker with standard ``- ``."""
        return ListDetector._BULLET_RE.sub("- ", text, count=1)

    @staticmethod
    def normalize_numbered(text: str) -> str:
        """Keep the number but ensure standard ``1. `` style."""
        m = ListDetector._NUMBERED_RE.match(text)
        if m:
            prefix = m.group(0).strip()
            rest = text[m.end():]
            # convert "1)" → "1."
            prefix = re.sub(r"(\d+)\)", r"\1.", prefix)
            return f"{prefix} {rest}"
        return text

    @staticmethod
    def process_line(text: str) -> str:
        """Return a normalised list line if applicable, else return as-is."""
        if ListDetector.is_bullet_item(text):
            return ListDetector.normalize_bullet(text)
        if ListDetector.is_numbered_item(text):
            return ListDetector.normalize_numbered(text)
        return text
