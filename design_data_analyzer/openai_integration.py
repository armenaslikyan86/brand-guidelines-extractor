"""OpenAI-powered extraction utilities for design guideline generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - requires optional dependency
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - environment specific
    raise SystemExit(
        "openai package is required for --engine openai. Install it with 'pip install openai'."
    ) from exc

from .io_utils import encode_image_as_data_url, guess_mime_type
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from .schema import DESIGN_DATA_SCHEMA


def build_client(api_key: Optional[str]) -> OpenAI:
    """Instantiate an OpenAI client using a provided or environment API key."""

    key = api_key or _read_env_api_key()
    if not key:
        raise SystemExit(
            "OpenAI API key not provided. Set OPENAI_API_KEY, pass --api-key, or load it via --env-file."
        )
    return OpenAI(api_key=key)


def analyze_image(
    client: OpenAI,
    image_path: Path,
    *,
    model: str,
    temperature: float,
    max_output_tokens: int,
) -> Optional[Dict[str, Any]]:
    """Call GPT vision to extract structured design data for a single image."""

    try:
        image_bytes = image_path.read_bytes()
    except OSError as exc:
        print(f"Failed to read {image_path}: {exc}", file=sys.stderr)
        return None

    prompt = USER_PROMPT_TEMPLATE.format(image_name=image_path.name)
    mime_type = guess_mime_type(image_path)
    data_url = encode_image_as_data_url(image_bytes, mime_type)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url, "detail": "auto"},
                    ],
                },
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": DESIGN_DATA_SCHEMA["name"],
                    "schema": DESIGN_DATA_SCHEMA["schema"],
                    "strict": True,
                }
            },
        )
    except Exception as exc:  # pragma: no cover - network dependent
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


def aggregate_guidelines(per_image: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine per-image guideline dictionaries into a consolidated view."""

    per_image_list = list(per_image)
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

    formatted_per_image: List[Dict[str, Any]] = []

    for record in per_image_list:
        image_path = record.get("image")
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
                    "usage_notes": set(),
                    "finishes": set(),
                    "additional_notes": set(),
                    "source_images": set(),
                },
            )
            if image_path:
                entry["source_images"].add(image_path)
            _maybe_add(color.get("name"), entry["names"])
            _maybe_add(color.get("usage"), entry["usage_notes"])
            _maybe_add(color.get("finish"), entry["finishes"])
            _maybe_add(color.get("notes"), entry["additional_notes"])

        type_map: Dict[str, Dict[str, Any]] = compiled["visual_identity"]["typography"]
        for typo in visual.get("typography", []) or []:
            family = (typo.get("family") or "").strip()
            if not family:
                continue
            style = (typo.get("style") or "").strip() or "unspecified"
            key = f"{family.lower()}::{style.lower()}"
            entry = type_map.setdefault(
                key,
                {
                    "family": family,
                    "styles": set(),
                    "usage": set(),
                    "size_ranges": set(),
                    "tracking": set(),
                    "notes": set(),
                    "source_images": set(),
                },
            )
            entry["styles"].add(style)
            _maybe_add(typo.get("usage"), entry["usage"])
            _maybe_add(typo.get("size_range"), entry["size_ranges"])
            _maybe_add(typo.get("tracking"), entry["tracking"])
            _maybe_add(typo.get("notes"), entry["notes"])
            if image_path:
                entry["source_images"].add(image_path)

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
        if confidence and image_path:
            compiled["confidence_notes"].append({"image": image_path, "note": confidence})

        formatted_per_image.append({"image": image_path, "guidelines": data})

    return {
        "images_analyzed": len(per_image_list),
        "compiled": _finalize_compiled(compiled),
        "per_image": formatted_per_image,
    }


def _maybe_add(value: Optional[str], target: set[str]) -> None:
    cleaned = (value or "").strip()
    if cleaned:
        target.add(cleaned)


def _merge_sets(source: Iterable[str], target: set[str]) -> None:
    for item in source or []:
        _maybe_add(item, target)


def _finalize_compiled(compiled: Dict[str, Any]) -> Dict[str, Any]:
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
                "usage_notes": sorted(color["usage_notes"]),
                "finishes": sorted(color["finishes"]),
                "additional_notes": sorted(color["additional_notes"]),
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
                "usage": sorted(entry["usage"]),
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


def _read_env_api_key() -> Optional[str]:
    import os

    return os.getenv("OPENAI_API_KEY")


__all__ = ["build_client", "analyze_image", "aggregate_guidelines"]
