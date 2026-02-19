"""Main PDF-to-Markdown orchestrator.

Combines all extraction modules into a single ``pdf_to_markdown()`` function.
"""

from __future__ import annotations

import os
from pathlib import Path

import fitz

from .metadata import PDFMetadataExtractor
from .text import TextFormatter
from .headings import HeadingDetector
from .lists import ListDetector
from .urls import URLExtractor
from .images import ImageExtractor
from .tables import TableExtractor
from .annotations import AnnotationExtractor
from .bookmarks import BookmarkExtractor
from .embedded import EmbeddedFileExtractor
from .security import SecurityHandler


def _compute_avg_font_size(page: fitz.Page) -> float:
    """Return the average font size across all spans on *page*."""
    sizes: list[float] = []
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sizes.append(span.get("size", 0))
    return sum(sizes) / len(sizes) if sizes else 12.0


def _process_page(
    page: fitz.Page,
    page_num: int,
    images_dir: str | None,
) -> str:
    """Process a single page and return its Markdown content."""
    avg_font_size = _compute_avg_font_size(page)

    # ------------------------------------------------------------------
    # 1. Collect all elements with their Y positions
    # ------------------------------------------------------------------
    elements: list[tuple[float, str, str]] = []

    # --- Tables (extracted first so we know which regions to skip) ------
    table_rects: list[fitz.Rect] = []
    for md_table, y_pos, bbox in TableExtractor.extract_all(page):
        elements.append((y_pos, "table", md_table))
        if bbox:
            table_rects.append(bbox)

    # --- Text blocks (skip text that falls inside a table region) ------
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        block_bbox = block.get("bbox", [0, 0, 0, 0])
        block_rect = fitz.Rect(block_bbox)

        # If this text block overlaps any detected table, skip it entirely
        if any(block_rect.intersects(tr) for tr in table_rects):
            continue

        block_y = block_bbox[1]
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            line_text, max_font_size, is_line_bold = TextFormatter.format_line(spans)
            if not line_text.strip():
                continue

            # Heading detection
            heading_prefix = HeadingDetector.detect_heading(max_font_size, avg_font_size, is_line_bold)

            # List detection
            if not heading_prefix:
                line_text = ListDetector.process_line(line_text)

            # URL conversion
            line_text = URLExtractor.replace_urls_in_text(line_text)

            final = f"{heading_prefix}{line_text}"
            elements.append((block_y, "text", final))

    # --- Images --------------------------------------------------------
    for md_ref, y_pos in ImageExtractor.extract_all(page, page_num, images_dir):
        elements.append((y_pos, "image", md_ref))

    # --- Annotations ---------------------------------------------------
    for md_annot, y_pos in AnnotationExtractor.extract_all(page):
        elements.append((y_pos, "annotation", md_annot))

    # --- Hyperlinks (deduplicate with text) ----------------------------
    # We already converted bare URLs; hyperlinks add link annotations
    # that may not appear as bare text.
    seen_urls: set[str] = set()
    for display, url, y_pos in URLExtractor.extract_hyperlinks(page):
        if url not in seen_urls:
            seen_urls.add(url)
            # Only add if URL wasn't already in a text element
            md_link = URLExtractor.markdown_url(display, url)
            elements.append((y_pos, "link", md_link))

    # --- Drawings / horizontal rules -----------------------------------
    try:
        drawings = page.get_drawings()
        for d in drawings:
            # Detect horizontal lines spanning > 60 % of page width
            rect = d.get("rect")
            if rect and (rect.width / page.rect.width > 0.6) and rect.height < 5:
                elements.append((rect.y0, "rule", "---"))
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 2. Sort by Y position and render
    # ------------------------------------------------------------------
    elements.sort(key=lambda e: e[0])

    lines: list[str] = []
    for _, elem_type, content in elements:
        if elem_type == "rule":
            lines.append("\n---\n")
        elif elem_type in ("table", "image", "annotation", "link"):
            lines.append(f"\n{content}\n")
        else:
            lines.append(content)

    return "\n".join(lines)


# ======================================================================
# Public API
# ======================================================================

def pdf_to_markdown(
    pdf_path: str,
    password: str | None = None,
    extract_images_dir: str | None = None,
) -> tuple[str, dict]:
    """Convert a PDF file to Markdown.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file.
    password : str | None
        Optional password for encrypted PDFs.
    extract_images_dir : str | None
        Directory to save extracted images.  ``None`` skips image extraction.

    Returns
    -------
    tuple[str, dict]
        ``(markdown_text, metadata_dict)``

    Raises
    ------
    FileNotFoundError
        If *pdf_path* does not exist.
    PermissionError
        If the PDF is encrypted and the password is wrong / missing.
    """
    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    doc = fitz.open(pdf_path)

    # --- Security / password ------------------------------------------
    if doc.is_encrypted:
        if password:
            if not SecurityHandler.authenticate(doc, password):
                doc.close()
                raise PermissionError("Invalid password!")
        elif doc.needs_pass:
            doc.close()
            raise PermissionError("PDF is password-protected. Please provide a password.")

    # --- Metadata & frontmatter ---------------------------------------
    meta = PDFMetadataExtractor.extract(doc)
    result_parts: list[str] = [PDFMetadataExtractor.create_frontmatter(meta)]

    # --- Bookmarks (stored in metadata only, not in Markdown body) ------
    toc = BookmarkExtractor.extract_raw(doc)
    if toc:
        meta["bookmarks"] = toc

    # --- Pages --------------------------------------------------------
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        result_parts.append(f"\n## 📄 Page {page_num + 1}\n")
        result_parts.append(_process_page(page, page_num, extract_images_dir))

    # --- Embedded files -----------------------------------------------
    embedded = EmbeddedFileExtractor.extract(doc)
    if embedded:
        result_parts.append(embedded)

    # --- Security info ------------------------------------------------
    security = SecurityHandler.get_permissions_info(doc)
    if security:
        result_parts.append(security)

    doc.close()
    return "\n".join(result_parts), meta
