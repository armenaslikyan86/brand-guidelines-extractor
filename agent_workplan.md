# Agent Workplan: Brand Guideline Automation

## Mission
Deliver an automated pipeline that ingests gallery templates under `design_assets/`, extracts brand-significant data, and synthesizes markdown guidelines that mirror `brand_guidelines_reference.md` in structure and tone.

## Current Inputs
- `design_assets/`: Source imagery (PNG/JPG/etc.) representing official templates.
- `brand_guidelines_reference.md`: Canonical example of the desired output format and voice.
- `design_data.md`: Prior manual extraction example for reference quality benchmarking.

## Key Outcomes
1. Automated extraction of colors, typography, layout cues, and copy tone from provided templates.
2. Normalized data schema that can drive guideline generation and downstream design services.
3. Generated markdown guidelines that remain faithful to Bynder standards while reflecting the analyzed assets.

## Functional Requirements
- Batch processing of new assets with idempotent runs.
- Metadata capture for each asset: file path, detected elements, confidence notes.
- Re-usable transformation mapping from raw detections to guideline sections (tone, social, visual system, corner radius, iconography, logo, color).
- Markdown generator that outputs professionally formatted guidelines with section parity to the reference file.

## Technical Expectations
- Use Python 3.10+ within the existing `design_data_analyzer/` package unless otherwise justified.
- Favor modular, testable code (e.g., separate extract/transform/generate layers).
- Provide unit coverage around parsing, normalization, and markdown rendering routines.
- Persist intermediate structured data (JSON or YAML) to support auditing and future pipelines.

## High-Level Plan
1. **Discovery:** Audit `design_assets/` for formats, naming conventions, and volume; document assumptions.
2. **Extraction Engine:** Implement detectors for palettes, typography, layout geometry, and textual copy via existing models or libraries (prefer deterministic/local tools over external APIs while network access is restricted).
3. **Normalization Layer:** Map extracted signals into a structured schema aligned with `design_data.md` and the sections in the reference guidelines.
4. **Guideline Generator:** Render markdown using templates to guarantee ordering, citation placeholders, and tone consistency.
5. **Validation:** Compare generated output against `brand_guidelines_reference.md` for structural parity; run regression tests on sample assets.
6. **Operationalization:** Wire up CLI entrypoint and document usage within README; schedule extension hooks for future template ingestion.

## Acceptance Criteria
- Running the analyzer on a curated asset subset produces a markdown file that mirrors the reference hierarchy, with asset-derived content populated per section.
- Extraction logs include confidence metrics and flag gaps requiring human review.
- Tests pass locally via `pytest` (or chosen runner) and cover core parsing and generation paths.

## Stretch Goals
- Implement diffing to highlight deviations between newly generated guidelines and the canonical reference.
- Add optional SVG/icon detection to enhance the Iconography section.
- Prepare hooks for integrating AI-assisted copy refinement once network access constraints lift.

## Deliverables
- Updated codebase under `design_data_analyzer/` supporting the above pipeline.
- New guideline markdown artifacts stored under a dedicated output directory (e.g., `generated_guidelines/`).
- Developer documentation outlining configuration, execution steps, and troubleshooting tips.

Stay aligned with the clarity, confidence, and empowerment principles defined in the brand guidelines when crafting any user-facing text or documentation.
