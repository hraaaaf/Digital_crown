import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const panel = readFileSync(resolve(process.cwd(), 'src/features/patients/components/PatientCompanionPanel.tsx'), 'utf8');
const details = readFileSync(resolve(process.cwd(), 'src/features/patients/PatientDetailsInner.tsx'), 'utf8');

describe('Patient Companion D2 staff surface', () => {
  it('reuses D0 staff contracts and keeps invitation secrets memory-only', () => {
    expect(panel).toContain('/patient-companion/admin/patients/${patientId}/status');
    expect(panel).toContain('/patient-companion/admin/patients/${patientId}/invitation');
    expect(panel).toContain('/patient-companion/admin/patients/${patientId}/shares');
    expect(panel).toContain('/patient-companion/admin/accesses/${access.access_id}/revoke');
    expect(panel).toContain('qr_data_url');
    expect(panel).not.toContain('localStorage');
    expect(panel).not.toContain('sessionStorage');
    expect(panel).toContain("recipient_type: 'email'");
    expect(panel).toContain('setEphemeralInvitation(null)');
  });

  it('refreshes durable status after multi-access revocation, including partial failures', () => {
    expect(panel).toContain('Promise.allSettled');
    expect(panel).toContain("result.status === 'rejected'");
    expect(panel).toContain('Révocation partielle : état actualisé');
    expect(panel).toContain('await load();');
  });

  it('is exposed only to the principal owner/admin inside PatientDetails', () => {
    expect(details).toContain("| 'companion'");
    expect(details).toContain('ownerOrAdmin && <TabButton');
    expect(details).toContain("activeTab === 'companion'");
    expect(details).toContain('<PatientCompanionPanel patientId={Number(id)} patientEmail={patient.email} />');
    expect(details).toContain("if (!ownerOrAdmin && activeTab === 'companion')");
  });

  it('keeps the 390px Companion shell compact without changing D0 contracts', () => {
    expect(details).toContain("if (!id || activeTab === 'companion') return;");
    expect(details).toContain("'hidden sm:grid gap-2 w-full xl:w-auto'");
    expect(details).toContain('mobileLabel="Suivi"');
    expect(panel).toContain('grid grid-cols-3 gap-2');
    expect(panel).toContain('hidden sm:block mt-1 text-sm');
    expect(panel).toContain('w-40 h-40 sm:w-48 sm:h-48');
  });
});
