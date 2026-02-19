"""Image extraction from PDF pages — saves images as files with relative-path references."""

from __future__ import annotations

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
    """Extract embedded images from a PDF page and save as individual files."""

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
        images_dir: str,
    ) -> list[tuple[str, float]]:
        """Extract every image on *page* and save to *images_dir*.

        Returns a list of ``(markdown_reference, y_position)`` tuples.
        Images are saved as individual files and referenced via relative paths.
        """
        results: list[tuple[str, float]] = []

        os.makedirs(images_dir, exist_ok=True)

        for img_index, img_info in enumerate(page.get_images(full=True)):
            xref = img_info[0]
            try:
                base_image = fitz.Pixmap(page.parent, xref)

                # Convert CMYK / other colour spaces to RGB
                if base_image.n - base_image.alpha > 3:
                    base_image = fitz.Pixmap(fitz.csRGB, base_image)

                ext = "png" if base_image.alpha else "jpg"

                # Get raw image bytes
                if ext == "png":
                    img_bytes = base_image.tobytes("png")
                else:
                    img_bytes = base_image.tobytes("jpeg")

                # Resize in memory
                img_bytes = ImageExtractor._resize_bytes(img_bytes, ext)

                # Save image to disk
                fname = f"page_{page_num + 1}_img_{img_index + 1}.{ext}"
                img_path = os.path.join(images_dir, fname)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                # Determine vertical position
                try:
                    img_rects = page.get_image_rects(xref)
                    y_pos = img_rects[0].y0 if img_rects else 0
                except Exception:
                    y_pos = 0

                # Use relative path for Markdown reference
                md_ref = f"![Image page {page_num + 1}](images/{fname})"
                results.append((md_ref, y_pos))
            except Exception:
                continue

        return results
