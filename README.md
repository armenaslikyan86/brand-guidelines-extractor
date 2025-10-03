# Design Data Analyzer

This CLI inspects design reference images and can operate in two modes:

1. **OpenAI mode (default)** — calls GPT-4o vision to extract rich design data and renders Bynder-style guidelines.
2. **Local mode** — runs deterministic heuristics (color, layout, lightweight OCR) without any network dependency.

## Prerequisites

- Python 3.9+
- Install dependencies via `python3 -m pip install -r requirements.txt` (includes `openai`, `numpy`, `Pillow`, `pytest`).
- Optional: [`pytesseract`](https://pypi.org/project/pytesseract/) and the Tesseract binary to improve on-device text extraction when using local mode.

## Quick Start

1. Drop design assets into `design_assets/` or point the CLI at a preferred directory.
2. Create a `.env` containing `OPENAI_API_KEY=...` (or pass `--api-key`).
3. Generate the guideline document with OpenAI (default engine):

```bash
python3 analyze_design_data.py \
  --input-dir design_assets \
  --format md \
  --output generated_guidelines/bynder-guidelines.md
```

The command scans supported images, calls OpenAI to extract structured design data, merges local heuristics for layout cues, and renders Markdown styled after the official Bynder brand guidelines. Omit `--output` to print to the terminal. Switch to `--format json` to inspect the raw design spec.

## Supported Asset Types

Images with extensions: PNG, JPG, JPEG, GIF, WEBP, BMP, TIF, TIFF. Use `--recursive` to traverse nested folders. Combine explicit paths via positional arguments with `--input-dir` for bespoke batches.

## CLI Highlights

- `--engine`: Choose `openai` (default) or `local` for offline heuristics.
- `--brand-name`: Override the title in the generated document (default: Bynder).
- `--format`: Select `md` (default) or `json` output.
- `--recursive`: Scan directories recursively.
- `--env-file`: Load environment variables (e.g., API keys) from a dotenv file.

Run `python3 analyze_design_data.py --help` for the full flag list.

## Outputs

The analyzer creates:

- A Markdown guideline set mirroring sections such as Tone of Voice, Social Media, Visual System, Corner Radius, Iconography, Logo, and Color.
- An aggregated OpenAI design spec (JSON) plus local evidence for downstream automation.
- Optional JSON output capturing either the full OpenAI spec or the local heuristic evidence.

Use the resulting document as the baseline for downstream design automation and manual reviews.
