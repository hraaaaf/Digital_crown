import type { Landmark } from '../cephaloShared';

/**
 * Presentation-only label placement. Never mutate landmark geometry or feed
 * these coordinates back to persistence, measurements, or pointer handlers.
 */
export interface CephaloLabelPlacement {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export const cephaloLabelFontSize = (imageWidth: number, imageHeight: number): number =>
  Math.max(42, Math.min(64, Math.max(imageWidth / 35, imageHeight / 35)));

export function layoutCephaloLandmarkLabels(
  landmarks: Pick<Landmark, 'id' | 'x' | 'y'>[],
  requestedIds: ReadonlySet<string>,
  priorityId: string | null,
  imageWidth: number,
  imageHeight: number,
): Map<string, CephaloLabelPlacement> {
  const result = new Map<string, CephaloLabelPlacement>();
  if (!(imageWidth > 0 && imageHeight > 0)) return result;
  const font = cephaloLabelFontSize(imageWidth, imageHeight);
  const candidates = landmarks
    .filter(pt => requestedIds.has(pt.id) && Number.isFinite(pt.x) && Number.isFinite(pt.y))
    .sort((a, b) => Number(b.id === priorityId) - Number(a.id === priorityId)
      || a.id.localeCompare(b.id));
  const occupied: CephaloLabelPlacement[] = [];
  const margin = font * 0.3;
  for (const pt of candidates) {
    const width = Math.max(font * 1.3, (pt.id.length * 0.68 + 0.6) * font);
    const height = font * 1.35;
    if (width + margin * 2 > imageWidth || height + margin * 2 > imageHeight) continue;
    const shift = font * 1.1;
    const origins = [
      { x: pt.x + shift, y: pt.y - shift },
      { x: pt.x - shift - width, y: pt.y - shift },
      { x: pt.x + shift, y: pt.y + shift + height * 0.15 },
      { x: pt.x - shift - width, y: pt.y + shift + height * 0.15 },
      { x: pt.x + shift * 1.8, y: pt.y - height * 0.1 },
      { x: pt.x - shift * 1.8 - width, y: pt.y - height * 0.1 },
    ];
    for (const origin of origins) {
      const x = Math.max(margin, Math.min(imageWidth - margin - width, origin.x));
      const y = Math.max(margin + height, Math.min(imageHeight - margin, origin.y));
      const box = { id: pt.id, x, y, width, height };
      // SVG text anchor is the baseline. Include a margin between labels.
      const collides = occupied.some(existing =>
        x < existing.x + existing.width + margin
        && x + width + margin > existing.x
        && y - height < existing.y + margin
        && y + margin > existing.y - existing.height);
      if (collides) continue;
      occupied.push(box);
      result.set(pt.id, box);
      break;
    }
  }
  return result;
}
