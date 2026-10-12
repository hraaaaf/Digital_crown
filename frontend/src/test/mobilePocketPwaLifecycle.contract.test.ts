import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { resolveDashboardTab } from '../features/mobile/bridge';

const source = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

describe('Pocket is a persistent standalone app, not a pairing deep-link', () => {
  it('launches installed Pocket on the real protected dashboard, preserving PWA identity', () => {
    const manifest = JSON.parse(source('public/manifest.json')) as {
      id: string; name: string; display: string; start_url: string; shortcuts: { url: string }[];
    };
    expect(manifest.name).toBe('Digital Crown Pocket');
    expect(manifest.id).toBe('/'); // existing installs must not split into a new PWA identity
    expect(manifest.display).toBe('standalone');
    expect(manifest.start_url).toBe('/mobile/dashboard');
    expect(manifest.shortcuts[0]?.url).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveDashboardTab('')).toBe('today');
    expect(resolveDashboardTab('?tab=agenda')).toBe('agenda');
  });

  it('boots onboarding inside the complete App Router so React can render Pocket after activation', () => {
    const main = source('src/main.tsx');
    const app = source('src/App.tsx');
    expect(main).not.toContain('return <BrowserRouter><OnboardingScanner /></BrowserRouter>');
    expect(main).toContain("const { default: App } = await import('./App.tsx')");
    expect(app).toContain('<BrowserRouter>');
    expect(app).toContain('path="/mobile/onboarding"');
    expect(app).toContain('path="/mobile/dashboard"');
    expect(app).toContain('<MobileProtectedRoute>');
    expect(app).toContain('<MobileBiometricGate>');
    expect(app).toContain("if (isMobile) {");
    expect(app).toContain('<Navigate to="/mobile/dashboard" replace />');
  });

  it('uses pairing only for enrollment, then starts Pocket Today with revocable device credentials', () => {
    const scanner = source('src/features/mobile/Onboarding/OnboardingScanner.tsx');
    const store = source('src/services/zka/MobileStorage.ts');
    expect(scanner).toContain("setDestinationRoute(pocketHome)");
    expect(scanner).toContain("const pocketHome = '/mobile/dashboard'");
    expect(scanner).toContain("setDestinationLabel('Digital Crown Pocket')");
    expect(scanner).toContain("await MobileStorage.saveCredentials");
    expect(scanner).toContain('href={destinationRoute}');
    expect(store).toContain('async isPaired(): Promise<boolean>');
    expect(store).toContain('async clearCredentials(): Promise<void>');
    expect(store).toContain("driver: localforage.INDEXEDDB");
    expect(store).toContain('refreshCredentialsInternal');
  });

  it('keeps the mobile shell with five tabs and guarded access to backend', () => {
    const dashboard = source('src/features/mobile/Dashboard/MobileDashboard.tsx');
    const nav = source('src/features/mobile/Dashboard/components/MobileBottomNav.tsx');
    expect(dashboard).toContain('<PocketTodayOverview');
    expect(dashboard).toContain('<MobileBottomNav');
    expect(dashboard).toContain('<PocketAgendaDay');
    for (const item of ['today', 'agenda', 'actions', 'patients', 'more']) {
      expect(nav).toContain(item);
    }
  });
});
