export const CERTIFICATE_TYPE_WORK_STOP = 'Arrêt de travail' as const;
export const CERTIFICATE_TYPE_PRESENCE = 'Certificat de Présence' as const;
export const CERTIFICATE_TYPE_FREE = 'Certificat médical' as const;

export const CERTIFICATE_TYPES = [
  CERTIFICATE_TYPE_WORK_STOP,
  CERTIFICATE_TYPE_PRESENCE,
  CERTIFICATE_TYPE_FREE,
] as const;

export type CertificateType = (typeof CERTIFICATE_TYPES)[number];

const LEGACY_WORK_STOP_TYPES = new Set([
  'Repos médical',
  'Certificat de Repos',
  'Repos Post-Opératoire',
  "Suite d'Intervention",
]);

export interface NormalizedCertificateSelection {
  type: CertificateType | '';
  content: string;
}

export function normalizeCertificateSelection(
  certifType: string,
  customContent: string,
): NormalizedCertificateSelection {
  const rawType = (certifType || '').trim();
  const rawContent = customContent || '';

  if (rawType === CERTIFICATE_TYPE_WORK_STOP || LEGACY_WORK_STOP_TYPES.has(rawType)) {
    return { type: CERTIFICATE_TYPE_WORK_STOP, content: rawContent };
  }

  if (rawType === CERTIFICATE_TYPE_PRESENCE) {
    return { type: CERTIFICATE_TYPE_PRESENCE, content: rawContent };
  }

  if (rawType === CERTIFICATE_TYPE_FREE || rawType === 'Autre') {
    return { type: CERTIFICATE_TYPE_FREE, content: rawContent };
  }

  if (rawType) {
    return {
      type: CERTIFICATE_TYPE_FREE,
      content: rawContent.trim() ? rawContent : rawType,
    };
  }

  // Un nouvel écran n'invente jamais une nature de certificat.
  return { type: '', content: rawContent };
}

export function certificateRequiresDuration(certifType: string): boolean {
  return normalizeCertificateSelection(certifType, '').type === CERTIFICATE_TYPE_WORK_STOP;
}

export function resolveCertificateReason(certifType: string, customContent: string): string | null {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  if (!normalized.type) return null;
  if (normalized.type === CERTIFICATE_TYPE_FREE && !normalized.content.trim()) return null;
  return normalized.type;
}

export function validateCertificateReason(certifType: string, customContent: string): string | null {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  if (!normalized.type) {
    return 'La nature du certificat est requise.';
  }
  if (normalized.type === CERTIFICATE_TYPE_FREE && !normalized.content.trim()) {
    return 'Le contenu du certificat médical est requis.';
  }
  return null;
}

export function buildCertificatePayload(
  certifType: string,
  customContent: string,
  certifDays: number,
  docDate: string,
  startDate: string,
) {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  const requiresDuration = certificateRequiresDuration(normalized.type);
  return {
    reason: normalized.type,
    days: requiresDuration ? Number(certifDays) : 0,
    doc_date: docDate,
    ...(requiresDuration ? { start_date: startDate || docDate } : {}),
    ...(normalized.type === CERTIFICATE_TYPE_FREE
      ? { content: normalized.content.trim() }
      : {}),
  };
}