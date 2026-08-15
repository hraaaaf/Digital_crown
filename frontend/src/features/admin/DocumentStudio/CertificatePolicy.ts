export function resolveCertificateReason(certifType: string, customMotif: string): string | null {
  if (certifType !== 'Autre') return certifType.trim() || null;
  const reason = customMotif.trim();
  return reason || null;
}

export function validateCertificateReason(certifType: string, customMotif: string): string | null {
  if (certifType === 'Autre' && !customMotif.trim()) {
    return 'Le motif personnalisé est requis pour un certificat en modèle libre.';
  }
  if (!resolveCertificateReason(certifType, customMotif)) {
    return 'Le motif du certificat est requis.';
  }
  return null;
}
