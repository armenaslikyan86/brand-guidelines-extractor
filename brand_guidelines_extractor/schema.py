"""Structured output schema definition for brand guidelines."""

from typing import Any, Dict

BRAND_GUIDELINES_SCHEMA: Dict[str, Any] = {
    "name": "brand_guidelines",
    "schema": {
        "type": "object",
        "properties": {
            "brand_identity": {
                "type": "object",
                "properties": {
                    "brand_name": {
                        "type": "string",
                        "description": "Inferred or explicit brand/product",
                    },
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
                    "tagline": {
                        "type": "string",
                        "description": "Headline copy or slogan if visible",
                    },
                },
                "additionalProperties": False,
                "required": [
                    "brand_name",
                    "design_context",
                    "core_attributes",
                    "tagline",
                ],
            },
            "visual_identity": {
                "type": "object",
                "properties": {
                    "color_palette": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Descriptive label if discernible",
                                },
                                "hex": {
                                    "type": "string",
                                    "description": "Hex approximation pulled from the artwork",
                                },
                                "finish": {
                                    "type": "string",
                                    "description": "Finish or texture hints (matte, gradient, etc.)",
                                },
                                "usage": {
                                    "type": "string",
                                    "description": "Where and how the color appears",
                                },
                                "notes": {"type": "string"},
                            },
                            "additionalProperties": False,
                            "required": ["name", "hex", "finish", "usage", "notes"],
                        },
                    },
                    "typography": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "family": {"type": "string"},
                                "style": {
                                    "type": "string",
                                    "description": "Weight or stylistic treatment",
                                },
                                "size_range": {
                                    "type": "string",
                                    "description": "Point sizes or hierarchy if legible",
                                },
                                "usage": {
                                    "type": "string",
                                    "description": "Typical use (e.g., headings, body copy)",
                                },
                                "tracking": {
                                    "type": "string",
                                    "description": "Kerning/letter-spacing observations",
                                },
                                "notes": {"type": "string"},
                            },
                            "additionalProperties": False,
                            "required": [
                                "family",
                                "style",
                                "size_range",
                                "usage",
                                "tracking",
                                "notes",
                            ],
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
                        "additionalProperties": False,
                        "required": [
                            "photography",
                            "illustration",
                            "iconography",
                            "textures_and_patterns",
                        ],
                    },
                },
                "additionalProperties": False,
                "required": [
                    "color_palette",
                    "typography",
                    "logo_usage",
                    "imagery_style",
                ],
            },
            "layout_and_components": {
                "type": "object",
                "properties": {
                    "grid_and_spacing": {"type": "array", "items": {"type": "string"}},
                    "key_components": {"type": "array", "items": {"type": "string"}},
                    "call_to_action_treatment": {"type": "array", "items": {"type": "string"}},
                    "interaction_notes": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
                "required": [
                    "grid_and_spacing",
                    "key_components",
                    "call_to_action_treatment",
                    "interaction_notes",
                ],
            },
            "voice_and_copy": {
                "type": "object",
                "properties": {
                    "tone_descriptors": {"type": "array", "items": {"type": "string"}},
                    "messaging_pillars": {"type": "array", "items": {"type": "string"}},
                    "dos": {"type": "array", "items": {"type": "string"}},
                    "donts": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
                "required": [
                    "tone_descriptors",
                    "messaging_pillars",
                    "dos",
                    "donts",
                ],
            },
            "production_notes": {"type": "array", "items": {"type": "string"}},
            "confidence": {
                "type": "string",
                "description": "Statement on confidence or areas needing confirmation",
            },
        },
        "required": [
            "brand_identity",
            "visual_identity",
            "layout_and_components",
            "voice_and_copy",
            "production_notes",
            "confidence",
        ],
        "additionalProperties": False,
    },
}

__all__ = ["BRAND_GUIDELINES_SCHEMA"]
