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

  it('keeps a fresh annex workstation locked until explicit enrollment (423 is not clinic setup)', () => {
    expect(app).toContain('const workstationBootstrap = await workstationModeService.getBootstrapState()');
    expect(app).toContain('if (workstationBootstrap.enrollmentRequired)');
    expect(app).toContain('setIsInitialized(null)');
    expect(app.indexOf('const workstationBootstrap = await workstationModeService.getBootstrapState()'))
      .toBeLessThan(app.indexOf('const status = await cabinetApi.checkInitStatus()'));
    expect(app).toContain("error.response?.status === 423");
    expect(app).toContain("error.response?.data?.detail === 'WORKSTATION_ENROLLMENT_REQUIRED'");
    expect(app).toContain("error.response?.data?.detail === 'WORKSTATION_IDENTITY_REQUIRED'");
    expect(app).not.toContain("error.response?.data?.detail === 'WORKSTATION_STATION_LOCKED'");
    expect(app).toContain('setWorkstationEnrollmentRequired(true)');
    expect(app).toContain('if (workstationEnrollmentRequired)');
    expect(app).toContain('return <Navigate to="/hub?enroll=1" replace />');
    expect(app).toContain('if (isInitialized === false && location.pathname !== \'/setup\')');
  });

  it('never labels an HTTP 423 workstation enrollment as a server outage', () => {
    expect(hub).toContain("response.status >= 400 && response.status < 500");
    expect(hub).toContain("setServerState('restricted')");
    expect(hub).toContain("setServerState('unavailable')");
    expect(hub).toContain("data-hub-server-state={serverState}");
    expect(hub).toContain("serverState === 'unavailable'");
    expect(hub.indexOf('response.status >= 400 && response.status < 500'))
      .toBeLessThan(hub.indexOf('if (!response.ok) throw new Error'));
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
    expect(controlCenter).toContain('bg-primary px-5 text-sm font-black text-on-primary');
    expect(controlCenter).toContain("border-primary bg-primary text-on-primary");
    expect(controlCenter).toContain('aria-describedby="cabinet-server-help"');
    expect(controlCenter).toContain('Détails techniques');
    expect(controlCenter).toContain('Continuer vers le Hub');
    expect(controlCenter).toContain('focus-visible:ring-offset-2');
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
