# Brand Guidelines Extractor

This proof-of-concept CLI inspects design reference images with OpenAI's GPT-4o Vision and produces a polished brand-guidelines specification that designers can hand off to stakeholders.

## Prerequisites

- Python 3.9+
- `pip install openai`
- An OpenAI API key with access to GPT-4o (set `OPENAI_API_KEY` or pass `--api-key`)

## Quick Start

1. Place one or more reference images inside the provided `design_assets/` directory (or point to any directory/file path you prefer).
2. Run the analyzer, choosing JSON (default) or Markdown output.

```bash
python3 analyze_brand_guidelines.py \
  --input-dir design_assets \
  --format md \
  --output brand-guidelines.md
```

That command scans every supported image in `design_assets/`, calls GPT-4o Vision, aggregates results across all files, and saves a client-ready Markdown report to `brand-guidelines.md`.

If you would rather view structured JSON, omit `--format md` and/or `--output` to print directly to the terminal.

## Supported Asset Types

Images with extensions: PNG, JPG, JPEG, GIF, WEBP, BMP, TIF, TIFF. Use `--recursive` to crawl nested folders.

## Additional Options

- `--images`: provide explicit image paths or directories alongside/outside `--input-dir`.
- `--fail-fast`: stop immediately if any image fails to process.
- `--model`, `--temperature`, `--max-output-tokens`: tune OpenAI model behavior.

See `python3 analyze_brand_guidelines.py --help` for the full flag list.

## Output Overview

Each run produces:

- A consolidated summary of brand identity, visual identity, layout, and copy insights deduplicated across all inputs.
- Detailed color palette and typography tables with usage notes.
- Production notes and confidence call-outs so designers know where to verify details.
- Embedded per-image JSON extracts for auditability.

Use the report as a starting point for handoffs, design reviews, or further documentation.
