#!/usr/bin/env python3
"""Integrate independently AI-rendered holiday scene masters into the art kit.

DO NOT synthesize holiday visuals with PIL. This tool only validates and copies
finished raster artwork. It never stretches a square frame into a wide frame.
Run after the normal background build. --strict requires all 480 masters.
"""
from pathlib import Path
from PIL import Image
import argparse
import shutil

HOLIDAYS = (
    "christmas", "july4", "easter", "halloween", "newyear",
    "thanksgiving", "memorial", "labor", "birthday_a", "birthday_b"
)
WEATHER = ("sunny", "partly", "cloudy", "rain", "heavy", "storm", "snow", "fog")
PHASES = ("day", "twilight", "night")
SIZE_TYPES = {"square": (1.0, 896), "wide": (2.0, 1400)}

def expected_names():
    for event in HOLIDAYS:
        for weather in WEATHER:
            for phase in PHASES:
                root = f"holiday_{event}_{weather}_{phase}"
                yield root + ".jpg", "square"
                yield root + "_wide.jpg", "wide"

def validate_one(path, size_type):
    ratio, min_width = SIZE_TYPES[size_type]
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        w, h = image.size
        if image.format != "JPEG":
            raise ValueError(f"{path}: expected JPEG, got {image.format}")
        if w < min_width or abs(w / h - ratio) > .02:
            raise ValueError(
                f"{path}: expected {size_type} ratio {ratio}:1 and width >= {min_width}; got {w}x{h}"
            )

def integrate(source: Path, destination: Path, strict=False):
    if not source.is_dir():
        raise FileNotFoundError(f"AI master directory missing: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    missing = []
    supplied = 0
    for name, size_type in expected_names():
        img = source / name
        if not img.exists():
            missing.append(name)
            continue
        validate_one(img, size_type)
        shutil.copy2(img, destination / name)
        supplied += 1
    if strict and missing:
        raise RuntimeError(
            f"Only {supplied}/480 AI-rendered masters. Missing: " + ", ".join(missing[:12])
        )
    print(f"AI-rendered art integrated: {supplied}/480. Remaining: {len(missing)}.")
    return supplied, missing

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("artwork/photoreal"))
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    integrate(args.source, args.destination, strict=args.strict)
