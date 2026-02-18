"""Application-wide configuration."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
UPLOAD_DIR = BASE_DIR / "uploads"
IMAGES_DIR = UPLOAD_DIR / "images"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Constraints
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".pdf"}

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
