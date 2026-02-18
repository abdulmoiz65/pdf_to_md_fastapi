"""URL and hyperlink extraction."""

from __future__ import annotations

import re

import fitz


class URLExtractor:
    """Extract visible URLs from text and clickable hyperlinks from annotations."""

    _URL_RE = re.compile(r"https?://[^\s\)\]\>]+")

    @staticmethod
    def find_visible_urls(text: str) -> list[str]:
        """Return all http/https URLs found in the raw text."""
        return URLExtractor._URL_RE.findall(text)

    @staticmethod
    def extract_hyperlinks(page: fitz.Page) -> list[tuple[str, str, float]]:
        """Return (display_text, url, y_position) for every link annotation on the page."""
        results: list[tuple[str, str, float]] = []
        for link in page.get_links():
            uri = link.get("uri", "")
            if not uri:
                continue
            rect = link.get("from", fitz.Rect())
            # Try to get the visible text inside the link rect
            display = page.get_textbox(rect).strip() if rect else uri
            if not display:
                display = uri
            results.append((display, uri, rect.y0 if rect else 0))
        return results

    @staticmethod
    def markdown_url(text: str, url: str) -> str:
        """Format as a Markdown link."""
        return f"[{text}]({url})"

    @staticmethod
    def replace_urls_in_text(text: str) -> str:
        """Turn bare URLs in text into Markdown links."""
        def _repl(m: re.Match) -> str:
            url = m.group(0)
            return f"[{url}]({url})"
        return URLExtractor._URL_RE.sub(_repl, text)
