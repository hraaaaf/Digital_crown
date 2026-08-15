export const CERTIFICATE_TYPES = ['Arrêt de travail', 'Certificat de Présence', 'Autre'] as const;
export type CertificateType = (typeof CERTIFICATE_TYPES)[number];

export interface CertificateDraft {
  certifType: CertificateType | '';
  certifCustomMotif: string;
}

export function isCertificateType(value: string): value is CertificateType {
  return (CERTIFICATE_TYPES as readonly string[]).includes(value);
}

export function isPresenceCertificate(certifType: string): boolean {
  return certifType === 'Certificat de Présence';
}

export function normalizeCertificateDraft(reason: string | null | undefined): CertificateDraft {
  const normalized = (reason || '').trim();
  if (!normalized) return { certifType: '', certifCustomMotif: '' };
  if (normalized === 'Arrêt de travail' || normalized === 'Certificat de Présence') {
    return { certifType: normalized, certifCustomMotif: '' };
  }
  if (normalized === 'Autre') {
    return { certifType: 'Autre', certifCustomMotif: '' };
  }
  // Legacy/custom archived reasons are preserved verbatim instead of being
  // reinterpreted as a different practitioner-controlled certificate type.
  return { certifType: 'Autre', certifCustomMotif: normalized };
}

export function resolveCertificateReason(certifType: string, customMotif: string): string | null {
  if (!isCertificateType(certifType)) return null;
  if (certifType !== 'Autre') return certifType;
  const reason = customMotif.trim();
  return reason || null;
}

export function validateCertificateReason(certifType: string, customMotif: string): string | null {
  if (!certifType.trim()) {
    return 'Le type de certificat est requis.';
  }
  if (!isCertificateType(certifType)) {
    return 'Le type de certificat n’est pas reconnu.';
  }
  if (certifType === 'Autre' && !customMotif.trim()) {
    return 'Le motif personnalisé est requis pour un certificat en modèle libre.';
  }
  return null;
}
