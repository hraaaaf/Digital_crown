import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const patientFlow = readFileSync(
  join(process.cwd(), 'src/features/mobile/Dashboard/components/MobileQuickPatientFlow.tsx'),
  'utf8',
);
const newPatientFlow = readFileSync(
  join(process.cwd(), 'src/features/mobile/Dashboard/components/MobileQuickNewPatientModal.tsx'),
  'utf8',
);
const capabilitiesHook = readFileSync(
  join(process.cwd(), 'src/features/mobile/Dashboard/hooks/useMobileQuickActionCapabilities.ts'),
  'utf8',
);

describe('MOB-3 quick patient flow contracts', () => {
  it('keeps clinical actions on the opaque Patient Cockpit bridge', () => {
    expect(patientFlow).toContain('/api/mobile/patient-cockpit/${patient.id}/context');
    expect(patientFlow).toContain('MobileStorage.saveBridgeContext');
    expect(patientFlow).toContain("sessionStorage.setItem('dc-mobile-quick-intent', action)");
    expect(patientFlow).toContain("window.location.assign('/mobile/context')");
    expect(patientFlow).not.toContain('/mobile/context?patient_id=');
  });

  it('reuses the canonical accounting payment endpoint and explicit payment method', () => {
    expect(patientFlow).toContain('/api/accounting/payments');
    expect(patientFlow).toContain('payment_method: paymentMethod');
    expect(patientFlow).toContain('patient_id: selectedPatient.id');
  });

  it('reuses canonical patient creation fields and endpoint', () => {
    expect(newPatientFlow).toContain('/api/patients/');
    expect(newPatientFlow).toContain('date_naissance: form.date_naissance');
    expect(newPatientFlow).toContain('sexe: form.sexe');
  });

  it('fails closed until encrypted server capabilities are returned', () => {
    expect(capabilitiesHook).toContain('/api/mobile/quick-actions/capabilities');
    expect(capabilitiesHook).toContain('const DENY_ALL');
    expect(capabilitiesHook).toContain('setCapabilities(DENY_ALL)');
    expect(capabilitiesHook).toContain('CryptoService.decryptPayload');
  });
});
