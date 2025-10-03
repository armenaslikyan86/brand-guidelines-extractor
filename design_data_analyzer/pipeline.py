"""Core pipeline types and orchestration helpers for local brand guideline extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class ColorSwatch:
    """Represents a single detected color and its contextual metadata."""

    hex: str
    name: str
    prominence: float
    usage_hint: str = ""


@dataclass
class TypographySample:
    """Lightweight description of detected typographic usage."""

    text: str
    casing: str
    weight: str
    classification: str


@dataclass
class LayoutSummary:
    """Encapsulates coarse layout cues used to infer guideline recommendations."""

    aspect_ratio: float
    dominant_orientation: str
    whitespace_ratio: float
    focal_regions: List[str] = field(default_factory=list)


@dataclass
class ImageExtraction:
    """All signals collected from a single asset."""

    source: Path
    colors: List[ColorSwatch] = field(default_factory=list)
    typography: List[TypographySample] = field(default_factory=list)
    layout: Optional[LayoutSummary] = None
    detected_copy: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class AggregatedEvidence:
    """Merged signals across the full asset set."""

    images: List[ImageExtraction]
    palette: List[ColorSwatch] = field(default_factory=list)
    typography: List[TypographySample] = field(default_factory=list)
    layout_patterns: List[str] = field(default_factory=list)
    tone_descriptors: List[str] = field(default_factory=list)
    copy_observations: List[str] = field(default_factory=list)
    production_notes: List[str] = field(default_factory=list)


def consolidate(extractions: Iterable[ImageExtraction]) -> AggregatedEvidence:
    """Merge per-image extractions into a single evidence bundle."""

    images: List[ImageExtraction] = list(extractions)
    by_hex: Dict[str, ColorSwatch] = {}
    typography_samples: Dict[str, TypographySample] = {}
    layout_patterns: List[str] = []
    tones: List[str] = []
    copy_lines: List[str] = []
    production: List[str] = []

    for extraction in images:
        for color in extraction.colors:
            key = color.hex.upper()
            existing = by_hex.get(key)
            if existing and existing.prominence >= color.prominence:
                continue
            by_hex[key] = color
        for typo in extraction.typography:
            key = f"{typo.classification}:{typo.weight}:{typo.casing}"
            if key not in typography_samples:
                typography_samples[key] = typo
        if extraction.layout:
            layout_patterns.append(extraction.layout.dominant_orientation)
            whitespace = extraction.layout.whitespace_ratio
            if whitespace < 0.25:
                production.append(
                    f"Consider reviewing dense composition in {extraction.source.name}; whitespace under 25%."
                )
        copy_lines.extend(extraction.detected_copy)
        production.extend(extraction.notes)

    palette = sorted(by_hex.values(), key=lambda item: item.prominence, reverse=True)
    return AggregatedEvidence(
        images=images,
        palette=palette,
        typography=list(typography_samples.values()),
        layout_patterns=layout_patterns,
        tone_descriptors=tones,
        copy_observations=copy_lines,
        production_notes=production,
    )




def color_to_dict(color: ColorSwatch) -> dict:
    return {
        "hex": color.hex,
        "name": color.name,
        "prominence": color.prominence,
        "usage_hint": color.usage_hint,
    }


def typography_to_dict(sample: TypographySample) -> dict:
    return {
        "text": sample.text,
        "casing": sample.casing,
        "weight": sample.weight,
        "classification": sample.classification,
    }


def layout_to_dict(summary: LayoutSummary | None) -> dict | None:
    if summary is None:
        return None
    return {
        "aspect_ratio": summary.aspect_ratio,
        "dominant_orientation": summary.dominant_orientation,
        "whitespace_ratio": summary.whitespace_ratio,
        "focal_regions": list(summary.focal_regions),
    }


def image_to_dict(extraction: ImageExtraction) -> dict:
    return {
        "source": str(extraction.source),
        "colors": [color_to_dict(color) for color in extraction.colors],
        "typography": [typography_to_dict(sample) for sample in extraction.typography],
        "layout": layout_to_dict(extraction.layout),
        "detected_copy": list(extraction.detected_copy),
        "notes": list(extraction.notes),
    }


def aggregated_to_dict(evidence: AggregatedEvidence) -> dict:
    return {
        "images": [image_to_dict(extraction) for extraction in evidence.images],
        "palette": [color_to_dict(color) for color in evidence.palette],
        "typography": [typography_to_dict(sample) for sample in evidence.typography],
        "layout_patterns": list(evidence.layout_patterns),
        "tone_descriptors": list(evidence.tone_descriptors),
        "copy_observations": list(evidence.copy_observations),
        "production_notes": list(evidence.production_notes),
    }

__all__ = [
    "ColorSwatch",
    "TypographySample",
    "LayoutSummary",
    "ImageExtraction",
    "AggregatedEvidence",
    "consolidate",
    "color_to_dict",
    "typography_to_dict",
    "layout_to_dict",
    "image_to_dict",
    "aggregated_to_dict",
]
