import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const hookSource = readSource('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
const dashboardSource = readSource('src/features/mobile/Dashboard/MobileDashboard.tsx');
const storageSource = readSource('src/services/zka/MobileStorage.ts');
const apiSource = readSource('src/services/api.ts');

describe('Digital Crown Pocket production runtime scope', () => {
  it('keeps Today out of the legacy full agenda manager', () => {
    expect(dashboardSource).not.toContain("import { AgendaView }");
    expect(dashboardSource).toContain('PocketTodayOverview');
  });

  it('restores the merged Pocket surfaces in the real MobileDashboard', () => {
    for (const surface of ['FinanceView', 'LabView', 'BotView', 'DentistsView', 'StockView', 'LibraryView', 'MarketplaceView']) {
      expect(dashboardSource).toContain(surface);
    }
    expect(hookSource).toContain('fetchLabJobs');
    expect(hookSource).toContain('/api/mobile/accounting/export-pdf');
  });

  it('keeps Pocket credentials out of desktop browser storage', () => {
    expect(storageSource).not.toContain("localStorage.setItem('token'");
    expect(hookSource).not.toContain("localStorage.setItem('token'");
    const requestBlock = apiSource.slice(apiSource.indexOf('api.interceptors.request.use'), apiSource.indexOf('api.interceptors.response.use'));
    expect(requestBlock).toContain('await MobileStorage.getCredentials()');
    expect(requestBlock).toContain('config.withCredentials = false');
    expect(requestBlock).not.toContain("localStorage.setItem('token'");
    const mobileRefresh = apiSource.slice(apiSource.indexOf('// Une session mobile'), apiSource.indexOf('// Auto-refresh/Sync web'));
    expect(mobileRefresh).toContain('MobileStorage.refreshCredentials()');
    expect(mobileRefresh).not.toContain("localStorage.setItem('token'");
  });
});
