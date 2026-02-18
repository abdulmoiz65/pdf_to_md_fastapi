"""FastAPI application — routes, templates, static files."""

from __future__ import annotations

import os
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
    """Upload a PDF, convert it to Markdown, and return the result as JSON."""
    # ── Validate ──────────────────────────────────────────────────────
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return ConversionResponse(success=False, error=f"Only PDF files are accepted, got '{ext}'.")

    # ── Save uploaded file ────────────────────────────────────────────
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{unique_id}_{file.filename}"
    pdf_path = config.UPLOAD_DIR / safe_name
    images_dir = config.UPLOAD_DIR / f"{unique_id}_images"

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ── Convert ──────────────────────────────────────────────────
        markdown, meta = pdf_to_markdown(
            str(pdf_path),
            password=password or None,
            extract_images_dir=str(images_dir),
        )

        md_filename = Path(file.filename or "output").stem + ".md"
        return ConversionResponse(
            success=True,
            markdown=markdown,
            filename=md_filename,
            metadata=meta,
        )
    except PermissionError as exc:
        return ConversionResponse(success=False, error=str(exc))
    except Exception as exc:
        return ConversionResponse(success=False, error=f"Conversion failed: {exc}")
    finally:
        # Cleanup temp files
        if pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
        if images_dir.exists():
            shutil.rmtree(images_dir, ignore_errors=True)


@app.post("/api/download")
async def download(
    file: UploadFile = File(...),
    password: str = Form(""),
):
    """Upload a PDF and get back a downloadable .md file."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return JSONResponse({"error": f"Only PDF files are accepted, got '{ext}'."}, status_code=400)

    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{unique_id}_{file.filename}"
    pdf_path = config.UPLOAD_DIR / safe_name
    images_dir = config.UPLOAD_DIR / f"{unique_id}_images"
    md_path = config.UPLOAD_DIR / (Path(file.filename or "output").stem + ".md")

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        markdown, _ = pdf_to_markdown(
            str(pdf_path),
            password=password or None,
            extract_images_dir=str(images_dir),
        )

        md_path.write_text(markdown, encoding="utf-8")
        return FileResponse(
            path=str(md_path),
            filename=Path(file.filename or "output").stem + ".md",
            media_type="text/markdown",
        )
    except PermissionError as exc:
        return JSONResponse({"error": str(exc)}, status_code=403)
    except Exception as exc:
        return JSONResponse({"error": f"Conversion failed: {exc}"}, status_code=500)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
