"""G5 LAB V2 editable cutaneous Bézier handles.

This is manual geometry only, NOT an anatomical inference or validation.
Canonical polylines remain the V1 authority for the two PDF views.
"""
from __future__ import annotations

from math import ceil, floor, hypot, isfinite
from typing import Any

MAX_NODES = 150
MAX_SAMPLES = 600
STEP_PIXELS = 5


class G5BezierRejected(ValueError):
    pass


def _pixel(raw: Any, width: int, height: int) -> list[float]:
    if not isinstance(raw, list) or len(raw) != 2:
        raise G5BezierRejected("G5_BEZIER_INVALID_HANDLE")
    if any(type(v) not in (int, float) or not isfinite(v) for v in raw):
        raise G5BezierRejected("G5_BEZIER_NONFINITE_HANDLE")
    x, y = raw
    if not 0 <= x < width or not 0 <= y < height:
        raise G5BezierRejected("G5_BEZIER_HANDLE_OUTSIDE_IMAGE")
    return [float(x), float(y)]


def _distance(a: list[float], b: list[float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _round_tenth(value: float) -> float:
    # JS Math.round used by g5SampleBezierContour for positive source pixels.
    return floor(value * 10 + 0.5) / 10


def canonical_bezier_profile_nodes(
    nodes: object, *, image_size: tuple[int, int],
) -> list[dict[str, list[float]]]:
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= MAX_NODES:
        raise G5BezierRejected("G5_BEZIER_NODE_COUNT_INVALID")
    width, height = image_size
    if not all(type(a) is int and 1 <= a <= 10000 for a in image_size):
        raise G5BezierRejected("G5_BEZIER_IMAGE_SIZE_INVALID")
    out = []
    for node in nodes:
        if type(node) is not dict or set(node) != {"anchor", "incoming", "outgoing"}:
            raise G5BezierRejected("G5_BEZIER_NODE_SCHEMA_INVALID")
        out.append({name: _pixel(node[name], width, height)
                    for name in ("anchor", "incoming", "outgoing")})
    for i in range(len(out) - 1):
        if _distance(out[i]["anchor"], out[i + 1]["anchor"]) < 0.5:
            raise G5BezierRejected("G5_BEZIER_DEGENERATE_SEGMENT")
    return out


def sample_bezier_profile(
    nodes: object, *, image_size: tuple[int, int],
) -> list[list[float]]:
    canonical = canonical_bezier_profile_nodes(nodes, image_size=image_size)
    output: list[list[float]] = []
    for idx in range(len(canonical) - 1):
        start = canonical[idx]["anchor"]
        control1 = canonical[idx]["outgoing"]
        control2 = canonical[idx + 1]["incoming"]
        end = canonical[idx + 1]["anchor"]
        control_length = (_distance(start, control1)
                          + _distance(control1, control2)
                          + _distance(control2, end))
        steps = max(2, ceil(control_length / STEP_PIXELS))
        for k in range(0 if idx == 0 else 1, steps + 1):
            t = k / steps
            q = 1 - t
            p = [
                q**3 * start[d] + 3*q*q*t * control1[d]
                + 3*q*t*t * control2[d] + t**3 * end[d]
                for d in (0, 1)
            ]
            point = [_round_tenth(v) for v in p]
            if output and _distance(output[-1], point) < 0.5:
                continue
            output.append(point)
            if len(output) > MAX_SAMPLES:
                raise G5BezierRejected("G5_BEZIER_TOO_MANY_SAMPLES")
    if len(output) < 2:
        raise G5BezierRejected("G5_BEZIER_INSUFFICIENT_SAMPLES")
    return output


def verify_bezier_profile_matches(
    nodes: object, *,
    contours: list[dict[str, Any]],
    image_size: tuple[int, int],
) -> list[dict[str, list[float]]]:
    canonical = canonical_bezier_profile_nodes(nodes, image_size=image_size)
    profile = next((x for x in contours if x.get("id") == "soft_tissue_profile"), None)
    if profile is None:
        raise G5BezierRejected("G5_BEZIER_SOFT_TISSUE_MISSING")
    expected = sample_bezier_profile(canonical, image_size=image_size)
    actual = profile.get("points")
    if not isinstance(actual, list) or len(actual) != len(expected):
        raise G5BezierRejected("G5_BEZIER_SAMPLES_DIFFER_FROM_V1")
    for given, sampled in zip(actual, expected):
        if not isinstance(given, list) or len(given) != 2 or any(
            type(v) not in (float, int) or not isfinite(v) for v in given
        ):
            raise G5BezierRejected("G5_BEZIER_SAMPLES_DIFFER_FROM_V1")
        if any(abs(a - b) > 1e-7 for a, b in zip(given, sampled)):
            raise G5BezierRejected("G5_BEZIER_SAMPLES_DIFFER_FROM_V1")
    return canonical
