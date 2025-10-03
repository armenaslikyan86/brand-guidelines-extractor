d"""Layout analytics for identifying composition patterns."""

from __future__ import annotations

from typing import List

import numpy as np
from PIL import Image, ImageFilter

from ..pipeline import LayoutSummary

GRID_REGIONS = [
    "top-left",
    "top-center",
    "top-right",
    "middle-left",
    "center",
    "middle-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
]


def summarize_layout(image: Image.Image) -> LayoutSummary:
    """Produce coarse layout descriptors based on pixel density."""

    grayscale = image.convert("L")
    grayscale = grayscale.filter(ImageFilter.GaussianBlur(radius=1.5))

    arr = np.asarray(grayscale, dtype=np.float32) / 255.0
    height, width = arr.shape
    aspect_ratio = width / height if height else 1.0
    orientation = _orientation_from_ratio(aspect_ratio)

    whitespace_ratio = float(np.mean(arr >= 0.9))

    focal_regions = _resolve_focal_regions(arr)

    return LayoutSummary(
        aspect_ratio=aspect_ratio,
        dominant_orientation=orientation,
        whitespace_ratio=whitespace_ratio,
        focal_regions=focal_regions,
    )


def _orientation_from_ratio(ratio: float) -> str:
    if ratio > 1.15:
        return "landscape"
    if ratio < 0.85:
        return "portrait"
    return "square"


def _resolve_focal_regions(arr: np.ndarray) -> List[str]:
    height, width = arr.shape
    third_h, third_w = height // 3, width // 3
    regions: List[str] = []

    for idx, label in enumerate(GRID_REGIONS):
        row = idx // 3
        col = idx % 3
        y0 = row * third_h
        y1 = (row + 1) * third_h if row < 2 else height
        x0 = col * third_w
        x1 = (col + 1) * third_w if col < 2 else width
        cell = arr[y0:y1, x0:x1]
        if cell.size == 0:
            continue
        darkness = 1.0 - float(np.mean(cell))
        if darkness > 0.35:
            regions.append(label)
    return regions


__all__ = ["summarize_layout"]
