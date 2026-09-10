"""SRPose38 runtime preprocessing and DarkPose decoding.

This module intentionally mirrors the inference geometry used by the validated
SRPose38 ONNX parity workflow. The ONNX asset already embeds horizontal flip
TTA; runtime code must not apply a second flip.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

SRPOSE38_INPUT_SIZE: Tuple[int, int] = (1024, 1024)  # (width, height)
SRPOSE38_NUM_LANDMARKS = 38
SRPOSE38_BBOX_PADDING = 1.25
SRPOSE38_MEAN = np.array([121.25, 121.25, 121.25], dtype=np.float32)
SRPOSE38_STD = np.array([76.5, 76.5, 76.5], dtype=np.float32)
SRPOSE38_DARKPOSE_BLUR_KERNEL = 11


@dataclass(frozen=True)
class SRPose38Geometry:
    center: np.ndarray
    scale: np.ndarray
    input_size: np.ndarray


def _fix_aspect_ratio(scale: np.ndarray, input_size: Tuple[int, int]) -> np.ndarray:
    """Match MMPose TopdownAffine aspect-ratio correction."""
    w, h = float(scale[0]), float(scale[1])
    aspect_ratio = float(input_size[0]) / float(input_size[1])
    if w > h * aspect_ratio:
        h = w / aspect_ratio
    elif w < h * aspect_ratio:
        w = h * aspect_ratio
    return np.array([w, h], dtype=np.float32)


def full_image_center_scale(
    image_shape: Tuple[int, ...],
    padding: float = SRPOSE38_BBOX_PADDING,
    input_size: Tuple[int, int] = SRPOSE38_INPUT_SIZE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Reproduce GetBBoxCenterScale + TopdownAffine for full-image bbox."""
    height, width = image_shape[:2]
    center = np.array([width * 0.5, height * 0.5], dtype=np.float32)
    scale = np.array([width, height], dtype=np.float32) * np.float32(padding)
    scale = _fix_aspect_ratio(scale, input_size)
    return center, scale


def get_warp_matrix(
    center: np.ndarray,
    scale: np.ndarray,
    output_size: Tuple[int, int] = SRPOSE38_INPUT_SIZE,
) -> np.ndarray:
    """MMPose get_warp_matrix for rot=0, shift=(0,0), inv=False."""
    center = np.asarray(center, dtype=np.float32)
    scale = np.asarray(scale, dtype=np.float32)
    src_w = float(scale[0])
    dst_w, dst_h = float(output_size[0]), float(output_size[1])

    src = np.zeros((3, 2), dtype=np.float32)
    src[0] = center
    src[1] = center + np.array([0.0, -0.5 * src_w], dtype=np.float32)
    direction = src[0] - src[1]
    src[2] = src[1] + np.array([-direction[1], direction[0]], dtype=np.float32)

    dst = np.zeros((3, 2), dtype=np.float32)
    dst[0] = np.array([0.5 * dst_w, 0.5 * dst_h], dtype=np.float32)
    dst[1] = dst[0] + np.array([0.0, -0.5 * dst_w], dtype=np.float32)
    direction = dst[0] - dst[1]
    dst[2] = dst[1] + np.array([-direction[1], direction[0]], dtype=np.float32)

    return cv2.getAffineTransform(src, dst)


def prepare_srpose38_input(image_bgr: np.ndarray) -> Tuple[np.ndarray, SRPose38Geometry]:
    """Affine-warp BGR image, convert to RGB, normalize, return NCHW float32."""
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("SRPose38 expects a BGR image with shape HxWx3")

    center, scale = full_image_center_scale(image_bgr.shape)
    warp = get_warp_matrix(center, scale)
    warped_bgr = cv2.warpAffine(
        image_bgr,
        warp,
        SRPOSE38_INPUT_SIZE,
        flags=cv2.INTER_LINEAR,
    )
    rgb = warped_bgr[..., ::-1].astype(np.float32)
    normalized = (rgb - SRPOSE38_MEAN) / SRPOSE38_STD
    tensor = np.ascontiguousarray(normalized.transpose(2, 0, 1)[None, ...], dtype=np.float32)
    geometry = SRPose38Geometry(
        center=center,
        scale=scale,
        input_size=np.array(SRPOSE38_INPUT_SIZE, dtype=np.float32),
    )
    return tensor, geometry


def _heatmap_maximum(heatmaps: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if heatmaps.ndim != 3:
        raise ValueError(f"Expected KxHxW heatmaps, got {heatmaps.shape}")
    keypoints_count, height, width = heatmaps.shape
    flat = heatmaps.reshape(keypoints_count, -1)
    y_locs, x_locs = np.unravel_index(np.argmax(flat, axis=1), shape=(height, width))
    locs = np.stack((x_locs, y_locs), axis=-1).astype(np.float32)
    vals = np.amax(flat, axis=1)
    locs[vals <= 0.0] = -1
    return locs, vals


def _gaussian_blur(heatmaps: np.ndarray, kernel: int) -> np.ndarray:
    if kernel % 2 != 1:
        raise ValueError("DarkPose Gaussian kernel must be odd")
    border = (kernel - 1) // 2
    keypoints_count, height, width = heatmaps.shape
    for idx in range(keypoints_count):
        origin_max = np.max(heatmaps[idx])
        padded = np.zeros((height + 2 * border, width + 2 * border), dtype=np.float32)
        padded[border:-border, border:-border] = heatmaps[idx].copy()
        padded = cv2.GaussianBlur(padded, (kernel, kernel), 0)
        blurred = padded[border:-border, border:-border].copy()
        blurred_max = np.max(blurred)
        if blurred_max != 0:
            blurred *= origin_max / blurred_max
        heatmaps[idx] = blurred
    return heatmaps


def _refine_keypoints_dark(
    keypoints: np.ndarray,
    heatmaps: np.ndarray,
    blur_kernel_size: int = SRPOSE38_DARKPOSE_BLUR_KERNEL,
) -> np.ndarray:
    """Exact DarkPose refinement used by the pinned MMPose SRPose source."""
    instances, keypoints_count = keypoints.shape[:2]
    height, width = heatmaps.shape[1:]

    heatmaps = _gaussian_blur(heatmaps, blur_kernel_size)
    np.maximum(heatmaps, 1e-10, out=heatmaps)
    np.log(heatmaps, out=heatmaps)

    for instance_idx in range(instances):
        for keypoint_idx in range(keypoints_count):
            x, y = keypoints[instance_idx, keypoint_idx, :2].astype(int)
            if 1 < x < width - 2 and 1 < y < height - 2:
                hm = heatmaps[keypoint_idx]
                dx = 0.5 * (hm[y, x + 1] - hm[y, x - 1])
                dy = 0.5 * (hm[y + 1, x] - hm[y - 1, x])
                dxx = 0.25 * (hm[y, x + 2] - 2 * hm[y, x] + hm[y, x - 2])
                dxy = 0.25 * (
                    hm[y + 1, x + 1]
                    - hm[y - 1, x + 1]
                    - hm[y + 1, x - 1]
                    + hm[y - 1, x - 1]
                )
                dyy = 0.25 * (hm[y + 2, x] - 2 * hm[y, x] + hm[y - 2, x])
                det = dxx * dyy - dxy**2
                if det != 0:
                    derivative = np.array([[dx], [dy]])
                    hessian = np.array([[dxx, dxy], [dxy, dyy]])
                    offset = -np.linalg.inv(hessian) @ derivative
                    keypoints[instance_idx, keypoint_idx, :2] += offset[:, 0]
    return keypoints


def decode_srpose38_heatmaps(
    encoded: np.ndarray,
    geometry: SRPose38Geometry,
) -> Tuple[np.ndarray, np.ndarray]:
    """Decode 38 ONNX heatmaps to original-image coordinates."""
    heatmaps = np.asarray(encoded)
    if heatmaps.ndim == 4:
        if heatmaps.shape[0] != 1:
            raise ValueError(f"SRPose38 runtime only supports batch=1, got {heatmaps.shape}")
        heatmaps = heatmaps[0]
    expected = (SRPOSE38_NUM_LANDMARKS, SRPOSE38_INPUT_SIZE[1], SRPOSE38_INPUT_SIZE[0])
    if heatmaps.shape != expected:
        raise ValueError(f"Unexpected SRPose38 heatmap shape {heatmaps.shape}, expected {expected}")
    if not np.isfinite(heatmaps).all():
        raise ValueError("SRPose38 returned non-finite heatmaps")

    work = heatmaps.astype(np.float32, copy=True)
    keypoints, scores = _heatmap_maximum(work)
    keypoints = _refine_keypoints_dark(keypoints[None, ...], work)[0]

    input_size = geometry.input_size.astype(np.float64)
    scale = geometry.scale.astype(np.float64)
    center = geometry.center.astype(np.float64)
    original = keypoints.astype(np.float64) / input_size * scale + center - 0.5 * scale

    if original.shape != (SRPOSE38_NUM_LANDMARKS, 2) or not np.isfinite(original).all():
        raise ValueError("SRPose38 decoded invalid landmark coordinates")
    return original, scores.astype(np.float32, copy=False)
