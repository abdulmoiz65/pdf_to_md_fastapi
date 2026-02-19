"""Pydantic response models."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ConversionResponse(BaseModel):
    success: bool
    markdown: str = ""
    filename: str = ""
    metadata: dict[str, Any] = {}
    error: str = ""
    image_base_url: str = ""
