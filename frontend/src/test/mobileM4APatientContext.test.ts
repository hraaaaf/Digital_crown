import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

const appSource = readSource('src/App.tsx');
const patientSource = readSource('src/features/patients/PatientDetailsInner.tsx');
const onboardingSource = readSource('src/features/mobile/Onboarding/OnboardingScanner.tsx');
const storageSource = readSource('src/services/zka/MobileStorage.ts');
const contextSource = readSource('src/features/mobile/Context/MobileContext.tsx');
const bridgeSource = readSource('src/features/patients/components/PatientMobileBridge.tsx');

describe('M4-A patient contextual mobile bridge', () => {
  it('keeps the mobile resource route idless and behind the existing pairing gate', () => {
    const contextStart = appSource.indexOf('path="/mobile/context"');
    const nextMobileRoute = appSource.indexOf('path="/mobile/dentists"', contextStart);
    const contextRouteSource = appSource.slice(contextStart, nextMobileRoute);
    expect(contextStart).toBeGreaterThanOrEqual(0);
    expect(nextMobileRoute).toBeGreaterThan(contextStart);
    expect(contextRouteSource).toContain('<MobileProtectedRoute>');
    expect(contextRouteSource).toContain('<MobileContext />');
    expect(contextRouteSource).toContain('</MobileProtectedRoute>');
    expect(appSource).not.toMatch(/\/mobile\/context\/:/);
  });

  it('adds the bridge to the patient header without replacing the existing actions', () => {
    expect(patientSource).toContain("import { PatientMobileBridge } from './components/PatientMobileBridge'");
    expect(patientSource).toContain('<PatientMobileBridge patientId={patient.id} patientName={fullName} />');
    expect(patientSource).toContain('label="RDV"');
    expect(patientSource).toContain('label="Document"');
  });

  it('resolves resource context first and preserves the M6.4 destination resolver as fallback', () => {
    expect(onboardingSource).toContain('/api/mobile/resource-bridge-destination');
    expect(onboardingSource).toContain('/api/mobile/bridge-destination');
    expect(onboardingSource.indexOf('/api/mobile/resource-bridge-destination')).toBeLessThan(onboardingSource.indexOf('/api/mobile/bridge-destination'));
    expect(onboardingSource).toContain('MobileStorage.saveBridgeContext(destination.context)');
    expect(onboardingSource).toContain("route: BRIDGE_ROUTES.context");
    expect(onboardingSource).toContain("window.history.replaceState({}, '', '/mobile/onboarding')");
  });

  it('stores context in IndexedDB scope and clears it with the mobile session', () => {
    expect(storageSource).toContain('export interface MobileBridgeContext');
    expect(storageSource).toContain('saveBridgeContext');
    expect(storageSource).toContain('getBridgeContext');
    expect(storageSource).toContain('clearBridgeContext');
    expect(storageSource).toContain('async function clearSessionData()');
    expect(storageSource).toContain('mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID)');
    expect(storageSource).toContain('mobileStore().setItem(STORE_BRIDGE_CONTEXT_ID');
    expect(storageSource).not.toContain("localStorage.setItem('dc_mobile_bridge_context'");
  });

  it('loads the patient only from the server-held context key', () => {
    expect(contextSource).toContain("request('resource-context', creds.access_token)");
    expect(contextSource).toContain("/api/mobile/${path}");
    expect(contextSource).toContain('context_key: stored.key');
    expect(contextSource).not.toContain('/patients/${');
    expect(contextSource).toContain('has_medical_alert');
  });

  it('never sends patient PHI in the bridge request body and fails closed on unsafe server metadata', () => {
    expect(bridgeSource).toContain("resource_type: 'patient'");
    expect(bridgeSource).toContain('resource_id: patientId');
    expect(bridgeSource.match(/contains_patient_data !== false/g)?.length ?? 0).toBeGreaterThanOrEqual(2);
    expect(bridgeSource).not.toContain('patientName,');
    expect(bridgeSource).not.toContain('telephone:');
  });
});
