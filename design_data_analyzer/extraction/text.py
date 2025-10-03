"""Text extraction and typography heuristics."""

from __future__ import annotations

from typing import List

from PIL import Image

try:  # pragma: no cover - optional dependency
    import pytesseract
except Exception:  # noqa: S110 - broad exception acceptable for optional feature
    pytesseract = None

from ..pipeline import TypographySample


def extract_text_lines(image: Image.Image, *, min_length: int = 3) -> List[str]:
    """Attempt to OCR text from the image, falling back to empty list."""

    if pytesseract is None:
        return []

    # pytesseract expects RGB images.
    rgb = image.convert("RGB")
    text = pytesseract.image_to_string(rgb)
    lines = [clean.strip() for clean in text.splitlines()]
    return [line for line in lines if len(line) >= min_length]


def build_typography_samples(lines: List[str]) -> List[TypographySample]:
    """Generate lightweight typography descriptors based on OCR output."""

    samples: List[TypographySample] = []
    seen: set[str] = set()
    for line in lines:
        normalized = " ".join(line.split())
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        samples.append(
            TypographySample(
                text=normalized,
                casing=_infer_casing(normalized),
                weight=_infer_weight(normalized),
                classification=_infer_classification(normalized),
            )
        )
    return samples


def _infer_casing(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "mixed"
    if all(c.isupper() for c in letters):
        return "uppercase"
    if all(c.islower() for c in letters):
        return "lowercase"
    if letters[0].isupper():
        return "title"
    return "mixed"


def _infer_weight(text: str) -> str:
    if len(text) <= 12 and text.isupper():
        return "bold"
    if len(text.split()) >= 8:
        return "regular"
    return "medium"


def _infer_classification(text: str) -> str:
    words = text.split()
    if len(words) <= 4 and text.isupper():
        return "display"
    if len(words) <= 8:
        return "headline"
    return "body"


__all__ = ["extract_text_lines", "build_typography_samples"]
