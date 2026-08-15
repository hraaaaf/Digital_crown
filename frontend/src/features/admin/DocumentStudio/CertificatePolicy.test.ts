import { describe, expect, it } from 'vitest';
import {
  buildCertificatePayload,
  certificateRequiresDuration,
  normalizeCertificateSelection,
  resolveCertificateReason,
  validateCertificateReason,
} from './CertificatePolicy';

describe('CertificatePolicy P3 — types et contenu libre', () => {
  it('refuse un certificat médical libre sans contenu explicite', () => {
    expect(resolveCertificateReason('Certificat médical', '   ')).toBeNull();
    expect(validateCertificateReason('Certificat médical', '')).toMatch(/contenu.*requis/i);
  });

  it('conserve exactement le contenu libre saisi et le sépare du type', () => {
    const payload = buildCertificatePayload(
      'Certificat médical',
      '  Contrôle post-opératoire sans complication.  ',
      5,
      '2026-08-15',
    );
    expect(payload).toEqual({
      reason: 'Certificat médical',
      days: 0,
      start_date: '2026-08-15',
      content: 'Contrôle post-opératoire sans complication.',
    });
  });

  it('ne demande une durée que pour l’arrêt de travail', () => {
    expect(certificateRequiresDuration('Arrêt de travail')).toBe(true);
    expect(certificateRequiresDuration('Certificat de Présence')).toBe(false);
    expect(certificateRequiresDuration('Certificat médical')).toBe(false);
  });

  it('normalise les anciens repos sans perdre leur intention', () => {
    expect(normalizeCertificateSelection('Repos médical', '')).toEqual({
      type: 'Arrêt de travail',
      content: '',
    });
  });

  it('récupère un ancien motif libre comme contenu de certificat médical', () => {
    expect(normalizeCertificateSelection('Contrôle post-opératoire', '')).toEqual({
      type: 'Certificat médical',
      content: 'Contrôle post-opératoire',
    });
  });

  it('migre le legacy Autre vers le certificat médical libre', () => {
    expect(normalizeCertificateSelection('Autre', 'Texte libre')).toEqual({
      type: 'Certificat médical',
      content: 'Texte libre',
    });
  });
});
