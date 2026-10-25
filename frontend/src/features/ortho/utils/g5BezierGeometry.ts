/**
 * ODF G5 LAB: deterministic, source-pixel cubic Bézier geometry only.
 *
 * NOT an anatomy detector or a source of clinical authority.
 * The backend V1 writes sampled polylines (max 600 points per structure).
 * Never show an unsampled Bézier in the editor as though it will print
 * identically in the approved PDF. UI/approval integration is a later gate.
 */
export type G5PixelPoint = readonly [number, number];

export type G5CubicSegment = Readonly<{
  start: G5PixelPoint;
  control1: G5PixelPoint;
  control2: G5PixelPoint;
  end: G5PixelPoint;
}>;

export type G5BezierSamplingOptions = Readonly<{
  imageWidth: number;
  imageHeight: number;
  maxStepPixels?: number;
  maxPoints?: number;
}>;

export const G5_MAX_CONTOUR_POINTS = 600;

function distance(a: G5PixelPoint, b: G5PixelPoint): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

function pointInsideSource(point: G5PixelPoint, width: number, height: number): boolean {
  return Array.isArray(point) && point.length === 2 &&
    point.every(Number.isFinite) &&
    point[0] >= 0 && point[0] < width &&
    point[1] >= 0 && point[1] < height;
}

export function g5CubicAt(segment: G5CubicSegment, t: number): G5PixelPoint {
  if (!Number.isFinite(t) || t < 0 || t > 1) {
    throw new Error('G5_BEZIER_INVALID_PARAMETER');
  }
  const q = 1 - t;
  const w0 = q * q * q;
  const w1 = 3 * q * q * t;
  const w2 = 3 * q * t * t;
  const w3 = t * t * t;
  return [
    w0 * segment.start[0] + w1 * segment.control1[0] +
      w2 * segment.control2[0] + w3 * segment.end[0],
    w0 * segment.start[1] + w1 * segment.control1[1] +
      w2 * segment.control2[1] + w3 * segment.end[1],
  ];
}

function tenth(v: number): number {
  return Math.round(v * 10) / 10;
}

/**
 * Convert explicitly placed cubic control points to V1-compatible ordered
 * pixel samples. No inferred contour, no synthetic landmark projection.
 *
 * Reject rather than silently truncate: geometry is the evidence the dentist
 * must see, approve and receive on both PDF views.
 */
export function g5SampleBezierContour(
  segments: readonly G5CubicSegment[],
  options: G5BezierSamplingOptions,
): G5PixelPoint[] {
  const {imageWidth, imageHeight} = options;
  const maxStep = options.maxStepPixels ?? 6;
  const maxPoints = options.maxPoints ?? G5_MAX_CONTOUR_POINTS;
  if (!Number.isSafeInteger(imageWidth) || !Number.isSafeInteger(imageHeight) ||
      imageWidth < 1 || imageHeight < 1 || imageWidth > 10000 ||
      imageHeight > 10000 || !Number.isFinite(maxStep) || maxStep < 1 ||
      maxStep > 32 || !Number.isSafeInteger(maxPoints) ||
      maxPoints < 2 || maxPoints > G5_MAX_CONTOUR_POINTS ||
      !Array.isArray(segments) || !segments.length || segments.length > 150) {
    throw new Error('G5_BEZIER_INVALID_SAMPLING_CONTRACT');
  }
  const output: G5PixelPoint[] = [];
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    if (!seg || ![seg.start, seg.control1, seg.control2, seg.end]
      .every(point => pointInsideSource(point, imageWidth, imageHeight))) {
      throw new Error('G5_BEZIER_OUTSIDE_SOURCE_IMAGE');
    }
    if (distance(seg.start, seg.end) < 0.5) {
      throw new Error('G5_BEZIER_DEGENERATE_SEGMENT');
    }
    if (i > 0 && distance(segments[i - 1].end, seg.start) > 0.01) {
      throw new Error('G5_BEZIER_DISCONTINUOUS_CONTOUR');
    }
    const controlLength = distance(seg.start, seg.control1) +
      distance(seg.control1, seg.control2) + distance(seg.control2, seg.end);
    const steps = Math.max(2, Math.ceil(controlLength / maxStep));
    for (let k = i === 0 ? 0 : 1; k <= steps; k++) {
      const p = g5CubicAt(seg, k / steps);
      const q: G5PixelPoint = [tenth(p[0]), tenth(p[1])];
      const last = output[output.length - 1];
      // V1 normalization refuses successive samples closer than 0.5 px.
      if (last && distance(last, q) < 0.5) continue;
      output.push(q);
      if (output.length > maxPoints) {
        throw new Error('G5_BEZIER_TOO_MANY_SAMPLES');
      }
    }
  }
  if (output.length < 2) throw new Error('G5_BEZIER_INSUFFICIENT_SAMPLES');
  return output;
}
