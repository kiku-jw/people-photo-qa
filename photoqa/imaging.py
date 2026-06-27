"""Image inspection helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def iter_image_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            paths.append(path)
    return sorted(paths)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(path: Path) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
            image.verify()
    except Exception:
        return {
            "ok": False,
            "width": None,
            "height": None,
            "mode": None,
            "error": "unreadable_image",
        }
    return {
        "ok": True,
        "width": int(width),
        "height": int(height),
        "mode": mode,
        "error": None,
    }


def basic_quality(width: int | None, height: int | None, mode: str | None) -> dict[str, Any]:
    if width is None or height is None or width <= 0 or height <= 0:
        return {
            "quality_score": 0.0,
            "quality_flags": ["missing_dimensions"],
            "payload": {
                "megapixels": None,
                "aspect_ratio": None,
                "usable_for_basic_review": False,
            },
        }

    flags: list[str] = []
    megapixels = (width * height) / 1_000_000
    aspect_ratio = width / height

    if min(width, height) < 512:
        flags.append("low_resolution")
    if megapixels < 0.25:
        flags.append("very_low_megapixels")
    if aspect_ratio < 0.35 or aspect_ratio > 2.8:
        flags.append("unusual_aspect_ratio")
    if mode not in {"RGB", "RGBA", "L"}:
        flags.append("unusual_color_mode")

    dimension_score = min(min(width, height) / 1024, 1.0)
    megapixel_score = min(megapixels / 1.5, 1.0)
    aspect_score = 1.0 if 0.5 <= aspect_ratio <= 2.0 else 0.65
    mode_score = 1.0 if mode in {"RGB", "RGBA", "L"} else 0.75
    quality_score = round(
        (dimension_score * 0.45) + (megapixel_score * 0.25) + (aspect_score * 0.20) + (mode_score * 0.10),
        4,
    )

    return {
        "quality_score": quality_score,
        "quality_flags": flags,
        "payload": {
            "megapixels": round(megapixels, 4),
            "aspect_ratio": round(aspect_ratio, 4),
            "usable_for_basic_review": quality_score >= 0.55 and not flags,
        },
    }
