import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(resolve(process.cwd(), 'src/features/patient-companion/PatientCompanionApp.tsx'), 'utf8');
const kiosk = readFileSync(resolve(process.cwd(), 'src/features/hub/StationPatientIdentity.tsx'), 'utf8');
const backend = readFileSync(resolve(process.cwd(), '../backend/routers/station_patient_session.py'), 'utf8');

describe('V1.5-03.3 station patient session contract', () => {
  it('consumes stationSession only through an authenticated Patient Companion access', () => {
    expect(app).toContain("params.get('stationSession')");
    expect(app).toContain('/api/workstation/patient-session/claim');
    expect(app).toContain('Authorization:');
    expect(app).toContain('pairing.accessToken');
    expect(app).toContain('pairing.context.access_id');
  });

  it('keeps Station QR/NFC identification separate from arrival and queue logic', () => {
    expect(kiosk).toContain('Aucune arrivée n’a encore été enregistrée.');
    expect(kiosk).not.toContain('ARRIVED');
    expect(backend).not.toContain('AppointmentStatus');
    expect(backend).not.toContain('queue');
  });

  it('purges patient references on expiry or explicit station cleanup', () => {
    expect(backend).toContain('patient_access_id = None');
    expect(backend).toContain('patient_id = None');
    expect(backend).toContain('purged_at');
    expect(backend).toContain('STATION_SESSION_ALREADY_USED');
  });
});
