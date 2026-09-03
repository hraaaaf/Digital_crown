import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { resolveBridgeRoute, resolveDashboardTab } from '../features/mobile/bridge';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

const securitySource = readSource('src/features/admin/Security/MobileSecurity.tsx');
const onboardingSource = readSource('src/features/mobile/Onboarding/OnboardingScanner.tsx');
const dashboardSource = readSource('src/features/mobile/Dashboard/MobileDashboard.tsx');

describe('M6.4 contextual QR bridge', () => {
  it('maps only allowlisted destinations to explicit mobile routes', () => {
    expect(resolveBridgeRoute('agenda')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveBridgeRoute('finance')).toBe('/mobile/dashboard?tab=finance');
    expect(resolveBridgeRoute('lab')).toBe('/mobile/dashboard?tab=lab');
    expect(resolveBridgeRoute('assistant')).toBe('/mobile/dashboard?tab=bot');
    expect(resolveBridgeRoute('security')).toBe('/mobile/dashboard?tab=securite');
    expect(resolveBridgeRoute('dentists')).toBe('/mobile/dentists');
    expect(resolveBridgeRoute('superadmin')).toBe('/mobile/superadmin');
    expect(resolveBridgeRoute('https://evil.example')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveBridgeRoute('../super-admin')).toBe('/mobile/dashboard?tab=agenda');
  });

  it('hydrates dashboard tab from the router location and fails closed to agenda', () => {
    expect(resolveDashboardTab('?tab=finance')).toBe('finance');
    expect(resolveDashboardTab('?tab=bot')).toBe('bot');
    expect(resolveDashboardTab('?tab=securite')).toBe('securite');
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
    expect(resolveDashboardTab('?tab=superadmin')).toBe('agenda');
    expect(resolveDashboardTab('')).toBe('agenda');
    expect(dashboardSource).toContain('const location = useLocation()');
    expect(dashboardSource).toContain('resolveDashboardTab(location.search)');
    expect(dashboardSource).not.toContain('resolveDashboardTab(window.location.search)');
  });

  it('hands the platform control tower to its dedicated origin when configured', () => {
    expect(dashboardSource).toContain('const platformControlUrl = getPlatformControlUrl()');
    expect(dashboardSource).toContain('isExternalPlatformControlUrl(platformControlUrl)');
    expect(dashboardSource).toContain('href={platformControlUrl}');
    expect(dashboardSource).toContain('to="/mobile/superadmin"');
  });

  it('requires explicit target + destination before generating the desktop bridge', () => {
    expect(securitySource).toContain("api.get<BridgeOptions>('/mobile/bridge-options')");
    expect(securitySource).toContain("api.post<BridgePairing>('/mobile/bridge-pairing'");
    expect(securitySource).toContain('target_user_id: selectedTarget.id');
    expect(securitySource).toContain('destination: selectedDestination');
    expect(securitySource).toContain('aria-label="Utilisateur mobile cible"');
    expect(securitySource).toContain('aria-label="Destination mobile"');
    expect(securitySource).toContain('Générer le pont mobile');
    expect(securitySource).toContain('contains_patient_data !== false');
    expect(securitySource).not.toContain("api.get('/admin/zka-key-qr')");
  });

  it('resolves destination from the authenticated server after claim, never from a free query param', () => {
    expect(onboardingSource).toContain('/api/mobile/bridge-destination');
    expect(onboardingSource).toContain('Authorization: `Bearer ${accessToken}`');
    expect(onboardingSource).toContain('body: JSON.stringify({ credential })');
    expect(onboardingSource).toContain("window.history.replaceState({}, '', '/mobile/onboarding')");
    expect(onboardingSource).toContain('Ouverture :');
    expect(onboardingSource).not.toContain("navigate('/mobile/dashboard', { replace: true })");
  });

  it('fixes the measured onboarding touch and 390px form defects', () => {
    expect(onboardingSource).toContain('min-h-11 inline-flex items-center');
    expect(onboardingSource).toContain('min-w-0 flex-1 min-h-[52px]');
    expect(onboardingSource).toContain('shrink-0 min-h-[52px]');
    expect(onboardingSource).toContain('disabled={manualToken.length !== 6}');
    expect(securitySource).toContain('min-h-[52px]');
  });
});
