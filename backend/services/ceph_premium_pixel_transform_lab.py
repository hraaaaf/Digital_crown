"""J2.1-M2 isolated 2D pixel-coordinate transforms; no clinical authority.

Coordinates refer to ORIGINAL image pixels as stored (before EXIF display
orientation). The UI maps them to orientation-correct viewport coordinates.
All affine operations are invertible and deterministic. Never resample or
silently overwrite original source coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


class PixelTransformError(ValueError):
    pass


def _finite(*values: float) -> None:
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise PixelTransformError("Coordinates and transforms must be finite")


@dataclass(frozen=True, slots=True)
class SourceView:
    width: int
    height: int
    orientation: int = 1  # EXIF orientation: 1..8.
    crop_x: float = 0
    crop_y: float = 0
    crop_width: float | None = None
    crop_height: float | None = None
    viewport_width: int = 1280
    viewport_height: int = 900
    zoom: float = 1.0
    pan_x: float = 0
    pan_y: float = 0

    def __post_init__(self):
        if any(type(z) is not int or z < 2 or z > 20000
               for z in (self.width, self.height, self.viewport_width, self.viewport_height)):
            raise PixelTransformError("Unsupported original/viewport dimensions")
        if type(self.orientation) is not int or not 1 <= self.orientation <= 8:
            raise PixelTransformError("Unsupported EXIF orientation")
        _finite(self.crop_x, self.crop_y, self.zoom, self.pan_x, self.pan_y)
        if not 0.1 <= self.zoom <= 12:
            raise PixelTransformError("Invalid zoom")
        ow, oh = self.oriented_size
        cw = ow - self.crop_x if self.crop_width is None else self.crop_width
        ch = oh - self.crop_y if self.crop_height is None else self.crop_height
        _finite(cw, ch)
        if (cw <= 1 or ch <= 1 or self.crop_x < 0 or self.crop_y < 0
            or self.crop_x + cw > ow or self.crop_y + ch > oh):
            raise PixelTransformError("Invalid crop in oriented image reference")
        object.__setattr__(self, "crop_width", float(cw))
        object.__setattr__(self, "crop_height", float(ch))

    @property
    def oriented_size(self) -> tuple[int, int]:
        return ((self.height, self.width) if self.orientation in (5, 6, 7, 8)
                else (self.width, self.height))

    def orient(self, x: float, y: float) -> tuple[float, float]:
        _finite(x, y)
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise PixelTransformError("Point outside original image")
        w, h = self.width, self.height
        return {
            1: (x, y),
            2: (w - 1 - x, y),
            3: (w - 1 - x, h - 1 - y),
            4: (x, h - 1 - y),
            5: (y, x),
            6: (h - 1 - y, x),
            7: (h - 1 - y, w - 1 - x),
            8: (y, w - 1 - x),
        }[self.orientation]

    def deorient(self, x: float, y: float) -> tuple[float, float]:
        _finite(x, y)
        if self.orientation in (1, 2, 3, 4):
            w, h = self.width, self.height
            originals = {1: (x, y), 2: (w - 1 - x, y),
                         3: (w - 1 - x, h - 1 - y), 4: (x, h - 1 - y)}
        else:
            w, h = self.width, self.height
            originals = {5: (y, x), 6: (y, h - 1 - x),
                         7: (w - 1 - y, h - 1 - x), 8: (w - 1 - y, x)}
        ox, oy = originals[self.orientation]
        # Affine forward/inverse division can introduce ~1e-13 negative
        # drift exactly at pixel zero; accept only this machine epsilon,
        # not arbitrary off-image mouse coordinates.
        if not (-1e-9 <= ox < self.width and -1e-9 <= oy < self.height):
            raise PixelTransformError("Mapped point outside original image")
        return max(0.0, ox), max(0.0, oy)

    @property
    def scale_and_origin(self) -> tuple[float, float, float]:
        scale = min(
            self.viewport_width / self.crop_width,
            self.viewport_height / self.crop_height,
        ) * self.zoom
        return (
            scale,
            (self.viewport_width - self.crop_width * scale) / 2 + self.pan_x,
            (self.viewport_height - self.crop_height * scale) / 2 + self.pan_y,
        )

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        ox, oy = self.orient(x, y)
        scale, left, top = self.scale_and_origin
        return (
            (ox - self.crop_x) * scale + left,
            (oy - self.crop_y) * scale + top,
        )

    def to_original(self, px: float, py: float) -> tuple[float, float]:
        _finite(px, py)
        scale, left, top = self.scale_and_origin
        ox = (px - left) / scale + self.crop_x
        oy = (py - top) / scale + self.crop_y
        return self.deorient(ox, oy)

    def point_in_crop(self, x: float, y: float) -> bool:
        ox, oy = self.orient(x, y)
        return (self.crop_x <= ox < self.crop_x + self.crop_width
                and self.crop_y <= oy < self.crop_y + self.crop_height)
