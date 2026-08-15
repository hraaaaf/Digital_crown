import { describe, expect, it } from 'vitest';
import {
  derivePrescriptionSafetyViewState,
  prescriptionSafetyFingerprint,
} from './PrescriptionSafetyState';

describe('PrescriptionSafetyState', () => {
  it('never presents an unchecked prescription as verified', () => {
    expect(derivePrescriptionSafetyViewState('unchecked', [])).toEqual({
      label: 'Sécurité non vérifiée',
      tone: 'neutral',
      verified: false,
    });
  });

  it('distinguishes checking, error, clean verification and verified warnings', () => {
    expect(derivePrescriptionSafetyViewState('checking', []).verified).toBe(false);
    expect(derivePrescriptionSafetyViewState('error', []).verified).toBe(false);
    expect(derivePrescriptionSafetyViewState('verified', [])).toEqual({
      label: 'Sécurité vérifiée',
      tone: 'success',
      verified: true,
    });
    expect(derivePrescriptionSafetyViewState('verified', [{ message: 'Interaction' }])).toEqual({
      label: '1 alerte',
      tone: 'warning',
      verified: true,
    });
  });

  it('creates a deterministic fingerprint from patient and normalized drug names', () => {
    expect(prescriptionSafetyFingerprint('42', [' ibuprofene ', 'Amoxicilline'])).toBe(
      '42::AMOXICILLINE|IBUPROFENE',
    );
    expect(prescriptionSafetyFingerprint('42', ['AMOXICILLINE', 'IBUPROFENE'])).toBe(
      '42::AMOXICILLINE|IBUPROFENE',
    );
  });

  it('changes fingerprint when the prescription safety inputs change', () => {
    const before = prescriptionSafetyFingerprint('42', ['AMOXICILLINE']);
    const afterDrugChange = prescriptionSafetyFingerprint('42', ['IBUPROFENE']);
    const afterPatientChange = prescriptionSafetyFingerprint('43', ['AMOXICILLINE']);

    expect(afterDrugChange).not.toBe(before);
    expect(afterPatientChange).not.toBe(before);
  });
});
