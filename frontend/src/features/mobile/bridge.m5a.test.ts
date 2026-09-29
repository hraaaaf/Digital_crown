import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_ROUTES, resolveDashboardTab } from './bridge';

describe('Digital Crown Pocket canonical routing', () => {
  it('keeps the current shell routes and restores merged Pocket V1 routes', () => {
    expect(MOBILE_BRIDGE_ROUTES.stock).toBe('/mobile/dashboard?tab=stock');
    expect(MOBILE_BRIDGE_ROUTES.library).toBe('/mobile/dashboard?tab=library');
    expect(MOBILE_BRIDGE_ROUTES.marketplace).toBe('/mobile/dashboard?tab=marketplace');
    expect(MOBILE_BRIDGE_ROUTES.finance).toBe('/mobile/dashboard?tab=finance');
    expect(MOBILE_BRIDGE_ROUTES.lab).toBe('/mobile/dashboard?tab=lab');

    for (const tab of ['agenda', 'patients', 'waiting-room', 'frontdesk', 'notifications', 'securite', 'dentists', 'finance', 'lab', 'bot', 'stock', 'library', 'marketplace']) {
      expect(resolveDashboardTab(`?tab=${tab}`)).toBe(tab);
    }
  });

  it('fails closed only for unknown dashboard modules', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
    expect(resolveDashboardTab('')).toBe('agenda');
  });
});
