"""Color extraction utilities for design assets."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Iterable, List, Tuple

from PIL import Image

from ..pipeline import ColorSwatch

# Simple named color anchors for labelling without extra dependencies.
NAMED_COLORS: List[Tuple[str, Tuple[int, int, int]]] = [
    ("Bynder Blue", (0, 161, 222)),
    ("Deep Blue", (0, 102, 204)),
    ("Navy", (17, 34, 68)),
    ("Sky", (102, 204, 255)),
    ("Midnight", (2, 20, 43)),
    ("Sunrise Orange", (255, 149, 0)),
    ("Vivid Red", (220, 20, 60)),
    ("Warm Red", (200, 48, 48)),
    ("Slate", (112, 128, 144)),
    ("Charcoal", (54, 69, 79)),
    ("Stone", (189, 195, 199)),
    ("Cloud", (236, 240, 241)),
    ("Emerald", (46, 204, 113)),
    ("Mint", (171, 235, 198)),
    ("Lavender", (187, 143, 206)),
    ("Magenta", (214, 41, 118)),
    ("Gold", (255, 195, 0)),
]


def extract_colors(image: Image.Image, max_colors: int = 5) -> List[ColorSwatch]:
    """Return the most prominent colors in the image."""

    working = image.convert("RGBA")
    # Resize to limit the number of pixels processed.
    working.thumbnail((600, 600))
    # Flatten alpha by compositing over white to avoid transparent noise.
    background = Image.new("RGBA", working.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(background, working)
    rgb_image = flattened.convert("RGB")

    palette = rgb_image.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
    palette_colors = palette.getpalette()[: max_colors * 3]
    counts = Counter(palette.getdata())

    swatches: List[ColorSwatch] = []
    total_pixels = sum(counts.values()) or 1

    for index, count in counts.most_common(max_colors):
        base_index = index * 3
        if base_index + 2 >= len(palette_colors):
            continue
        r, g, b = palette_colors[base_index : base_index + 3]
        prominence = count / total_pixels
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        swatches.append(
            ColorSwatch(
                hex=hex_code,
                name=_closest_named_color((r, g, b)),
                prominence=prominence,
                usage_hint=_usage_hint(prominence),
            )
        )

    return swatches


def _closest_named_color(rgb: Tuple[int, int, int]) -> str:
    """Pick the nearest predefined color name for labelling."""

    def distance(candidate: Tuple[int, int, int]) -> float:
        return sqrt(sum((component - ref) ** 2 for component, ref in zip(candidate, rgb)))

    name, _ = min(NAMED_COLORS, key=lambda item: distance(item[1]))
    return name


def _usage_hint(prominence: float) -> str:
    if prominence >= 0.45:
        return "Dominant background or hero coverage"
    if prominence >= 0.25:
        return "Primary supporting block"
    if prominence >= 0.10:
        return "Accent or typography highlight"
    return "Detail accent"


__all__ = ["extract_colors"]
