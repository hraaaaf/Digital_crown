import { describe, expect, it } from 'vitest';
import { resolveCertificateReason, validateCertificateReason } from './CertificatePolicy';

describe('CertificatePolicy P3-B', () => {
  it('refuse un modèle libre sans motif explicite', () => {
    expect(resolveCertificateReason('Autre', '   ')).toBeNull();
    expect(validateCertificateReason('Autre', '')).toMatch(/motif personnalisé.*requis/i);
  });

  it('conserve exactement le motif libre saisi sans fallback clinique', () => {
    expect(resolveCertificateReason('Autre', '  Contrôle post-opératoire  ')).toBe('Contrôle post-opératoire');
    expect(validateCertificateReason('Autre', 'Contrôle post-opératoire')).toBeNull();
  });

  it('conserve les types de certificat explicites', () => {
    expect(resolveCertificateReason('Certificat de Présence', '')).toBe('Certificat de Présence');
    expect(validateCertificateReason('Certificat de Présence', '')).toBeNull();
  });
});
