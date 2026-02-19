"""FastAPI application — routes, templates, static files."""

from __future__ import annotations

import os
import uuid
import shutil
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from . import config
from .models import ConversionResponse
from .converter.engine import pdf_to_markdown

# ── App setup ─────────────────────────────────────────────────────────
app = FastAPI(
    title="PDF → Markdown Converter",
    description="Convert any PDF to beautiful Markdown — extracts text, images, tables, metadata, and more.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# ── Routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the upload / conversion UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/convert", response_model=ConversionResponse)
async def convert(
    file: UploadFile = File(...),
    password: str = Form(""),
):
    """Upload a PDF, convert it to Markdown, and return the result as JSON.

    Images are extracted as separate files and served via /api/images/{session_id}/.
    """
    # ── Validate ──────────────────────────────────────────────────────
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return ConversionResponse(success=False, error=f"Only PDF files are accepted, got '{ext}'.")

    # ── Create processing directory ───────────────────────────────────
    session_id = uuid.uuid4().hex[:12]
    processing_dir = config.UPLOAD_DIR / session_id
    images_dir = processing_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = processing_dir / f"upload_{file.filename}"

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ── Convert ──────────────────────────────────────────────────
        markdown, meta = pdf_to_markdown(
            str(pdf_path),
            password=password or None,
            extract_images_dir=str(images_dir),
        )

        # Remove the uploaded PDF (no longer needed)
        pdf_path.unlink(missing_ok=True)

        md_filename = Path(file.filename or "output").stem + ".md"
        return ConversionResponse(
            success=True,
            markdown=markdown,
            filename=md_filename,
            metadata=meta,
            image_base_url=f"/api/images/{session_id}",
        )
    except PermissionError as exc:
        # Clean up on error
        if processing_dir.exists():
            shutil.rmtree(processing_dir, ignore_errors=True)
        return ConversionResponse(success=False, error=str(exc))
    except Exception as exc:
        if processing_dir.exists():
            shutil.rmtree(processing_dir, ignore_errors=True)
        return ConversionResponse(success=False, error=f"Conversion failed: {exc}")


@app.get("/api/images/{session_id}/{filename}")
async def serve_image(session_id: str, filename: str):
    """Serve an extracted image from a processing session."""
    img_path = config.UPLOAD_DIR / session_id / "images" / filename
    if not img_path.is_file():
        return JSONResponse({"error": "Image not found"}, status_code=404)

    # Determine media type
    ext = img_path.suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(path=str(img_path), media_type=media_type)


@app.post("/api/download")
async def download(
    file: UploadFile = File(...),
    password: str = Form(""),
):
    """Upload a PDF and get back a downloadable ZIP containing document.md + images/."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return JSONResponse({"error": f"Only PDF files are accepted, got '{ext}'."}, status_code=400)

    session_id = uuid.uuid4().hex[:12]
    processing_dir = config.UPLOAD_DIR / session_id
    images_dir = processing_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = processing_dir / f"upload_{file.filename}"

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        markdown, _ = pdf_to_markdown(
            str(pdf_path),
            password=password or None,
            extract_images_dir=str(images_dir),
        )

        # Write document.md
        md_path = processing_dir / "document.md"
        md_path.write_text(markdown, encoding="utf-8")

        # Remove the uploaded PDF
        pdf_path.unlink(missing_ok=True)

        # Build ZIP file
        stem = Path(file.filename or "output").stem
        zip_path = config.UPLOAD_DIR / f"{session_id}_{stem}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add document.md
            zf.write(md_path, "document.md")
            # Add all images
            for img_file in images_dir.iterdir():
                if img_file.is_file():
                    zf.write(img_file, f"images/{img_file.name}")

        # Background cleanup: delete the processing dir and ZIP after response
        def cleanup():
            shutil.rmtree(processing_dir, ignore_errors=True)
            zip_path.unlink(missing_ok=True)

        return FileResponse(
            path=str(zip_path),
            filename=f"{stem}.zip",
            media_type="application/zip",
            background=BackgroundTask(cleanup),
        )
    except PermissionError as exc:
        if processing_dir.exists():
            shutil.rmtree(processing_dir, ignore_errors=True)
        return JSONResponse({"error": str(exc)}, status_code=403)
    except Exception as exc:
        if processing_dir.exists():
            shutil.rmtree(processing_dir, ignore_errors=True)
        return JSONResponse({"error": f"Conversion failed: {exc}"}, status_code=500)


@app.delete("/api/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up a processing session's temporary files."""
    processing_dir = config.UPLOAD_DIR / session_id
    if processing_dir.exists():
        shutil.rmtree(processing_dir, ignore_errors=True)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
