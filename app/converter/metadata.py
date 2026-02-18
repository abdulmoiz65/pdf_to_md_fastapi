"""PDF metadata extraction and YAML frontmatter generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

import fitz  # PyMuPDF


class PDFMetadataExtractor:
    """Extract document-level metadata from a PDF."""

    @staticmethod
    def extract(doc: fitz.Document) -> dict[str, Any]:
        """Return a dict with title, author, subject, creator, dates, pages, encrypted."""
        meta = doc.metadata or {}

        def _parse_date(raw: str | None) -> str | None:
            if not raw:
                return None
            # PDF dates look like "D:20240115103000+00'00'"
            raw = raw.replace("D:", "").replace("'", "")
            for fmt in ("%Y%m%d%H%M%S%z", "%Y%m%d%H%M%S", "%Y%m%d"):
                try:
                    return datetime.strptime(raw[:len(fmt.replace("%", ""))], fmt).replace(
                        tzinfo=timezone.utc
                    ).isoformat()
                except (ValueError, IndexError):
                    continue
            return raw  # return as-is if unparseable

        return {
            "title": meta.get("title", "") or "Untitled",
            "author": meta.get("author", "") or "Unknown",
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "creation_date": _parse_date(meta.get("creationDate")),
            "modified_date": _parse_date(meta.get("modDate")),
            "pages": doc.page_count,
            "encrypted": doc.is_encrypted,
        }

    @staticmethod
    def create_frontmatter(meta: dict[str, Any]) -> str:
        """Return a YAML frontmatter block."""
        # Build a clean dict (drop empty values)
        clean: dict[str, Any] = {}
        for key in ("title", "author", "subject", "creator", "creation_date", "modified_date", "pages", "encrypted"):
            val = meta.get(key)
            if val not in (None, ""):
                clean[key] = val

        if HAS_YAML:
            body = yaml.dump(clean, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
        else:
            lines = []
            for k, v in clean.items():
                if isinstance(v, bool):
                    lines.append(f"{k}: {'true' if v else 'false'}")
                elif isinstance(v, int):
                    lines.append(f"{k}: {v}")
                else:
                    lines.append(f"{k}: \"{v}\"")
            body = "\n".join(lines)

        return f"---\n{body}\n---\n\n"
