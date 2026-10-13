import type { Landmark } from './cephaloShared';

/**
 * Presentation-only viewport for extrapolated reference lines. Never edits a
 * landmark, a line's source coordinates, a persisted measurement or an image.
 * If reliable image-space bounds are unavailable we deliberately do not clip.
 */
export interface CephaloConstructionViewport {
  x: number;
  y: number;
  width: number;
  height: number;
  limited: boolean;
}
export function getCephaloConstructionViewport(
  landmarks: ReadonlyArray<Pick<Landmark, 'x' | 'y'>>,
  imageWidth: number,
  imageHeight: number,
): CephaloConstructionViewport {
  const full = { x: 0, y: 0, width: imageWidth, height: imageHeight, limited: false };
  if (!(Number.isFinite(imageWidth) && imageWidth > 0 && Number.isFinite(imageHeight) && imageHeight > 0)) return full;
  const inImage = landmarks.filter(point =>
    Number.isFinite(point.x) && Number.isFinite(point.y) &&
    point.x >= 0 && point.x <= imageWidth && point.y >= 0 && point.y <= imageHeight,
  );
  if (inImage.length < 4) return full;
  const left = Math.min(...inImage.map(p => p.x));
  const right = Math.max(...inImage.map(p => p.x));
  const top = Math.min(...inImage.map(p => p.y));
  const bottom = Math.max(...inImage.map(p => p.y));
  if (!(right > left && bottom > top)) return full;
  // Preserve all landmarks with a generous margin. Only the infinitely
  // extended visual rays are clipped; ordinary point-to-point lines are not.
  const padX = Math.max(imageWidth * 0.08, 24);
  const padY = Math.max(imageHeight * 0.08, 24);
  const x = Math.max(0, left - padX);
  const y = Math.max(0, top - padY);
  const maxX = Math.min(imageWidth, right + padX);
  const maxY = Math.min(imageHeight, bottom + padY);
  const width = maxX - x;
  const height = maxY - y;
  if (!(width > 0 && height > 0)) return full;
  return { x, y, width, height, limited: x > 0 || y > 0 || maxX < imageWidth || maxY < imageHeight };
}
