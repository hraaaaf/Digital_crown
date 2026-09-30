import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(__dirname, '..');
const gate = fs.readFileSync(path.join(root, 'features/hub/WorkstationModeGate.tsx'), 'utf8');
const service = fs.readFileSync(path.join(root, 'services/workstationMode.ts'), 'utf8');
const app = fs.readFileSync(path.join(root, 'App.tsx'), 'utf8');

describe('V1.5-00.3 workstation mode trust contract', () => {
  it('keeps server state authoritative over convenience localStorage', () => {
    expect(service).toContain("api.get<WorkstationBootstrapState>('/workstation/bootstrap')");
    expect(service).toContain("api.get<WorkstationState>('/workstation/state')");
    expect(service).toContain('Convenience cache only. Server state remains authoritative.');
    expect(service).not.toContain("localStorage.getItem(CONVENIENCE_KEY)");
  });

  it('keeps Station fail-closed and ignores Hub selection as an escape authority', () => {
    expect(gate).toContain("state.defaultExperience === 'station' && !state.stationEscapeAuthorized");
    expect(gate).toContain('return <Navigate to="/station" replace />');
    expect(gate).toContain("target === 'station'");
  });

  it('places Hub and Station behind the workstation gate without touching legacy appMode', () => {
    expect(app).toContain('<WorkstationModeGate target="hub">');
    expect(app).toContain('<WorkstationModeGate target="station">');
    expect(gate).not.toContain('appMode');
    expect(service).not.toContain('appMode');
  });
});
