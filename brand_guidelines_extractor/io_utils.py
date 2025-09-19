"""Utility helpers for I/O, environment management, and image handling."""

from __future__ import annotations

import base64
import mimetypes
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

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


def collect_image_paths(
    inputs: Sequence[str],
    input_dir: Optional[Path],
    recursive: bool,
    supported_exts: Iterable[str] = SUPPORTED_IMAGE_EXTENSIONS,
) -> List[Path]:
    """Gather unique image paths from direct inputs and optional directories."""

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


def guess_mime_type(path: Path) -> str:
    """Best-effort mime-type detection for image files."""

    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "image/png"


def encode_image_as_data_url(data: bytes, mime_type: str) -> str:
    """Encode raw image data as a data URL expected by the Responses API."""

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def load_env_file(path: Path) -> None:
    """Populate environment variables from a KEY=VALUE dotenv file."""

    if not path.is_file():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except OSError as exc:
        print(f"Failed to read env file {path}: {exc}", file=sys.stderr)


__all__ = [
    "SUPPORTED_IMAGE_EXTENSIONS",
    "collect_image_paths",
    "guess_mime_type",
    "encode_image_as_data_url",
    "load_env_file",
]
