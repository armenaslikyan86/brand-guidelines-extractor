"""Prompt templates used for the brand guidelines extraction workflow."""

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

__all__ = ["SYSTEM_PROMPT", "USER_PROMPT_TEMPLATE"]
