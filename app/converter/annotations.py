"""Annotation extraction — comments, highlights, sticky notes."""

from __future__ import annotations

import fitz


class AnnotationExtractor:
    """Extract annotations from a PDF page and format as Markdown blockquotes."""

    # Annotation sub-types we care about
    _TYPE_LABELS = {
        fitz.PDF_ANNOT_TEXT: "📝 Note",
        fitz.PDF_ANNOT_FREE_TEXT: "📝 Note",
        fitz.PDF_ANNOT_HIGHLIGHT: "🔆 Highlight",
        fitz.PDF_ANNOT_UNDERLINE: "📎 Underline",
        fitz.PDF_ANNOT_STRIKE_OUT: "✂️ Strikeout",
        fitz.PDF_ANNOT_STAMP: "🔖 Stamp",
    }

    @staticmethod
    def extract_all(page: fitz.Page) -> list[tuple[str, float]]:
        """Return ``(blockquote_md, y_position)`` for every relevant annotation."""
        results: list[tuple[str, float]] = []
        for annot in page.annots():
            try:
                subtype = annot.type[0]
                label = AnnotationExtractor._TYPE_LABELS.get(subtype)
                if label is None:
                    continue

                content = (annot.info.get("content", "") or "").strip()
                if not content:
                    # For highlights, try to get the underlying text
                    if subtype == fitz.PDF_ANNOT_HIGHLIGHT:
                        try:
                            content = page.get_textbox(annot.rect).strip()
                        except Exception:
                            pass
                if not content:
                    continue

                md = f"> {label}: {content}"
                y_pos = annot.rect.y0
                results.append((md, y_pos))
            except Exception:
                continue
        return results
