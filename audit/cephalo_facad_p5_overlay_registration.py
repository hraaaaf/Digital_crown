"""P5: photographic overlay/coordinate congruence; NOT landmark anatomy proof.

Input screenshot stays PRIVATE, never committed to a public repository/CI artifacts.
Actual screenshot displays Bergen short (not Ricketts 32F); positional evidence
does not certify FACAD measurement protocols, clinician-reviewed landmark identity
or any Digital Crown clinical parity.

A human selects TWO unmistakable corresponding displayed landmark ring centers
and supplies them separately. Their 2-point fit has zero independent degrees of
freedom for the anchors; therefore report out-of-sample points separately.
A hit means thresholded red pixels nearby, NOT unique correct marker identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def read_public_facad_coordinates(path: Path) -> dict[str, tuple[float, float]]:
    """Accept only pinned, de-identified public fixture; never vendor text exports."""
    from audit import cephalo_facad_robert_public_ci as demo
    require(path.resolve(strict=True) == demo.FIXTURE.resolve(strict=True),
            "only pinned public educational coordinates accepted")
    fixture = demo.read_checked_fixture(path)
    # The helper above yields results, not coordinates.
    require(fixture["clinical_no_go"] is True, "unsafe source input")
    content = json.loads(path.read_text(encoding="utf-8"))
    points = content["points_mm"]
    require(len(points) == 30 and content["coordinate_rounding_mm"] == 0.1,
            "coordinate source format drift")
    return {key: (float(v[0]), float(v[1])) for key, v in points.items()}


def similarity_from_two_anchors(
    points_mm: dict[str, tuple[float, float]],
    anchors_px: dict[str, tuple[float, float]],
) -> tuple[complex, complex]:
    """Return z_pixel = scale_rotate*z_mm + translation; axes are not invented."""
    require(type(points_mm) is dict and type(anchors_px) is dict and len(anchors_px) == 2,
            "exactly two explicit matching visual anchors required")
    labels = list(anchors_px)
    require(all(k in points_mm for k in labels), "anchor missing from point export")
    entries = [(*points_mm[name], *anchors_px[name]) for name in labels]
    require(all(type(v) in (int, float) and math.isfinite(v)
                for row in entries for v in row),
            "nonfinite registration coordinate")
    p1, p2 = [complex(*points_mm[name]) for name in labels]
    z1, z2 = [complex(*anchors_px[name]) for name in labels]
    require(abs(p2 - p1) > 1.0 and abs(z2 - z1) > 1.0,
            "ill-conditioned or degenerate registration anchors")
    coefficient = (z2 - z1) / (p2 - p1)
    require(math.isfinite(abs(coefficient)) and 0.1 < abs(coefficient) < 100.0,
            "implausible educational display scale")
    offset = z1 - coefficient * p1
    return coefficient, offset


def red_pixel_match(
    image, x: float, y: float, *, radius_px: float = 4.0,
    min_red_pixels: int = 3,
) -> bool:
    """Read Pillow RGB image only at the projected location, no OCR or PII."""
    require(math.isfinite(x) and math.isfinite(y) and
            0 < radius_px <= 12 and
            isinstance(min_red_pixels, int) and 1 <= min_red_pixels <= 15,
            "invalid image overlay criteria")
    w, h = image.size
    if x < radius_px or y < radius_px or x >= w-radius_px or y >= h-radius_px:
        return False
    points = 0
    for j in range(math.floor(y-radius_px), math.ceil(y+radius_px)+1):
        for i in range(math.floor(x-radius_px), math.ceil(x+radius_px)+1):
            if (i-x)**2 + (j-y)**2 > radius_px**2:
                continue
            r,g,b = image.getpixel((i,j))[:3]
            if r > 150 and r-g > 70 and r-b > 70:
                points += 1
                if points >= min_red_pixels:
                    return True
    return False


def assess(
    image,
    points_mm: dict[str, tuple[float, float]],
    anchors_px: dict[str, tuple[float, float]],
    *,
    radius_px: float = 4.0,
    min_red_pixels: int = 3,
) -> dict:
    require(image.mode in {"RGB", "RGBA"}, "image must be RGB or RGBA")
    coefficient, offset = similarity_from_two_anchors(points_mm, anchors_px)
    hit_map = {}
    for name,(x,y) in points_mm.items():
        position = coefficient * complex(x,y) + offset
        hit_map[name] = red_pixel_match(image, position.real, position.imag,
                                        radius_px=radius_px,
                                        min_red_pixels=min_red_pixels)
    independent = {name: ok for name,ok in hit_map.items()
                   if name not in anchors_px}
    require(len(hit_map) == 30 and len(independent) == 28,
            "public Robert anchor cardinality drift")
    return {
        "schema_version": "FACAD_P5_SCREENSHOT_OVERLAY_CONGRUENCE_NONCLINICAL_V1",
        "screenshot_uploaded_as_ci_artifact": False,
        "landmark_names_resolved_from_screenshot": False,
        "red_overlay_near_exported_coordinates_only": True,
        "fitted_anchor_count": 2,
        "out_of_sample_point_count": 28,
        "all_points_count": 30,
        "red_neighborhood_radius_pixels": radius_px,
        "red_min_pixel_count": min_red_pixels,
        "red_overlay_hits_total": sum(hit_map.values()),
        "red_overlay_hits_out_of_sample": sum(independent.values()),
        "red_overlay_misses": sorted(name for name, hit in hit_map.items() if not hit),
        "facad_analysis_visible_in_screenshot": "BERGEN_SHORT_NOT_RICKETTS_32F",
        "source_display_coordinate_frame_clinically_verified": False,
        "marker_anatomical_placement_independently_verified": False,
        "dc_pog_hard_identity_authorized": False,
        "clinical_parity_count": 0,
        "clinical_no_go": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True,
                        help="PRIVATE JSON mapping exactly two FACAD names to visual pixel centers")
    parser.add_argument("--aggregate-only", action="store_true",
                        help="Never print landmark names or pixel coordinates")
    args = parser.parse_args()
    try:
        from PIL import Image
        from audit import cephalo_facad_robert_public_ci as demo
        points = read_public_facad_coordinates(demo.FIXTURE)
        supplied = json.loads(args.anchors.read_text(encoding="utf-8"))
        anchors = {name:tuple(pair) for name,pair in supplied.items()}
        with Image.open(args.screenshot) as im:
            result = assess(im.convert("RGB"), points, anchors)
        result["input_image_sha256"] = hashlib.sha256(args.screenshot.read_bytes()).hexdigest()
    except (OSError, ValueError, TypeError, ImportError, KeyError,
            json.JSONDecodeError) as exc:
        print("FACAD_P5_SCREENSHOT_OVERLAY=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    if args.aggregate_only:
        result.pop("red_overlay_misses", None)
        result.pop("input_image_sha256", None)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
