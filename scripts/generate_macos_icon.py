from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

SIZES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("frontend/public/icon-512.png"))
    ap.add_argument("--output", type=Path, default=Path("build/macos/DigitalCrown.iconset"))
    args = ap.parse_args()

    image = Image.open(args.source).convert("RGBA")
    if image.width != image.height:
        raise SystemExit(f"macOS icon source must be square, got {image.width}x{image.height}")
    if image.width < 512:
        raise SystemExit(f"macOS icon source must be at least 512x512, got {image.width}x{image.height}")

    args.output.mkdir(parents=True, exist_ok=True)
    for filename, size in SIZES:
        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(args.output / filename, format="PNG", optimize=True)

    print(
        f"P7_MACOS_ICONSET=SUCCESS source={image.width}x{image.height} "
        f"output={args.output} upscaled_1024={'yes' if image.width < 1024 else 'no'}"
    )


if __name__ == "__main__":
    main()
