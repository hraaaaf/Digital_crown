/**
 * Recognition of a manual three-landmark selection.
 * Presentation-only: this module never computes or classifies clinical measurements.
 * Values and interpretations must come from the canonical cephalometric engine.
 */
export type RecognizedCephaloAngle = {
  measurementId: 'M_ANB_DEG_V1' | 'M_SNA_DEG_V1' | 'M_SNB_DEG_V1';
  label: 'ANB' | 'SNA' | 'SNB';
  points: readonly [string, string, string];
};

const ANGLES: readonly RecognizedCephaloAngle[] = [
  { measurementId: 'M_ANB_DEG_V1', label: 'ANB', points: ['A', 'N', 'B'] },
  { measurementId: 'M_SNA_DEG_V1', label: 'SNA', points: ['S', 'N', 'A'] },
  { measurementId: 'M_SNB_DEG_V1', label: 'SNB', points: ['S', 'N', 'B'] },
];

const normalize = (point: string): string => point.trim().toUpperCase();

/** Vertex must be the second selected point; endpoints may be selected in either order. */
export function recognizeCephaloAngle(points: readonly string[]): RecognizedCephaloAngle | null {
  if (points.length !== 3 || points.some(point => typeof point !== 'string' || !point.trim())) return null;
  const [first, vertex, last] = points.map(normalize);
  if (new Set([first, vertex, last]).size !== 3) return null;
  return ANGLES.find(angle => {
    const [a, v, b] = angle.points.map(normalize);
    return vertex === v && ((first === a && last === b) || (first === b && last === a));
  }) ?? null;
}

/** No reference range or clinical classification is inferred from geometry alone. */
export function describeRecognizedAngle(
  recognized: RecognizedCephaloAngle,
  canonicalValue: number | null | undefined,
  canonicalInterpretation?: string | null,
): { title: string; valueLabel: string; reading: string } {
  const available = typeof canonicalValue === 'number' && Number.isFinite(canonicalValue);
  return {
    title: recognized.label,
    valueLabel: available ? `${canonicalValue.toFixed(1)}°` : 'Non calculable',
    reading: available
      ? canonicalInterpretation?.trim() || 'Mesure disponible ; interprétation clinique à confirmer selon le contexte du patient.'
      : 'La mesure canonique n’est pas disponible. Vérifier les repères et le protocole avant toute interprétation.',
  };
}
