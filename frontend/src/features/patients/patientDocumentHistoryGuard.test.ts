import { describe, expect, it } from 'vitest';
import { isSamePatientDocumentTabNavigation } from './patientDocumentHistoryGuard';

describe('isSamePatientDocumentTabNavigation', () => {
  const current = 'http://localhost/patients/42?tab=admin';

  it('detects a documentTab change for the current patient', () => {
    expect(isSamePatientDocumentTabNavigation(current, '?tab=admin&documentTab=devis', '42')).toBe(true);
  });

  it('ignores unrelated search-param changes', () => {
    expect(isSamePatientDocumentTabNavigation(current, '?tab=documents', '42')).toBe(false);
  });

  it('does not intercept navigation to another patient or another route', () => {
    expect(isSamePatientDocumentTabNavigation(current, '/patients/43?documentTab=devis', '42')).toBe(false);
    expect(isSamePatientDocumentTabNavigation(current, '/dashboard?documentTab=devis', '42')).toBe(false);
  });
});
