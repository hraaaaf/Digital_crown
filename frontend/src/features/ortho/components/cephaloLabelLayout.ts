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
  fontOverride?: number,
): Map<string, CephaloLabelPlacement> {
  const result = new Map<string, CephaloLabelPlacement>();
  if (!(imageWidth > 0 && imageHeight > 0)) return result;
  const font = fontOverride && Number.isFinite(fontOverride) && fontOverride > 0
    ? fontOverride : cephaloLabelFontSize(imageWidth, imageHeight);
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
    if (fontOverride) {
      origins.push(
        { x: pt.x + shift * 2.6, y: pt.y - height },
        { x: pt.x - shift * 2.6 - width, y: pt.y - height },
        { x: pt.x + shift * 2.6, y: pt.y + height },
        { x: pt.x - shift * 2.6 - width, y: pt.y + height },
        { x: pt.x + shift * 3.5, y: pt.y - height * 0.25 },
        { x: pt.x - shift * 3.5 - width, y: pt.y - height * 0.25 },
      );
    }
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


/**
 * R21.2 desktop editorial layout: every anatomical name gets a stable text
 * position on one of two visual rails. This only creates presentation data.
 * The source landmarks, calibrated measurements and editing remain untouched.
 */
export interface CephaloPerimeterLabel {
  id: string;
  x: number;
  y: number;
  side: 'left' | 'right';
  sourceX: number;
  sourceY: number;
  leaderEndX: number;
  leaderEndY: number;
}

export function layoutCephaloPerimeterLabels(
  landmarks: Pick<Landmark, 'id' | 'x' | 'y'>[],
  viewport: string,
  unitsPerPixel: number,
): Map<string, CephaloPerimeterLabel> {
  const result = new Map<string, CephaloPerimeterLabel>();
  const parts = viewport.trim().split(/\s+/).map(Number);
  if (parts.length !== 4 || parts.some(value => !Number.isFinite(value))) return result;
  const [vx, vy, vw, vh] = parts;
  if (vw <= 0 || vh <= 0 || !Number.isFinite(unitsPerPixel) || unitsPerPixel <= 0) return result;
  const scale = Math.max(0.1, Math.min(unitsPerPixel, 30));
  const pad = 13 * scale;
  const points = landmarks.filter(pt => Number.isFinite(pt.x) && Number.isFinite(pt.y))
    .slice().sort((a, b) => a.x - b.x || a.y - b.y || a.id.localeCompare(b.id));
  const left = points.slice(0, Math.ceil(points.length / 2));
  const right = points.slice(Math.ceil(points.length / 2));
  const clamp = (value: number, low: number, high: number) => Math.max(low, Math.min(high, value));
  const place = (side: 'left' | 'right', column: typeof points) => {
    const rows = column.slice().sort((a, b) => a.y - b.y || a.id.localeCompare(b.id));
    // Floating image controls occupy the top and bottom corners on tall
    // radiographs. Reserve these lanes where vertical room permits, while
    // preserving 22.5px minimum row pitch for the desktop 38-name layout.
    const stageHeightCss = vh / scale;
    const verticalPadCss = Math.min(74, Math.max(13,
      (stageHeightCss - rows.length * 22.5) / 2));
    const verticalPad = verticalPadCss * scale;
    const step = (vh - verticalPad * 2) / Math.max(1, rows.length);
    const x = side === 'left' ? vx + pad : vx + vw - pad;
    rows.forEach((pt, index) => {
      const y = vy + verticalPad + (index + 0.5) * step + 5.5 * scale;
      // Full clinical name, never a relabeled or truncated anatomical ID.
      const approxWidth = pt.id.length * 9.7 * scale;
      const leaderEndX = side === 'left'
        ? Math.min(x + approxWidth + 7 * scale, vx + vw * 0.47)
        : Math.max(x - approxWidth - 7 * scale, vx + vw * 0.53);
      result.set(pt.id, {
        id: pt.id, x, y, side,
        sourceX: clamp(pt.x, vx + pad, vx + vw - pad),
        sourceY: clamp(pt.y, vy + pad, vy + vh - pad),
        leaderEndX,
        leaderEndY: y - 5 * scale,
      });
    });
  };
  place('left', left);
  place('right', right);
  return result;
}
