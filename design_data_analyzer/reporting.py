"""Rendering utilities for design data outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def render_markdown(aggregated: Dict[str, Any]) -> str:
    """Generate a polished Markdown report from aggregated guideline data."""

    compiled = aggregated.get("compiled", {})
    lines: List[str] = ["# Design Data Specification", ""]
    lines.append(f"- Images analyzed: {aggregated.get('images_analyzed', 0)}")
    lines.append("")

    brand = compiled.get("brand_identity", {})
    if any(brand.values()):
        lines.append("## Brand Identity")
        if brand.get("brand_names"):
            lines.append(f"- **Brand references:** {', '.join(brand['brand_names'])}")
        if brand.get("design_context"):
            lines.append("- **Design context cues:**")
            for item in brand["design_context"]:
                lines.append(f"  - {item}")
        if brand.get("core_attributes"):
            lines.append("- **Core attributes:** " + ", ".join(brand["core_attributes"]))
        if brand.get("taglines"):
            lines.append(f"- **Taglines / slogans:** {', '.join(brand['taglines'])}")
        lines.append("")

    visual = compiled.get("visual_identity", {})
    if visual:
        lines.append("## Visual Identity")
        palette = visual.get("color_palette") or []
        if palette:
            lines.extend(
                [
                    "### Color Palette",
                    "| Hex | Names | Usage | Finishes | Source Images | Notes |",
                    "| --- | ----- | ----- | -------- | ------------- | ----- |",
                ]
            )
            for color in palette:
                lines.append(
                    "| {hex} | {names} | {usage} | {finishes} | {sources} | {notes} |".format(
                        hex=color["hex"],
                        names=", ".join(color["names"]) or "—",
                        usage=", ".join(color["usage_notes"]) or "—",
                        finishes=", ".join(color["finishes"]) or "—",
                        sources=", ".join(Path(src).name for src in color["source_images"]) or "—",
                        notes=", ".join(color["additional_notes"]) or "—",
                    )
                )
            lines.append("")

        typography = visual.get("typography") or []
        if typography:
            lines.extend(
                [
                    "### Typography",
                    "| Family | Styles | Usage | Sizes | Tracking | Source Images | Notes |",
                    "| ------ | ------ | ----- | ----- | -------- | ------------- | ----- |",
                ]
            )
            for typo in typography:
                lines.append(
                    "| {family} | {styles} | {usage} | {sizes} | {tracking} | {sources} | {notes} |".format(
                        family=typo["family"],
                        styles=", ".join(typo["styles"]) or "—",
                        usage=", ".join(typo["usage"]) or "—",
                        sizes=", ".join(typo["size_ranges"]) or "—",
                        tracking=", ".join(typo["tracking"]) or "—",
                        sources=", ".join(Path(src).name for src in typo["source_images"]) or "—",
                        notes=", ".join(typo["notes"]) or "—",
                    )
                )
            lines.append("")

        if visual.get("logo_usage"):
            lines.append("### Logo Usage")
            for note in visual["logo_usage"]:
                lines.append(f"- {note}")
            lines.append("")

        imagery = visual.get("imagery_style") or {}
        if any(imagery.values()):
            lines.append("### Imagery Style")
            for section, items in imagery.items():
                if items:
                    title = section.replace("_", " ").title()
                    lines.append(f"- **{title}:** {', '.join(items)}")
            lines.append("")

    layout = compiled.get("layout_and_components", {})
    if any(layout.values()):
        lines.append("## Layout & Components")
        for field, label in (
            ("grid_and_spacing", "Grid & spacing"),
            ("key_components", "Key components"),
            ("call_to_action_treatment", "Call-to-action treatment"),
            ("interaction_notes", "Interaction notes"),
        ):
            if layout.get(field):
                lines.append(f"- **{label}:** {', '.join(layout[field])}")
        lines.append("")

    voice = compiled.get("voice_and_copy", {})
    if any(voice.values()):
        lines.append("## Voice & Copy")
        for field, label in (
            ("tone_descriptors", "Tone descriptors"),
            ("messaging_pillars", "Messaging pillars"),
            ("dos", "Do"),
            ("donts", "Don't"),
        ):
            if voice.get(field):
                lines.append(f"- **{label}:** {', '.join(voice[field])}")
        lines.append("")

    if compiled.get("production_notes"):
        lines.append("## Production Notes")
        for note in compiled["production_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    if compiled.get("confidence_notes"):
        lines.append("## Confidence & Follow-ups")
        for item in compiled["confidence_notes"]:
            image_name = Path(item["image"]).name
            lines.append(f"- **{image_name}:** {item['note']}")
        lines.append("")

    lines.append("## Per-Image Extracts")
    for record in aggregated.get("per_image", []):
        image_path = record.get("image", "unknown")
        guidelines = record.get("guidelines", {})
        lines.append(f"### {Path(image_path).name}")
        lines.append(f"- Source path: `{image_path}`")
        confidence = guidelines.get("confidence")
        if confidence:
            lines.append(f"- Model confidence note: {confidence}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(guidelines, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


__all__ = ["render_markdown"]
