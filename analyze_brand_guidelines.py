"""Brand guidelines extractor powered by GPT-4o Vision.

This script inspects one or more design reference images and produces a
structured brand guidelines specification that designers can hand off to
stakeholders. Outputs can be emitted as JSON (default) or Markdown.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - library availability depends on environment
    raise SystemExit(
        "openai package is required to run this script. Install it with 'pip install openai'."
    ) from exc


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

SYSTEM_PROMPT = (
    "You are a senior brand designer and art director. Deliver precise, actionable "
    "brand guidelines extracted strictly from the provided reference image. Avoid "
    "speculation beyond visible evidence and clearly flag low-confidence insights."
)

USER_PROMPT_TEMPLATE = (
    "You are reviewing the design reference: {image_name}.\n"
    "Create a professional brand guidelines specification tailored for designers and "
    "stakeholders. Base every insight on tangible cues in the image.\n\n"
    "For each section use concise bullet points, note measurements or hierarchies when "
    "legible, and annotate any assumptions as 'needs confirmation'.\n"
    "Capture: brand tone, color palette, typography, logo usage, imagery style, layout "
    "structure, spacing rules, CTA handling, and any production notes that could impact "
    "handoff."
)

BRAND_GUIDELINES_SCHEMA: Dict[str, Any] = {
    "name": "brand_guidelines",
    "schema": {
        "type": "object",
        "properties": {
            "brand_identity": {
                "type": "object",
                "properties": {
                    "brand_name": {"type": "string", "description": "Inferred or explicit brand/product"},
                    "design_context": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Usage scenarios or campaign context inferred from the layout",
                    },
                    "core_attributes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords that describe the brand voice or personality",
                    },
                    "tagline": {"type": "string", "description": "Headline copy or slogan if visible"},
                },
            },
            "visual_identity": {
                "type": "object",
                "properties": {
                    "color_palette": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Descriptive label if discernible"},
                                "hex": {"type": "string", "description": "Hex approximation pulled from the artwork"},
                                "finish": {"type": "string", "description": "Finish or texture hints (matte, gradient, etc.)"},
                                "usage": {"type": "string", "description": "Where and how the color appears"},
                                "notes": {"type": "string"},
                            },
                            "required": ["hex"],
                        },
                    },
                    "typography": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "family": {"type": "string"},
                                "style": {"type": "string", "description": "Weight or stylistic treatment"},
                                "size_range": {"type": "string", "description": "Point sizes or hierarchy if legible"},
                                "usage": {"type": "string", "description": "Typical use (e.g., headings, body copy)"},
                                "tracking": {"type": "string", "description": "Kerning/letter-spacing observations"},
                                "notes": {"type": "string"},
                            },
                            "required": ["family"],
                        },
                    },
                    "logo_usage": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Logo placement, clear space, and treatment notes",
                    },
                    "imagery_style": {
                        "type": "object",
                        "properties": {
                            "photography": {"type": "array", "items": {"type": "string"}},
                            "illustration": {"type": "array", "items": {"type": "string"}},
                            "iconography": {"type": "array", "items": {"type": "string"}},
                            "textures_and_patterns": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "required": ["color_palette", "typography"],
            },
            "layout_and_components": {
                "type": "object",
                "properties": {
                    "grid_and_spacing": {"type": "array", "items": {"type": "string"}},
                    "key_components": {"type": "array", "items": {"type": "string"}},
                    "call_to_action_treatment": {"type": "array", "items": {"type": "string"}},
                    "interaction_notes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "voice_and_copy": {
                "type": "object",
                "properties": {
                    "tone_descriptors": {"type": "array", "items": {"type": "string"}},
                    "messaging_pillars": {"type": "array", "items": {"type": "string"}},
                    "dos": {"type": "array", "items": {"type": "string"}},
                    "donts": {"type": "array", "items": {"type": "string"}},
                },
            },
            "production_notes": {"type": "array", "items": {"type": "string"}},
            "confidence": {
                "type": "string",
                "description": "Statement on confidence or areas needing confirmation",
            },
        },
        "required": ["visual_identity"],
    },
}


def collect_image_paths(
    inputs: Sequence[str],
    input_dir: Optional[Path],
    recursive: bool,
    supported_exts: Iterable[str] = SUPPORTED_IMAGE_EXTENSIONS,
) -> List[Path]:
    """Gather unique image paths from direct inputs and an optional directory."""

    supported = {ext.lower() for ext in supported_exts}
    ordered_paths: List[Path] = []
    seen: set[Path] = set()

    def add_path(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        if not resolved.is_file():
            return
        if resolved.suffix.lower() not in supported:
            return
        seen.add(resolved)
        ordered_paths.append(resolved)

    def walk_directory(directory: Path) -> None:
        if not directory.exists():
            print(f"Skipping missing directory: {directory}", file=sys.stderr)
            return
        pattern = "**/*" if recursive else "*"
        for candidate in directory.glob(pattern):
            if candidate.is_file() and candidate.suffix.lower() in supported:
                add_path(candidate)

    for raw in inputs:
        path = Path(raw).expanduser()
        if path.is_dir():
            walk_directory(path)
        else:
            add_path(path)

    if input_dir:
        walk_directory(input_dir.expanduser())

    return ordered_paths


def build_client(api_key: Optional[str]) -> OpenAI:
    """Instantiate an OpenAI client with the provided API key or environment variable."""

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            "OpenAI API key not provided. Set OPENAI_API_KEY env var or pass --api-key."
        )
    return OpenAI(api_key=key)


def analyze_image(
    client: OpenAI,
    image_path: Path,
    model: str,
    temperature: float,
    max_output_tokens: int,
) -> Optional[Dict[str, Any]]:
    """Call GPT-4o Vision on a single image and return the structured guidelines."""

    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        print(f"Failed to read {image_path}: {exc}", file=sys.stderr)
        return None

    prompt = USER_PROMPT_TEMPLATE.format(image_name=image_path.name)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image": {"bytes": image_bytes}},
                    ],
                },
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_format={"type": "json_schema", "json_schema": BRAND_GUIDELINES_SCHEMA},
        )
    except Exception as exc:  # pragma: no cover - depends on network/API availability
        print(f"OpenAI request failed for {image_path}: {exc}", file=sys.stderr)
        return None

    raw_output = getattr(response, "output_text", "").strip()
    if not raw_output:
        print(f"Empty response for {image_path}", file=sys.stderr)
        return None

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        print(f"Failed to parse JSON for {image_path}: {exc}: {raw_output}", file=sys.stderr)
        return None

    return parsed


def _merge_sets(source: Iterable[str], target: set[str]) -> None:
    for item in source or []:
        cleaned = (item or "").strip()
        if cleaned:
            target.add(cleaned)


def aggregate_guidelines(per_image: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine per-image guideline dictionaries into a consolidated view."""

    compiled: Dict[str, Any] = {
        "brand_identity": {
            "brand_names": set(),
            "design_context": set(),
            "core_attributes": set(),
            "taglines": set(),
        },
        "visual_identity": {
            "color_palette": {},
            "typography": {},
            "logo_usage": set(),
            "imagery_style": {
                "photography": set(),
                "illustration": set(),
                "iconography": set(),
                "textures_and_patterns": set(),
            },
        },
        "layout_and_components": {
            "grid_and_spacing": set(),
            "key_components": set(),
            "call_to_action_treatment": set(),
            "interaction_notes": set(),
        },
        "voice_and_copy": {
            "tone_descriptors": set(),
            "messaging_pillars": set(),
            "dos": set(),
            "donts": set(),
        },
        "production_notes": set(),
        "confidence_notes": [],
    }

    for record in per_image:
        image = record.get("image")
        data = record.get("guidelines") or {}

        identity = data.get("brand_identity", {})
        name = (identity.get("brand_name") or "").strip()
        if name:
            compiled["brand_identity"]["brand_names"].add(name)
        _merge_sets(identity.get("design_context", []), compiled["brand_identity"]["design_context"])
        _merge_sets(identity.get("core_attributes", []), compiled["brand_identity"]["core_attributes"])
        tagline = (identity.get("tagline") or "").strip()
        if tagline:
            compiled["brand_identity"]["taglines"].add(tagline)

        visual = data.get("visual_identity", {})
        palette: Dict[str, Any] = compiled["visual_identity"]["color_palette"]
        for color in visual.get("color_palette", []) or []:
            hex_value = (color.get("hex") or "").strip().upper()
            if not hex_value:
                continue
            entry = palette.setdefault(
                hex_value,
                {
                    "hex": hex_value,
                    "names": set(),
                    "usages": set(),
                    "finishes": set(),
                    "notes": set(),
                    "source_images": set(),
                },
            )
            if image:
                entry["source_images"].add(image)
            for field, key in (("name", "names"), ("usage", "usages"), ("finish", "finishes"), ("notes", "notes")):
                value = (color.get(field) or "").strip()
                if value:
                    entry[key].add(value)

        type_map: Dict[Tuple[str, str], Dict[str, Any]] = compiled["visual_identity"]["typography"]
        for typo in visual.get("typography", []) or []:
            family = (typo.get("family") or "").strip()
            if not family:
                continue
            style = (typo.get("style") or "unspecified").strip() or "unspecified"
            key = (family.lower(), style.lower())
            entry = type_map.setdefault(
                key,
                {
                    "family": family,
                    "styles": set(),
                    "usages": set(),
                    "size_ranges": set(),
                    "tracking": set(),
                    "notes": set(),
                    "source_images": set(),
                },
            )
            entry["styles"].add(style)
            for attr, target_key in (("usage", "usages"), ("size_range", "size_ranges"), ("tracking", "tracking"), ("notes", "notes")):
                value = (typo.get(attr) or "").strip()
                if value:
                    entry[target_key].add(value)
            if image:
                entry["source_images"].add(image)

        _merge_sets(visual.get("logo_usage", []), compiled["visual_identity"]["logo_usage"])

        imagery = visual.get("imagery_style", {}) or {}
        for field in ("photography", "illustration", "iconography", "textures_and_patterns"):
            _merge_sets(imagery.get(field, []), compiled["visual_identity"]["imagery_style"][field])

        layout = data.get("layout_and_components", {}) or {}
        for field in ("grid_and_spacing", "key_components", "call_to_action_treatment", "interaction_notes"):
            _merge_sets(layout.get(field, []), compiled["layout_and_components"][field])

        voice = data.get("voice_and_copy", {}) or {}
        for field in ("tone_descriptors", "messaging_pillars", "dos", "donts"):
            _merge_sets(voice.get(field, []), compiled["voice_and_copy"][field])

        _merge_sets(data.get("production_notes", []), compiled["production_notes"])

        confidence = (data.get("confidence") or "").strip()
        if confidence and image:
            compiled["confidence_notes"].append({"image": image, "note": confidence})

    return {
        "images_analyzed": len(per_image),
        "compiled": _finalize_compiled(compiled),
        "per_image": per_image,
    }


def _finalize_compiled(compiled: Dict[str, Any]) -> Dict[str, Any]:
    """Convert internal sets to sorted lists for serialization."""

    brand = compiled["brand_identity"]
    visual = compiled["visual_identity"]
    layout = compiled["layout_and_components"]
    voice = compiled["voice_and_copy"]

    finalized_palette: List[Dict[str, Any]] = []
    for color in visual["color_palette"].values():
        finalized_palette.append(
            {
                "hex": color["hex"],
                "names": sorted(color["names"]),
                "usage_notes": sorted(color["usages"]),
                "finishes": sorted(color["finishes"]),
                "additional_notes": sorted(color["notes"]),
                "source_images": sorted(color["source_images"]),
            }
        )
    finalized_palette.sort(key=lambda item: item["hex"])

    finalized_typography: List[Dict[str, Any]] = []
    for entry in visual["typography"].values():
        styles = sorted(s for s in entry["styles"] if s != "unspecified")
        if not styles and "unspecified" in entry["styles"]:
            styles = ["unspecified"]
        finalized_typography.append(
            {
                "family": entry["family"],
                "styles": styles,
                "usage": sorted(entry["usages"]),
                "size_ranges": sorted(entry["size_ranges"]),
                "tracking": sorted(entry["tracking"]),
                "notes": sorted(entry["notes"]),
                "source_images": sorted(entry["source_images"]),
            }
        )
    finalized_typography.sort(key=lambda item: item["family"].lower())

    return {
        "brand_identity": {
            "brand_names": sorted(brand["brand_names"]),
            "design_context": sorted(brand["design_context"]),
            "core_attributes": sorted(brand["core_attributes"]),
            "taglines": sorted(brand["taglines"]),
        },
        "visual_identity": {
            "color_palette": finalized_palette,
            "typography": finalized_typography,
            "logo_usage": sorted(visual["logo_usage"]),
            "imagery_style": {
                field: sorted(values)
                for field, values in visual["imagery_style"].items()
            },
        },
        "layout_and_components": {
            field: sorted(values) for field, values in layout.items()
        },
        "voice_and_copy": {field: sorted(values) for field, values in voice.items()},
        "production_notes": sorted(compiled["production_notes"]),
        "confidence_notes": compiled["confidence_notes"],
    }


def render_markdown(aggregated: Dict[str, Any]) -> str:
    """Generate a polished Markdown report from the aggregated data."""

    compiled = aggregated.get("compiled", {})
    lines: List[str] = ["# Brand Guidelines Specification", ""]
    lines.append(f"- Images analyzed: {aggregated.get('images_analyzed', 0)}")
    lines.append("")

    brand = compiled.get("brand_identity", {})
    if any(brand.values()):
        lines.append("## Brand Identity")
        if brand.get("brand_names"):
            lines.append(f"- **Brand references:** {', '.join(brand['brand_names'])}")
        if brand.get("design_context"):
            lines.append("- **Design context cues:**" )
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


def run_analysis(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute analysis workflow and return aggregated data."""

    image_paths = collect_image_paths(
        inputs=args.images,
        input_dir=Path(args.input_dir).expanduser() if args.input_dir else None,
        recursive=args.recursive,
    )

    if not image_paths:
        raise SystemExit("No valid images were found to analyze.")

    client = build_client(args.api_key)

    results: List[Dict[str, Any]] = []
    for path in image_paths:
        print(f"Analyzing {path}...")
        guidelines = analyze_image(
            client=client,
            image_path=path,
            model=args.model,
            temperature=args.temperature,
            max_output_tokens=args.max_output_tokens,
        )
        if guidelines:
            results.append({"image": str(path), "guidelines": guidelines})
        elif args.fail_fast:
            raise SystemExit(f"Analysis failed for {path}; aborting due to --fail-fast.")

    if not results:
        raise SystemExit("No analyses succeeded. Please check the logs above.")

    return aggregate_guidelines(results)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured brand guidelines from design assets using GPT-4o Vision.",
    )
    parser.add_argument("images", nargs="*", help="Specific image files or directories to analyze.")
    parser.add_argument(
        "--input-dir",
        help="Directory containing design assets to scan. Supports JPG, PNG, GIF, WEBP, BMP, TIF.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search within --input-dir or directory arguments.",
    )
    parser.add_argument(
        "--output",
        help="Output file path. If omitted, results are printed to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "md"],
        default="json",
        help="Select output format (JSON or Markdown).",
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key. If absent, OPENAI_API_KEY environment variable is used.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Vision-capable OpenAI model identifier (default: gpt-4o).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the model (default: 0.2).",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for the model response (default: 1024).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort execution if any image analysis fails.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    aggregated = run_analysis(args)

    if args.format == "json":
        output_str = json.dumps(aggregated, indent=2, ensure_ascii=False)
    else:
        output_str = render_markdown(aggregated)

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.write_text(output_str, encoding="utf-8")
        print(f"Results written to {output_path}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
