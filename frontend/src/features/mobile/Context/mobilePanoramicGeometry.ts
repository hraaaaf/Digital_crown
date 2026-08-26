export interface PanoramicTransform {
  scale: number;
  x: number;
  y: number;
}

export interface PanoramicGeometry {
  width: number;
  height: number;
  imageWidth: number;
  imageHeight: number;
}

export const PANORAMIC_MIN_SCALE = 1;
export const PANORAMIC_MAX_SCALE = 4;
export const PANORAMIC_SCALE_STEP = 0.5;
export const PANORAMIC_RESET: PanoramicTransform = { scale: 1, x: 0, y: 0 };

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

export function clampPanoramicScale(value: number): number {
  return clamp(Number.isFinite(value) ? value : PANORAMIC_MIN_SCALE, PANORAMIC_MIN_SCALE, PANORAMIC_MAX_SCALE);
}

export function containedPanoramicSize(geometry: PanoramicGeometry): { width: number; height: number } {
  const width = Math.max(1, geometry.width);
  const height = Math.max(1, geometry.height);
  const imageWidth = Math.max(1, geometry.imageWidth);
  const imageHeight = Math.max(1, geometry.imageHeight);
  const ratio = Math.min(width / imageWidth, height / imageHeight);
  return { width: imageWidth * ratio, height: imageHeight * ratio };
}

export function clampPanoramicTransform(transform: PanoramicTransform, geometry: PanoramicGeometry): PanoramicTransform {
  const scale = clampPanoramicScale(transform.scale);
  if (scale <= PANORAMIC_MIN_SCALE) return { ...PANORAMIC_RESET };
  const fitted = containedPanoramicSize(geometry);
  const maxX = Math.max(0, (fitted.width * scale - geometry.width) / 2);
  const maxY = Math.max(0, (fitted.height * scale - geometry.height) / 2);
  return {
    scale,
    x: clamp(Number.isFinite(transform.x) ? transform.x : 0, -maxX, maxX),
    y: clamp(Number.isFinite(transform.y) ? transform.y : 0, -maxY, maxY),
  };
}

export function zoomPanoramicAt(
  transform: PanoramicTransform,
  targetScale: number,
  anchor: { x: number; y: number },
  geometry: PanoramicGeometry,
): PanoramicTransform {
  const nextScale = clampPanoramicScale(targetScale);
  if (nextScale === PANORAMIC_MIN_SCALE) return { ...PANORAMIC_RESET };
  const currentScale = clampPanoramicScale(transform.scale);
  const ratio = nextScale / currentScale;
  const centerX = geometry.width / 2;
  const centerY = geometry.height / 2;
  const next = {
    scale: nextScale,
    x: anchor.x - centerX - (anchor.x - centerX - transform.x) * ratio,
    y: anchor.y - centerY - (anchor.y - centerY - transform.y) * ratio,
  };
  return clampPanoramicTransform(next, geometry);
}

export function panPanoramicBy(
  transform: PanoramicTransform,
  dx: number,
  dy: number,
  geometry: PanoramicGeometry,
): PanoramicTransform {
  return clampPanoramicTransform({ ...transform, x: transform.x + dx, y: transform.y + dy }, geometry);
}
