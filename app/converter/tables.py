"""Table detection and extraction to Markdown format."""

from __future__ import annotations

import fitz


class TableExtractor:
    """Detect and extract tables from a PDF page using PyMuPDF's built-in table finder."""

    @staticmethod
    def _to_markdown(table_data: list[list[str]]) -> str:
        """Convert a 2-D list of cell strings into a Markdown table."""
        if not table_data or not table_data[0]:
            return ""

        col_count = max(len(row) for row in table_data)
        # Normalise rows to same column count
        normalised = [row + [""] * (col_count - len(row)) for row in table_data]

        header = normalised[0]
        sep = ["---"] * col_count
        body = normalised[1:] if len(normalised) > 1 else []

        lines: list[str] = []
        lines.append("| " + " | ".join(c or "" for c in header) + " |")
        lines.append("| " + " | ".join(sep) + " |")
        for row in body:
            lines.append("| " + " | ".join(c or "" for c in row) + " |")
        return "\n".join(lines)

    @staticmethod
    def extract_all(page: fitz.Page) -> list[tuple[str, float]]:
        """Return ``(markdown_table, y_position)`` for every table on the page."""
        results: list[tuple[str, float]] = []
        try:
            tabs = page.find_tables()
            for tab in tabs:
                table_data = tab.extract()
                md = TableExtractor._to_markdown(table_data)
                if md:
                    y_pos = tab.bbox[1] if hasattr(tab, "bbox") else 0
                    results.append((md, y_pos))
        except Exception:
            pass  # table detection is best-effort
        return results
