import { describe, expect, it } from 'vitest';

import {
  CERTIFICATE_TYPE_FREE,
  CERTIFICATE_TYPE_WORK_STOP,
  normalizeCertificateSelection,
  resolveCertificateReason,
  validateCertificateReason,
} from './CertificatePolicy';

describe('P3 certificate explicit selection policy', () => {
  it('preserves a new certificate as unselected instead of inventing a work stop', () => {
    expect(normalizeCertificateSelection('', '')).toEqual({ type: '', content: '' });
    expect(resolveCertificateReason('', '')).toBeNull();
    expect(validateCertificateReason('', '')).toBe('La nature du certificat est requise.');
  });

  it('keeps legacy work-stop labels mapped to the canonical type', () => {
    expect(normalizeCertificateSelection('Repos Post-Opératoire', '').type).toBe(CERTIFICATE_TYPE_WORK_STOP);
    expect(normalizeCertificateSelection('Repos médical', '').type).toBe(CERTIFICATE_TYPE_WORK_STOP);
  });

  it('migrates legacy Autre to a free certificate without inventing content', () => {
    const normalized = normalizeCertificateSelection('Autre', 'Texte historique');
    expect(normalized).toEqual({ type: CERTIFICATE_TYPE_FREE, content: 'Texte historique' });
  });

  it('preserves an unknown legacy reason as practitioner-authored free content', () => {
    const normalized = normalizeCertificateSelection('Contrôle postopératoire', '');
    expect(normalized).toEqual({
      type: CERTIFICATE_TYPE_FREE,
      content: 'Contrôle postopératoire',
    });
  });
});
