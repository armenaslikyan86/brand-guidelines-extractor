"""Local analysis orchestration for design guideline extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .extraction import extract_from_path
from .pipeline import AggregatedEvidence, ImageExtraction, consolidate


def analyze_paths(paths: Iterable[Path]) -> List[ImageExtraction]:
    """Run extraction across multiple image paths."""

    extractions: List[ImageExtraction] = []
    for path in paths:
        extraction = extract_from_path(path)
        extractions.append(extraction)
    return extractions


def aggregate(extractions: Iterable[ImageExtraction]) -> AggregatedEvidence:
    """Aggregate per-image extractions into evidence pool."""

    return consolidate(extractions)


__all__ = ["analyze_paths", "aggregate"]
