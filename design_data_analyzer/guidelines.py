"""Guideline synthesis from aggregated evidence and OpenAI design specs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .pipeline import AggregatedEvidence, ColorSwatch, TypographySample


@dataclass
class Section:
    title: str
    body: List[str]


@dataclass
class GuidelineDocument:
    title: str
    sections: List[Section]


def build_document(evidence: AggregatedEvidence, *, brand_name: str = "Bynder") -> GuidelineDocument:
    """Create a guideline document using locally extracted evidence only."""

    palette = evidence.palette
    typography = evidence.typography
    layout_labels = evidence.layout_patterns
    copy_lines = evidence.copy_observations

    sections: List[Section] = []
    sections.append(
        _tone_of_voice_section(
            palette,
            typography,
            copy_lines,
        )
    )
    sections.append(
        _social_media_section(
            layout_labels,
        )
    )
    sections.append(
        _visual_system_section(
            palette,
            evidence,
        )
    )
    sections.append(_corner_radius_section(evidence))
    sections.append(_iconography_section(palette))
    sections.append(_logo_section(palette))
    sections.append(_color_section(palette))

    if evidence.production_notes:
        sections.append(_production_notes_section(evidence.production_notes, []))

    return GuidelineDocument(
        title=f"{brand_name} Brand Guidelines (Auto-generated)",
        sections=sections,
    )


def build_document_from_spec(
    design_spec: Dict[str, Any],
    *,
    brand_name: str = "Bynder",
    evidence: Optional[AggregatedEvidence] = None,
) -> GuidelineDocument:
    """Create a guideline document from OpenAI aggregated design data."""

    compiled = design_spec.get("compiled", {})
    brand_spec = compiled.get("brand_identity", {})
    voice_spec = compiled.get("voice_and_copy", {})
    visual_spec = compiled.get("visual_identity", {})
    layout_spec = compiled.get("layout_and_components", {})
    palette_spec = visual_spec.get("color_palette", []) or []
    imagery_spec = (visual_spec.get("imagery_style") or {}).get("iconography")
    logo_usage = visual_spec.get("logo_usage") or []
    production_notes = compiled.get("production_notes") or []
    confidence_notes = compiled.get("confidence_notes") or []

    palette_swatches = _swatches_from_palette_spec(palette_spec)
    typography: List[TypographySample] = []
    layout_labels = evidence.layout_patterns if evidence else []
    copy_lines = evidence.copy_observations if evidence else []

    sections: List[Section] = []
    sections.append(
        _tone_of_voice_section(
            palette_swatches,
            typography,
            copy_lines,
            voice_spec=voice_spec,
            brand_spec=brand_spec,
        )
    )
    sections.append(
        _social_media_section(
            layout_labels,
            design_context=brand_spec.get("design_context"),
            key_components=layout_spec.get("key_components"),
            callouts=layout_spec.get("call_to_action_treatment"),
        )
    )
    sections.append(
        _visual_system_section(
            palette_swatches,
            evidence,
            visual_spec=visual_spec,
            layout_spec=layout_spec,
        )
    )
    sections.append(_corner_radius_section(evidence, layout_spec=layout_spec))
    sections.append(_iconography_section(palette_swatches, imagery_spec=imagery_spec))
    sections.append(_logo_section(palette_swatches, logo_usage=logo_usage))
    sections.append(_color_section(palette_swatches, palette_spec=palette_spec))

    if production_notes or confidence_notes:
        sections.append(_production_notes_section(production_notes, confidence_notes))

    return GuidelineDocument(
        title=f"{brand_name} Brand Guidelines (Auto-generated)",
        sections=sections,
    )


def render_markdown(document: GuidelineDocument) -> str:
    """Render a guideline document to Markdown with a reference-style layout."""

    lines: List[str] = [f"# {document.title}"]
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    for section in document.sections:
        anchor = section.title.lower().replace(" ", "-")
        lines.append(f"- [{section.title}](#{anchor})")
    lines.append("")
    lines.append("***")
    lines.append("")

    for section in document.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.extend(section.body)
        if section.body and section.body[-1] != "":
            lines.append("")
        lines.append("***")
        lines.append("")

    lines.append("_Generated from current design asset gallery._")
    return "\n".join(lines)


def _tone_of_voice_section(
    palette: Sequence[ColorSwatch],
    typography: Iterable[TypographySample],
    copy_lines: Iterable[str],
    *,
    voice_spec: Optional[Dict[str, Any]] = None,
    brand_spec: Optional[Dict[str, Any]] = None,
) -> Section:
    dominant = palette[0] if palette else None
    uppercase_ratio = _uppercase_ratio(copy_lines)
    average_length = mean(len(line.split()) for line in copy_lines) if copy_lines else 0.0

    voice_lines: List[str] = []
    voice_lines.append("### What Defines the Voice")
    if dominant:
        brightness = _relative_brightness(dominant.hex)
        if brightness < 0.35:
            tone = "confident and premium"
        elif brightness < 0.6:
            tone = "assured and balanced"
        else:
            tone = "open and energizing"
        voice_lines.append(
            f"- Dominant palette leans {tone}; mirror this energy in written narratives."
        )
    else:
        voice_lines.append("- Palette analysis unavailable; retain neutral authoritative tone.")

    if brand_spec and brand_spec.get("core_attributes"):
        voice_lines.append(
            f"- Core attributes surfaced: {', '.join(brand_spec['core_attributes'])}."
        )

    if uppercase_ratio > 0.55:
        voice_lines.append("- High uppercase usage; maintain bold, declarative headlines.")
    elif uppercase_ratio < 0.25 and copy_lines:
        voice_lines.append("- Predominantly sentence case; emphasize conversational clarity.")
    else:
        voice_lines.append("- Mixed casing observed; adapt tone per channel while staying precise.")

    if voice_spec and voice_spec.get("tone_descriptors"):
        voice_lines.append(
            f"- Noted tone descriptors: {', '.join(voice_spec['tone_descriptors'])}."
        )

    voice_lines.append("")
    voice_lines.append("### Key Voice Principles")
    if voice_spec and voice_spec.get("messaging_pillars"):
        for idx, pillar in enumerate(voice_spec["messaging_pillars"], start=1):
            voice_lines.append(f"{idx}. **{pillar}**")
    else:
        if average_length <= 4:
            voice_lines.append("1. **Punchy Headlines** — Lead with sharp benefit statements.")
        else:
            voice_lines.append("1. **Clarity First** — Summaries should surface the outcome immediately.")
        voice_lines.append("2. **Evidence-backed Claims** — Support impact points with data where available.")
        voice_lines.append("3. **Partner Mindset** — Use second-person framing to reinforce collaboration.")

    if voice_spec and (voice_spec.get("dos") or voice_spec.get("donts")):
        voice_lines.append("")
        if voice_spec.get("dos"):
            voice_lines.append(f"- **Do:** {', '.join(voice_spec['dos'])}")
        if voice_spec.get("donts"):
            voice_lines.append(f"- **Don't:** {', '.join(voice_spec['donts'])}")

    return Section(title="Tone of Voice", body=voice_lines)


def _social_media_section(
    layout_labels: Iterable[str],
    *,
    design_context: Optional[Iterable[str]] = None,
    key_components: Optional[Iterable[str]] = None,
    callouts: Optional[Iterable[str]] = None,
) -> Section:
    counts = Counter(layout_labels)
    if counts:
        orientation, _ = counts.most_common(1)[0]
    else:
        orientation = "landscape"

    recommendations: List[str] = []
    recommendations.append("### Channel Focus")
    if orientation == "portrait":
        recommendations.append("- Prioritize Instagram Stories/Reels and mobile-first LinkedIn posts.")
        recommendations.append("- Repurpose vertical cuts for event live coverage on X.")
    elif orientation == "square":
        recommendations.append("- Square treatments adapt well to Instagram feed and LinkedIn carousels.")
        recommendations.append("- Ensure captions highlight value quickly for mobile consumption.")
    else:
        recommendations.append("- Landscape layouts suit webinars, YouTube explainers, and LinkedIn banners.")
        recommendations.append("- Maintain responsive crops for Instagram and short-form platforms.")

    if design_context:
        context_label = ", ".join(design_context)
        recommendations.append(f"- Observed design contexts: {context_label}; tailor copy for these audiences.")

    recommendations.append("")
    recommendations.append("### Publishing Checklist")
    recommendations.append("- Tag Bynder master accounts to amplify reach.")
    recommendations.append("- Validate stats and claims before post scheduling.")
    recommendations.append("- Secure approvals for any customer visuals or quotes.")
    if key_components:
        recommendations.append(f"- Spotlight key modules: {', '.join(key_components)}.")
    if callouts:
        recommendations.append(f"- Reinforce CTAs using: {', '.join(callouts)}.")

    return Section(title="Social Media", body=recommendations)


def _visual_system_section(
    palette: Sequence[ColorSwatch],
    evidence: Optional[AggregatedEvidence],
    *,
    visual_spec: Optional[Dict[str, Any]] = None,
    layout_spec: Optional[Dict[str, Any]] = None,
) -> Section:
    colors = list(palette)
    layout_regions: Counter[str] = Counter()
    if evidence:
        for image in evidence.images:
            if image.layout:
                layout_regions.update(image.layout.focal_regions)

    lines: List[str] = []
    lines.append("### Datastream Principles")
    if layout_regions:
        hotspots = ", ".join(region for region, _ in layout_regions.most_common(3))
        lines.append(f"- Visual weight concentrates around {hotspots}; maintain consistent rhythm across assets.")
    else:
        lines.append("- Layout scans evenly; introduce focal anchors aligned to brand icon nodes.")

    if colors:
        dominant = colors[0]
        lines.append(
            f"- Anchor hero compositions with {dominant.name} ({dominant.hex}); deploy secondary hues for supporting datablocks."
        )
    if len(colors) >= 3:
        accent = colors[2]
        lines.append(
            f"- Use {accent.name.lower()} as a thrive accent within charts, chips, or callouts."
        )

    if layout_spec and layout_spec.get("grid_and_spacing"):
        lines.append(
            f"- Grid cues detected: {', '.join(layout_spec['grid_and_spacing'])}."
        )

    lines.append("")
    lines.append("### Motion & Composition")
    lines.append("- Stack datablocks into coherent streams; avoid fragmented visual noise.")
    lines.append("- Apply progressive offsets (25%-75%) to reinforce depth and motion cues.")
    if visual_spec and visual_spec.get("imagery_style"):
        imagery_notes = []
        for field, items in visual_spec["imagery_style"].items():
            if items:
                imagery_notes.append(f"{field.replace('_', ' ')}: {', '.join(items)}")
        if imagery_notes:
            lines.append(f"- Imagery cues: {'; '.join(imagery_notes)}.")

    return Section(title="Visual System", body=lines)


def _corner_radius_section(
    evidence: Optional[AggregatedEvidence],
    *,
    layout_spec: Optional[Dict[str, Any]] = None,
) -> Section:
    whitespace_levels = []
    if evidence:
        whitespace_levels = [img.layout.whitespace_ratio for img in evidence.images if img.layout]
    average_whitespace = mean(whitespace_levels) if whitespace_levels else 0.35

    lines: List[str] = []
    lines.append("### Radius Guidance")
    if average_whitespace >= 0.5:
        lines.append("- Embrace softer 16px-20px radii for hero containers; whitespace supports openness.")
    elif average_whitespace >= 0.3:
        lines.append("- Standard 12px-16px radii keep content structured while preserving flow.")
    else:
        lines.append("- Use tighter 8px radii on dense modules to maintain precision.")

    lines.append("- Datastream datablocks: default to 20% of block height for rounded corners.")
    lines.append("- Physical deliverables: scale corner radius to 1.5% of the shortest edge as baseline.")

    if layout_spec and layout_spec.get("interaction_notes"):
        lines.append(f"- Interaction cues: {', '.join(layout_spec['interaction_notes'])}.")

    return Section(title="Corner Radius", body=lines)


def _iconography_section(
    palette: Sequence[ColorSwatch],
    *,
    imagery_spec: Optional[Iterable[str]] = None,
) -> Section:
    colors = list(palette)
    base_color = colors[0].hex if colors else "#00A1DE"

    lines: List[str] = []
    lines.append("### Icon Library")
    lines.append("- Leverage Material Symbols Rounded set at optical size 40 for accessibility.")
    lines.append(f"- Primary tint: {base_color} with white fill for contrast.")
    if len(colors) > 1:
        lines.append(f"- Secondary tint: {colors[1].hex} for hover states or SMB contexts.")
    lines.append("")
    lines.append("### Usage")
    lines.append("- Nest icons within datablocks; reserve standalone usage for favicons or app shortcuts.")
    lines.append("- Maintain icon containers at 150%-200% of icon bounding box for breathing room.")
    if imagery_spec:
        lines.append(f"- Icon motifs emphasised: {', '.join(imagery_spec)}.")

    return Section(title="Iconography", body=lines)


def _logo_section(
    palette: Sequence[ColorSwatch],
    *,
    logo_usage: Optional[Iterable[str]] = None,
) -> Section:
    colors = list(palette)
    primary_hex = colors[0].hex if colors else "#00A1DE"

    lines: List[str] = []
    lines.append("### Logo Lockups")
    lines.append(f"- Primary lockup: symbol + wordmark in {primary_hex} on white or deep navy.")
    lines.append("- Maintain 1x clearspace buffer around the combined lockup.")
    lines.append("- Minimum size: 24px height digital, 12mm print.")
    lines.append("")
    lines.append("### Symbol Guidance")
    lines.append("- Reserve mono symbol for avatars and favicons where scale is restricted.")
    lines.append("- When color is limited, default to black/white paired set.")
    if logo_usage:
        lines.append(f"- Additional notes: {', '.join(logo_usage)}.")

    return Section(title="Logo", body=lines)


def _color_section(
    palette: Sequence[ColorSwatch],
    *,
    palette_spec: Optional[List[Dict[str, Any]]] = None,
) -> Section:
    colors = list(palette)

    lines: List[str] = []
    lines.append("### Palette Overview")
    if palette_spec:
        lines.append("| Hex | Names | Usage | Finishes | Notes |")
        lines.append("| --- | ----- | ----- | -------- | ----- |")
        for color in palette_spec:
            names = ", ".join(color.get("names", [])) or "—"
            usage = ", ".join(color.get("usage_notes", [])) or "—"
            finishes = ", ".join(color.get("finishes", [])) or "—"
            notes = ", ".join(color.get("additional_notes", [])) or "—"
            lines.append(f"| {color.get('hex', '—')} | {names} | {usage} | {finishes} | {notes} |")
    else:
        if not colors:
            lines.append("- No colors detected; verify source assets and rerun analysis.")
            return Section(title="Color", body=lines)
        lines.append("| Hex | Name | Recommended Usage |")
        lines.append("| --- | ---- | ----------------- |")
        for swatch in colors:
            lines.append(f"| {swatch.hex} | {swatch.name} | {swatch.usage_hint} |")

    lines.append("")
    lines.append("- Ensure minimum 4.5:1 contrast for primary copy against backgrounds.")
    lines.append("- Assign accent hues to thrive data streams; limit to 20% coverage per layout.")

    return Section(title="Color", body=lines)


def _production_notes_section(
    production_notes: Sequence[str],
    confidence_notes: Sequence[Dict[str, Any]],
) -> Section:
    lines: List[str] = []
    if production_notes:
        lines.append("### Production Notes")
        for note in production_notes:
            lines.append(f"- {note}")
    if confidence_notes:
        if lines:
            lines.append("")
        lines.append("### Confidence & Follow-ups")
        for entry in confidence_notes:
            image = entry.get("image", "asset")
            note = entry.get("note", "")
            lines.append(f"- **{image}:** {note}")
    return Section(title="Production References", body=lines or ["- No outstanding notes."])


def _swatches_from_palette_spec(palette_spec: List[Dict[str, Any]]) -> List[ColorSwatch]:
    swatches: List[ColorSwatch] = []
    for idx, color in enumerate(palette_spec):
        hex_value = color.get("hex", "#000000")
        names = color.get("names") or []
        usage = color.get("usage_notes") or []
        prominence = max(0.5 - idx * 0.1, 0.1)
        swatches.append(
            ColorSwatch(
                hex=hex_value,
                name=names[0] if names else hex_value,
                prominence=prominence,
                usage_hint=", ".join(usage) if usage else "Detail accent",
            )
        )
    if not swatches:
        swatches.append(ColorSwatch(hex="#00A1DE", name="Bynder Blue", prominence=0.6, usage_hint="Primary anchor"))
    return swatches


def _uppercase_ratio(lines: Iterable[str]) -> float:
    letters = 0
    uppercase = 0
    for line in lines:
        for char in line:
            if char.isalpha():
                letters += 1
                if char.isupper():
                    uppercase += 1
    if letters == 0:
        return 0.0
    return uppercase / letters


def _relative_brightness(hex_value: str) -> float:
    hex_clean = hex_value.lstrip("#")
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


__all__ = [
    "GuidelineDocument",
    "Section",
    "build_document",
    "build_document_from_spec",
    "render_markdown",
]
