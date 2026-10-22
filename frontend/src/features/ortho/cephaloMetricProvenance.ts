/** R23-J — presentation-only truth of automatic cephalometric measurements.
 *
 * A numerical result is not proof of human review, anatomical correctness,
 * a clinical norm, or a diagnosis. Never promote unverifiable legacy metadata
 * (even if it contains ad-hoc validated_by / approved strings) to clinical GO.
 */
export type CephaloMetricOrigin = 'AUTOMATIC_SRPOSE38_UNREVIEWED' | 'ORIGIN_NOT_ATTESTED';

export interface CephaloMetricProvenance {
  origin: CephaloMetricOrigin;
  methodLabel: string;
  reviewLabel: string;
  studyLabel: string;
  clinicianValidated: false;
  classificationAuthorized: false;
}

export function deriveCephaloMetricProvenance(
  anglesData: Record<string, unknown> | null | undefined,
  analysisId: number | undefined,
): CephaloMetricProvenance {
  const metadata = anglesData?.vision_metadata;
  const record = metadata !== null && typeof metadata === 'object' && !Array.isArray(metadata)
    ? metadata as Record<string, unknown>
    : {};
  // Only this known backend inference-mode ID has an evidenced meaning here.
  // Unknown/free-form strings must never be displayed as trusted model identity.
  const isOnnx38 = record.mode_inference === 'SOTA_ONNX_38';
  const origin: CephaloMetricOrigin = isOnnx38
    ? 'AUTOMATIC_SRPOSE38_UNREVIEWED' : 'ORIGIN_NOT_ATTESTED';
  return {
    origin,
    methodLabel: isOnnx38
      ? 'Points automatiques · SRPose38 (origine déclarée par l’étude)'
      : 'Origine des repères non attestée',
    reviewLabel: 'Revue par un praticien non attestée · valeurs non validées cliniquement',
    studyLabel: Number.isSafeInteger(analysisId) && Number(analysisId) > 0
      ? `Étude #${analysisId}` : 'Étude non identifiée',
    clinicianValidated: false,
    classificationAuthorized: false,
  };
}

/** Distinguish computability from clinical approval. */
export function rawCephaloMetricStatus(hasFiniteValue: boolean): string {
  return hasFiniteValue ? 'Mesure brute · non validée cliniquement' : 'Non calculable';
}
