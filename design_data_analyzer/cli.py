"""CLI entrypoint for the design data analyzer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .analyzer import aggregate_guidelines, analyze_image, build_client
from .io_utils import collect_image_paths, load_env_file
from .reporting import render_markdown


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured design data from visual assets using GPT-4o Vision.",
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
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to preload environment variables (default: .env).",
    )
    return parser.parse_args(argv)


def run_analysis(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the analysis workflow and return aggregated guideline data."""

    image_paths = collect_image_paths(
        inputs=args.images,
        input_dir=Path(args.input_dir).expanduser() if args.input_dir else None,
        recursive=args.recursive,
    )

    if not image_paths:
        raise SystemExit("No valid images were found to analyze.")

    if args.env_file:
        load_env_file(Path(args.env_file).expanduser())

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


__all__ = ["parse_args", "run_analysis", "main"]
