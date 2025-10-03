"""CLI entrypoint for the design guideline synthesizer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .analyzer import aggregate as aggregate_local, analyze_paths
from .guidelines import build_document, build_document_from_spec, render_markdown
from .io_utils import collect_image_paths, load_env_file
from .pipeline import aggregated_to_dict


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate brand guideline references from design assets.",
    )
    parser.add_argument("images", nargs="*", help="Specific image files or directories to analyze.")
    parser.add_argument(
        "--input-dir",
        help="Directory containing design assets to scan. Supports common raster formats.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search directories for images.",
    )
    parser.add_argument(
        "--output",
        help="Destination file path. Defaults to stdout output.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "md"],
        default="md",
        help="Select output format (default: md).",
    )
    parser.add_argument(
        "--brand-name",
        default="Bynder",
        help="Brand label to embed in the guideline title.",
    )
    parser.add_argument(
        "--engine",
        choices=["openai", "local"],
        default="openai",
        help="Analysis engine: OpenAI GPT vision or local heuristics (default: openai).",
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (defaults to OPENAI_API_KEY env var when omitted).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI vision-capable model identifier (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for OpenAI runs (default: 0.2).",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for OpenAI responses (default: 1024).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort OpenAI analysis if any image fails to process.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to preload environment variables (default: .env).",
    )
    return parser.parse_args(argv)


def _collect_paths(args: argparse.Namespace) -> list[Path]:
    return collect_image_paths(
        inputs=args.images,
        input_dir=Path(args.input_dir).expanduser() if args.input_dir else None,
        recursive=args.recursive,
    )


def _run_local(paths: list[Path], args: argparse.Namespace) -> str:
    extractions = analyze_paths(paths)
    evidence = aggregate_local(extractions)

    if args.format == "json":
        payload = {
            "brand_name": args.brand_name,
            "engine": "local",
            "evidence": aggregated_to_dict(evidence),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    document = build_document(evidence, brand_name=args.brand_name)
    return render_markdown(document)


def _run_openai(paths: list[Path], args: argparse.Namespace) -> str:
    if args.env_file:
        load_env_file(Path(args.env_file).expanduser())

    from . import openai_integration as openai_api  # Imported lazily to avoid mandatory dependency.

    client = openai_api.build_client(args.api_key)

    per_image: list[dict[str, object]] = []
    for path in paths:
        print(f"Analyzing {path} with OpenAI...")
        guidelines = openai_api.analyze_image(
            client=client,
            image_path=path,
            model=args.model,
            temperature=args.temperature,
            max_output_tokens=args.max_output_tokens,
        )
        if guidelines:
            per_image.append({"image": str(path), "guidelines": guidelines})
        elif args.fail_fast:
            raise SystemExit(f"Analysis failed for {path}; aborting due to --fail-fast.")

    if not per_image:
        raise SystemExit("No analyses succeeded; check API credentials and retry.")

    design_spec = openai_api.aggregate_guidelines(per_image)

    if args.format == "json":
        payload = {
            "brand_name": args.brand_name,
            "engine": "openai",
            "design_spec": design_spec,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    # Supplement OpenAI data with local heuristics for layout cues.
    local_evidence = aggregate_local(analyze_paths(paths))
    document = build_document_from_spec(
        design_spec,
        brand_name=args.brand_name,
        evidence=local_evidence,
    )
    return render_markdown(document)


def run_analysis(args: argparse.Namespace) -> str:
    paths = _collect_paths(args)
    if not paths:
        raise SystemExit("No valid images were found to analyze.")

    if args.engine == "local":
        return _run_local(paths, args)
    return _run_openai(paths, args)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    output = run_analysis(args)

    if args.output:
        destination = Path(args.output).expanduser()
        destination.write_text(output, encoding="utf-8")
        print(f"Guidelines written to {destination}")
    else:
        print(output)


__all__ = ["parse_args", "run_analysis", "main"]
