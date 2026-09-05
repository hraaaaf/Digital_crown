import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_ROUTES, resolveDashboardTab } from './bridge';

describe('MOB-5 secondary routing', () => {
  it('keeps Team and Frontdesk inside the canonical dashboard shell', () => {
    expect(MOBILE_BRIDGE_ROUTES.dentists).toBe('/mobile/dashboard?tab=dentists');
    expect(resolveDashboardTab('?tab=dentists')).toBe('dentists');
    expect(MOBILE_BRIDGE_ROUTES.frontdesk).toBe('/mobile/dashboard?tab=frontdesk');
    expect(resolveDashboardTab('?tab=frontdesk')).toBe('frontdesk');
  });

  it('keeps unknown dashboard destinations fail-safe on agenda', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
