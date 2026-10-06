import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(resolve(process.cwd(), 'src/features/patient-companion/PatientCompanionApp.tsx'), 'utf8');
const kiosk = readFileSync(resolve(process.cwd(), 'src/features/hub/StationPatientIdentity.tsx'), 'utf8');
const arrival = readFileSync(resolve(process.cwd(), 'src/features/hub/StationAppointmentArrival.tsx'), 'utf8');
const backend = readFileSync(resolve(process.cwd(), '../backend/routers/station_patient_session.py'), 'utf8');
const bridge = readFileSync(resolve(process.cwd(), '../backend/services/station_arrival_bridge.py'), 'utf8');

describe('V1.5-03.3 / 03.4 station patient session contract', () => {
  it('consumes stationSession only through an authenticated Patient Companion access', () => {
    expect(app).toContain("params.get('stationSession')");
    expect(app).toContain('/api/workstation/patient-session/claim');
    expect(app).toContain('Authorization:');
    expect(app).toContain('pairing.accessToken');
    expect(app).toContain('pairing.context.access_id');
  });

  it('keeps arrival downstream of secure identification and excludes Queue Core behavior', () => {
    expect(kiosk).toContain('StationAppointmentArrival');
    expect(kiosk).not.toContain('ticket_number');
    expect(arrival).toContain('Confirmer mon arrivée');
    expect(arrival).toContain('Aucun numéro de file ni ordre de passage');
    expect(backend).toContain('/appointments/{appointment_id}/arrive');
    expect(bridge).toContain('AppointmentStatus.EN_SALLE_ATTENTE');
    expect(bridge).not.toContain('ticket_number');
    expect(bridge).not.toContain('priority');
  });

  it('purges patient references on expiry or explicit station cleanup', () => {
    expect(backend).toContain('patient_access_id = None');
    expect(backend).toContain('patient_id = None');
    expect(backend).toContain('purged_at');
    expect(backend).toContain('STATION_SESSION_ALREADY_USED');
  });
});
