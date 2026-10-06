import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(path.join(process.cwd(), 'src', 'App.tsx'), 'utf8');
const header = readFileSync(path.join(process.cwd(), 'src', 'components', 'Header.tsx'), 'utf8');
const hub = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'HubPage.tsx'), 'utf8');
const workstation = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'WorkstationExperiencePage.tsx'), 'utf8');
const stationShell = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'StationKioskShell.tsx'), 'utf8');
const workstationAdmin = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'WorkstationModeAdminPanel.tsx'), 'utf8');
const controlCenter = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'ControlCenterTopologyPanel.tsx'), 'utf8');

describe('V1.5-00.2 Hub routing contract', () => {
  it('keeps workstation mode separate from legacy appMode', () => {
    expect(app).toContain('return <Navigate to="/hub" replace />');
    expect(app).toContain('path="/hub"');
    expect(app).toContain('path="/cabinet"');
    expect(app).toContain('path="/station"');
    expect(app).toContain('path="/control-center"');
    expect(app).toContain('<WorkstationModeGate target="protected"><ProtectedRoutes /></WorkstationModeGate>');
    expect(app).toContain('<WorkstationModeGate target="control-center">');
    expect(app).not.toContain("safeStorage.set('appMode', 'cabinet')");
    expect(app).not.toContain("safeStorage.set('appMode', 'station')");
  });

  it('uses only canonical theme tokens in V1.5 Hub surfaces', () => {
    const source = hub + workstation + stationShell + workstationAdmin + controlCenter;
    expect(source).not.toMatch(/(?:rounded|text|tracking|shadow|bg|border)-\[[^\]]+\]/);
    expect(source).not.toMatch(/(?:amber|red|rose|green|emerald|blue|indigo|violet|purple|slate)-\d+/);
    expect(source).not.toContain('shadow-2xl');
    expect(source).not.toContain('text-white');
    expect(source).toContain('rounded-elite-lg');
    expect(source).toContain('rounded-elite-sm');
    expect(source).toContain('shadow-elite');
    expect(source).toContain('shadow-elite-hover');
    expect(source).toContain('border-border-main');
    expect(source).toContain('text-text-muted');
    expect(source).toContain('bg-card-bg');
    expect(source).toContain('bg-primary/5');
  });

  it('keeps the Control Center actionable and fail-closed for LAN targets', () => {
    expect(workstation).toContain('<ControlCenterTopologyPanel />');
    expect(workstation).not.toContain('Espace technique en cours de construction');
    expect(controlCenter).toContain('data-control-center-target');
    expect(controlCenter).toContain('data-control-center-probe');
    expect(controlCenter).toContain('data-control-center-remediation');
    expect(controlCenter).toContain("credentials: 'omit'");
    expect(controlCenter).toContain('isCurrentAuthority');
    expect(controlCenter).toContain('getRuntimeAuthToken');
    expect(controlCenter).toContain('HTTPS est obligatoire pour une adresse LAN');
    expect(controlCenter).toContain('Utilisez uniquement une adresse locale du cabinet');
    expect(controlCenter).toContain('Aucune requête n’est envoyée à une origine distante');
    expect(controlCenter).toContain('Digital Crown utilise le port cabinet 8005');
    expect(controlCenter).not.toContain('localStorage.setItem');
    expect(controlCenter).not.toContain('sessionStorage.setItem');
    expect(controlCenter).toContain("void runProbe(API_BASE)");
    expect(controlCenter).not.toContain("}, [target])");
  });

  it('exposes a clean Cabinet return to Hub', () => {
    expect(header).toContain('to="/hub?select=1"');
    expect(header).toContain("Changer d'espace");
  });
});
