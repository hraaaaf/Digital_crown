import { describe, expect, it } from 'vitest';
import {
  isPresenceCertificate,
  normalizeCertificateDraft,
  resolveCertificateReason,
  validateCertificateReason,
} from './CertificatePolicy';

describe('CertificatePolicy P3 section 1', () => {
  it('exige un choix explicite pour un nouveau certificat', () => {
    expect(normalizeCertificateDraft(undefined)).toEqual({ certifType: '', certifCustomMotif: '' });
    expect(resolveCertificateReason('', '')).toBeNull();
    expect(validateCertificateReason('', '')).toMatch(/type de certificat.*requis/i);
  });

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
    expect(isPresenceCertificate('Certificat de Présence')).toBe(true);
  });

  it('réhydrate un motif historique inconnu comme personnalisé sans le réinterpréter', () => {
    expect(normalizeCertificateDraft('  Repos médical  ')).toEqual({
      certifType: 'Autre',
      certifCustomMotif: 'Repos médical',
    });
  });

  it('rejette un type technique inattendu au lieu de le sérialiser silencieusement', () => {
    expect(resolveCertificateReason('Repos médical', '')).toBeNull();
    expect(validateCertificateReason('Repos médical', '')).toMatch(/pas reconnu/i);
  });
});
