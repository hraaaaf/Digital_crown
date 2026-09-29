import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const hookSource = readSource('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
const dashboardSource = readSource('src/features/mobile/Dashboard/MobileDashboard.tsx');
const storageSource = readSource('src/services/zka/MobileStorage.ts');
const mobileApiSource = readSource('src/services/zka/mobileApi.ts');
const stockSource = readSource('src/features/mobile/Dashboard/views/StockView.tsx');
const botSource = readSource('src/features/mobile/Dashboard/views/BotView.tsx');
const marketplaceSource = readSource('src/features/partnerMarketplace/usePartnerMarketplace.ts');
const authBackend = readSource('../backend/routers/auth.py');
const mobileBackend = readSource('../backend/routers/mobile.py');

describe('Digital Crown Pocket production runtime scope', () => {
  it('keeps Today bounded and restores the canonical Pocket surfaces', () => {
    expect(dashboardSource).not.toContain("import { AgendaView }");
    expect(dashboardSource).toContain('PocketTodayOverview');
    for (const surface of ['FinanceView', 'LabView', 'BotView', 'DentistsView', 'StockView', 'LibraryView', 'MarketplaceView']) {
      expect(dashboardSource).toContain(surface);
    }
    expect(dashboardSource).toContain('PocketRestrictedView');
  });

  it('routes Pocket data through the mobile boundary instead of desktop auth', () => {
    expect(mobileApiSource).toContain('/api/mobile');
    expect(mobileApiSource).toContain('mobileFetch');
    expect(mobileApiSource).toContain('MobileStorage.getCredentials()');
    expect(stockSource).toContain('mobileApiJson');
    expect(stockSource).not.toContain("services/api");
    expect(hookSource).toContain("mobileApiJson<LabJob[]>('/lab-jobs')");
    expect(marketplaceSource).toContain('mobileApiJson');
    expect(marketplaceSource).toContain('isPocketRuntime');
  });

  it('keeps desktop and Pocket credentials isolated and fails closed', () => {
    expect(storageSource).not.toContain("localStorage.setItem('token'");
    expect(hookSource).not.toContain("localStorage.setItem('token'");
    expect(authBackend).toContain('token_type != "access"');
    expect(authBackend).toContain('Paired Pocket JWTs are intentionally scoped');
    expect(mobileBackend).toContain("_legacy.require_mobile_permission");
    expect(mobileBackend).toContain("@router.get('/stock/items'");
    expect(mobileBackend).toContain("@router.get('/lab-jobs'");
    expect(mobileBackend).toContain("@router.get('/partner-catalog/products'");
  });

  it('keeps Assistant canonical without opening a desktop session', () => {
    expect(botSource).toContain('data-mobile-assistant');
    expect(botSource).toContain('En cours de construction');
    expect(botSource).not.toContain('CrownBotChat');
  });
});
