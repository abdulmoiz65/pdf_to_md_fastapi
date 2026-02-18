"""Embedded / attached file extraction."""

from __future__ import annotations

import fitz


class EmbeddedFileExtractor:
    """List files embedded (attached) inside the PDF."""

    @staticmethod
    def extract(doc: fitz.Document) -> str:
        """Return a Markdown section listing embedded files, or empty string."""
        count = doc.embfile_count()
        if count == 0:
            return ""

        lines: list[str] = ["\n## 📎 Embedded Files\n"]
        for i in range(count):
            try:
                info = doc.embfile_info(i)
                name = info.get("name", f"file_{i}")
                size = info.get("size", 0)
                if size >= 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size >= 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                lines.append(f"- **{name}** ({size_str})")
            except Exception:
                continue
        lines.append("")
        return "\n".join(lines)
