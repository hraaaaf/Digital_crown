import { readFileSync } from 'node:fs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./patient-companion/firebasePatientAuth', () => ({
  getVerifiedPatientIdToken: vi.fn().mockResolvedValue('patient-id-token'),
  signOutPatient: vi.fn().mockResolvedValue(undefined),
}));

import { getPatientContexts } from './patient-companion/patientCompanionApi';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('Patient Companion D1 transport isolation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sends only Firebase auth and explicitly omits cabinet cookies', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(
      JSON.stringify({ contexts: [] }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    ));

    await getPatientContexts();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get('Authorization')).toBe('Firebase patient-id-token');
    expect(headers.get('Authorization')).not.toMatch(/^Bearer /);
    expect(init?.credentials).toBe('omit');
    expect(init?.cache).toBe('no-store');
  });

  it('does not import or reuse the shared cabinet Axios client', () => {
    const source = read('./patient-companion/patientCompanionApi.ts');
    expect(source).toContain("import { resolveApiBase } from '../services/apiBase'");
    expect(source).not.toContain("from '../services/api'");
    expect(source).not.toContain("localStorage.getItem('token')");
    expect(source).toContain("headers.set('Authorization', `Firebase ${token}`)");
    expect(source).toContain("credentials: 'omit'");
  });

  it('fails closed if the backend rejects the Firebase patient session', () => {
    const source = read('./patient-companion/patientCompanionApi.ts');
    expect(source).toContain('if (response.status === 401)');
    expect(source).toContain('await signOutPatient()');
    expect(source).toContain("window.location.replace('/patient-companion')");
  });

  it('forces a fresh Firebase token after verified-email reload', () => {
    const source = read('./patient-companion/firebasePatientAuth.ts');
    expect(source).toContain('await reload(user)');
    expect(source).toContain('user.getIdToken(true)');
    expect(source).toContain('browserSessionPersistence');
    expect(source).not.toContain('browserLocalPersistence');
  });

  it('keeps the invitation QR token memory-only and strips it from the URL before render', () => {
    const source = read('./patient-companion/PatientCompanionEntry.tsx');
    expect(source).toContain("new URLSearchParams(window.location.search).get('token')");
    expect(source).toContain("window.history.replaceState({}, '', window.location.pathname)");
    expect(source).not.toContain('localStorage');
    expect(source).not.toContain('sessionStorage');
  });

  it('pins the dedicated Firebase Web Auth dependency exactly', () => {
    const pkg = JSON.parse(read('../package.json')) as { dependencies?: Record<string, string> };
    expect(pkg.dependencies?.firebase).toBe('12.19.0');
  });

  it('boots Patient Companion before the staff App and excludes patient pages from staff telemetry/offline bootstrap', () => {
    const source = read('./main.tsx');
    expect(source).toContain("previewPath.startsWith('/patient-companion')");
    expect(source).toContain('!isPreviewRequest && !isPatientCompanionRequest && frontendTelemetryEnabled');
    expect(source).toContain('isFrontendCloudTelemetryEnabled');
    expect(source).toContain("!isPatientCompanionRequest && 'serviceWorker' in navigator");
    expect(source.indexOf('if (isPatientCompanionRequest)')).toBeLessThan(source.indexOf("const { default: App } = await import('./App.tsx')"));
  });
});
