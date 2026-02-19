"""Table detection and extraction to Markdown format."""

from __future__ import annotations

import fitz


class TableExtractor:
    """Detect and extract tables from a PDF page using PyMuPDF's built-in table finder."""

    @staticmethod
    def _clean_cell(cell: str | None) -> str:
        """Flatten multiline cell content to a single line for valid Markdown."""
        if not cell:
            return ""
        # Replace newlines / carriage returns with a space, collapse whitespace
        return " ".join(cell.split())

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

        clean = TableExtractor._clean_cell
        lines: list[str] = []
        lines.append("| " + " | ".join(clean(c) for c in header) + " |")
        lines.append("| " + " | ".join(sep) + " |")
        for row in body:
            lines.append("| " + " | ".join(clean(c) for c in row) + " |")
        return "\n".join(lines)

    @staticmethod
    def extract_all(page: fitz.Page) -> list[tuple[str, float, fitz.Rect | None]]:
        """Return ``(markdown_table, y_position, bbox)`` for every table on the page.

        The *bbox* is a ``fitz.Rect`` covering the table area so callers can
        suppress duplicate text blocks that fall within a table region.
        """
        results: list[tuple[str, float, fitz.Rect | None]] = []
        try:
            tabs = page.find_tables()
            for tab in tabs:
                table_data = tab.extract()
                md = TableExtractor._to_markdown(table_data)
                if md:
                    bbox = fitz.Rect(tab.bbox) if hasattr(tab, "bbox") else None
                    y_pos = bbox.y0 if bbox else 0
                    results.append((md, y_pos, bbox))
        except Exception:
            pass  # table detection is best-effort
        return results
