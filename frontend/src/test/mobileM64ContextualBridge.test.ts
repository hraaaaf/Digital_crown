import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { resolveBridgeRoute, resolveDashboardTab } from '../features/mobile/bridge';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

const securitySource = readSource('src/features/admin/Security/MobileSecurity.tsx');
const onboardingSource = readSource('src/features/mobile/Onboarding/OnboardingScanner.tsx');
const dashboardSource = readSource('src/features/mobile/Dashboard/MobileDashboard.tsx');

describe('Digital Crown Pocket general QR bridge', () => {
  it('preserves trusted canonical Pocket destinations and fails closed for unknown input', () => {
    expect(resolveBridgeRoute('agenda')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveBridgeRoute('finance')).toBe('/mobile/dashboard?tab=finance');
    expect(resolveBridgeRoute('lab')).toBe('/mobile/dashboard?tab=lab');
    expect(resolveBridgeRoute('assistant')).toBe('/mobile/dashboard?tab=bot');
    expect(resolveBridgeRoute('security')).toBe('/mobile/dashboard?tab=securite');
    expect(resolveBridgeRoute('dentists')).toBe('/mobile/dashboard?tab=dentists');
    expect(resolveBridgeRoute('stock')).toBe('/mobile/dashboard?tab=stock');
    expect(resolveBridgeRoute('library')).toBe('/mobile/dashboard?tab=library');
    expect(resolveBridgeRoute('marketplace')).toBe('/mobile/dashboard?tab=marketplace');
    expect(resolveBridgeRoute('superadmin')).toBe('/mobile/superadmin');
    expect(resolveBridgeRoute('https://evil.example')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveBridgeRoute('../super-admin')).toBe('/mobile/dashboard?tab=agenda');
  });

  it('allows canonical Pocket tabs from the router location and fails closed for unknown tabs', () => {
    expect(resolveDashboardTab('?tab=patients')).toBe('patients');
    expect(resolveDashboardTab('?tab=waiting-room')).toBe('waiting-room');
    expect(resolveDashboardTab('?tab=frontdesk')).toBe('frontdesk');
    expect(resolveDashboardTab('?tab=notifications')).toBe('notifications');
    expect(resolveDashboardTab('?tab=securite')).toBe('securite');
    expect(resolveDashboardTab('?tab=finance')).toBe('finance');
    expect(resolveDashboardTab('?tab=lab')).toBe('lab');
    expect(resolveDashboardTab('?tab=bot')).toBe('bot');
    expect(resolveDashboardTab('?tab=dentists')).toBe('dentists');
    expect(resolveDashboardTab('?tab=stock')).toBe('stock');
    expect(resolveDashboardTab('?tab=library')).toBe('library');
    expect(resolveDashboardTab('?tab=marketplace')).toBe('marketplace');
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
    expect(resolveDashboardTab('')).toBe('agenda');
    expect(dashboardSource).toContain("import { useLocation } from 'react-router-dom'");
    expect(dashboardSource).toContain('const location = useLocation()');
    expect(dashboardSource).toContain('resolveDashboardTab(location.search)');
    expect(dashboardSource).not.toContain('resolveDashboardTab(window.location.search)');
  });

  it('requires only an authorized user before generating the desktop Pocket bridge', () => {
    expect(securitySource).toContain("api.get<BridgeOptions>('/mobile/bridge-options')");
    expect(securitySource).toContain("api.post<BridgePairing>('/mobile/bridge-pairing'");
    expect(securitySource).toContain('target_user_id: selectedTarget.id');
    expect(securitySource).not.toContain('destination: selectedDestination');
    expect(securitySource).toContain('aria-label="Utilisateur mobile cible"');
    expect(securitySource).not.toContain('aria-label="Destination mobile"');
    expect(securitySource).toContain('Digital Crown Pocket');
    expect(securitySource).toContain('Générer le QR de connexion');
    expect(securitySource).toContain('contains_patient_data !== false');
    expect(securitySource).not.toContain("api.get('/admin/zka-key-qr')");
  });

  it('resolves the server-bound home after claim, never from a free query param', () => {
    expect(onboardingSource).toContain('/api/mobile/bridge-destination');
    expect(onboardingSource).toContain('Authorization: `Bearer ${accessToken}`');
    expect(onboardingSource).toContain('body: JSON.stringify({ credential })');
    expect(onboardingSource).toContain("window.history.replaceState({}, '', '/mobile/onboarding')");
    expect(onboardingSource).toContain('Ouverture :');
    expect(onboardingSource).not.toContain("navigate('/mobile/dashboard', { replace: true })");
  });

  it('keeps the measured onboarding touch and 390px form safeguards', () => {
    expect(onboardingSource).toContain('min-h-11 inline-flex items-center');
    expect(onboardingSource).toContain('min-w-0 flex-1 min-h-[52px]');
    expect(onboardingSource).toContain('shrink-0 min-h-[52px]');
    expect(onboardingSource).toContain('disabled={manualToken.length !== 6}');
    expect(securitySource).toContain('min-h-[52px]');
  });
});
