import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_ROUTES, resolveDashboardTab } from './bridge';

describe('MOB-5A team routing', () => {
  it('keeps dentists inside the canonical dashboard shell', () => {
    expect(MOBILE_BRIDGE_ROUTES.dentists).toBe('/mobile/dashboard?tab=dentists');
    expect(resolveDashboardTab('?tab=dentists')).toBe('dentists');
  });

  it('keeps unknown dashboard destinations fail-safe on agenda', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
