export const toRad = (deg: number) => (deg * Math.PI) / 180;
export const toDeg = (rad: number) => (rad * 180) / Math.PI;

export function projectPointOnLine(
  px: number, py: number,
  ax: number, ay: number,
  bx: number, by: number
): { x: number; y: number } | null {
  const dx = bx - ax;
  const dy = by - ay;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return null;
  const t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
  return { x: ax + t * dx, y: ay + t * dy };
}

export function getPerpendicularTick(
  cx: number, cy: number,
  lineAngle: number,
  tickLength: number = 16
): { x1: number; y1: number; x2: number; y2: number } {
  const perpAngle = toRad(lineAngle + 90);
  const halfLen = tickLength / 2;
  return {
    x1: cx + halfLen * Math.cos(perpAngle),
    y1: cy + halfLen * Math.sin(perpAngle),
    x2: cx - halfLen * Math.cos(perpAngle),
    y2: cy - halfLen * Math.sin(perpAngle),
  };
}

export function polarPoint(cx: number, cy: number, r: number, angleDeg: number) {
  return {
    x: cx + r * Math.cos(toRad(angleDeg)),
    y: cy + r * Math.sin(toRad(angleDeg)),
  };
}

/**
 * buildWedgePath — secteur angulaire SVG (anneau creux ou plein).
 * Clamp à ±359.99° pour éviter le cercle dégénéré.
 */
export function buildWedgePath(
  cx: number, cy: number,
  rOuter: number, rInner: number,
  startDeg: number, sweepDeg: number,
): string {
  const clamped = Math.max(-359.99, Math.min(359.99, sweepDeg));
  const endDeg = startDeg + clamped;
  const largeArc = Math.abs(clamped) >= 180 ? 1 : 0;
  const cw = clamped >= 0 ? 1 : 0;

  const p1 = polarPoint(cx, cy, rOuter, startDeg);
  const p2 = polarPoint(cx, cy, rOuter, endDeg);

  if (rInner <= 0) {
    return [
      `M ${cx} ${cy}`,
      `L ${p1.x} ${p1.y}`,
      `A ${rOuter} ${rOuter} 0 ${largeArc} ${cw} ${p2.x} ${p2.y}`,
      'Z',
    ].join(' ');
  }

  const p3 = polarPoint(cx, cy, rInner, endDeg);
  const p4 = polarPoint(cx, cy, rInner, startDeg);
  const ccw = cw ^ 1;

  return [
    `M ${p1.x} ${p1.y}`,
    `A ${rOuter} ${rOuter} 0 ${largeArc} ${cw}  ${p2.x} ${p2.y}`,
    `L ${p3.x} ${p3.y}`,
    `A ${rInner} ${rInner} 0 ${largeArc} ${ccw} ${p4.x} ${p4.y}`,
    'Z',
  ].join(' ');
}
