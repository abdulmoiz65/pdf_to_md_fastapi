"""Image extraction from PDF pages — returns base64 data URIs."""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path

import fitz

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class ImageExtractor:
    """Extract embedded images from a PDF page and return as base64 data URIs."""

    MAX_DIMS = (800, 1000)

    @staticmethod
    def _resize_bytes(img_bytes: bytes, ext: str, max_dims: tuple[int, int] = (800, 1000)) -> bytes:
        """Resize image bytes in memory. Returns resized bytes."""
        if not HAS_PILLOW:
            return img_bytes
        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                img.thumbnail(max_dims, Image.LANCZOS)
                buf = io.BytesIO()
                fmt = "PNG" if ext == "png" else "JPEG"
                img.save(buf, format=fmt)
                return buf.getvalue()
        except Exception:
            return img_bytes

    @staticmethod
    def extract_all(
        page: fitz.Page,
        page_num: int,
        output_dir: str | None = None,
    ) -> list[tuple[str, float]]:
        """Extract every image on *page*.

        Returns a list of ``(markdown_reference, y_position)`` tuples.
        Images are embedded as base64 data URIs so no filesystem writes are needed.
        If *output_dir* is provided, images are also saved to disk.
        """
        results: list[tuple[str, float]] = []

        for img_index, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                base_image = fitz.Pixmap(page.parent, xref)

                # Convert CMYK / other colour spaces to RGB
                if base_image.n - base_image.alpha > 3:
                    base_image = fitz.Pixmap(fitz.csRGB, base_image)

                ext = "png" if base_image.alpha else "jpg"
                mime = "image/png" if ext == "png" else "image/jpeg"

                # Get raw image bytes
                if ext == "png":
                    img_bytes = base_image.tobytes("png")
                else:
                    img_bytes = base_image.tobytes("jpeg")

                # Resize in memory
                img_bytes = ImageExtractor._resize_bytes(img_bytes, ext)

                # Encode as base64 data URI
                b64 = base64.b64encode(img_bytes).decode("ascii")
                data_uri = f"data:{mime};base64,{b64}"

                # Optionally save to disk too
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    fname = f"page{page_num + 1}_img{img_index}.{ext}"
                    img_path = os.path.join(output_dir, fname)
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)

                # Determine vertical position
                try:
                    img_rects = page.get_image_rects(xref)
                    y_pos = img_rects[0].y0 if img_rects else 0
                except Exception:
                    y_pos = 0

                md_ref = f"![Image page {page_num + 1}]({data_uri})"
                results.append((md_ref, y_pos))
            except Exception:
                continue

        return results
