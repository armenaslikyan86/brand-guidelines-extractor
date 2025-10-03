"""Image extraction orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image

from ..pipeline import ImageExtraction
from .colors import extract_colors
from .layout import summarize_layout
from .text import build_typography_samples, extract_text_lines


def extract_from_path(path: Path) -> ImageExtraction:
    """Collect structured signals from a single image asset."""

    with Image.open(path) as img:
        img.load()
        colors = extract_colors(img)
        layout = summarize_layout(img)
        text_lines = extract_text_lines(img)
        typography = build_typography_samples(text_lines)

    notes: List[str] = []
    if not colors:
        notes.append("No dominant colors detected; image may be transparent or monochrome.")
    if not typography and text_lines:
        notes.append("OCR text present but typography heuristics produced no samples.")
    if not text_lines:
        notes.append("No copy detected automatically; review manually for critical messaging.")

    return ImageExtraction(
        source=path,
        colors=colors,
        typography=typography,
        layout=layout,
        detected_copy=text_lines,
        notes=notes,
    )


__all__ = ["extract_from_path"]
