import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_LABELS, MOBILE_BRIDGE_ROUTES, resolveDashboardTab } from './bridge';

describe('MOB-5 secondary routing', () => {
  it('keeps Team, Frontdesk, Notifications, Stock, Library and Marketplace inside the canonical dashboard shell', () => {
    expect(MOBILE_BRIDGE_ROUTES.dentists).toBe('/mobile/dashboard?tab=dentists');
    expect(resolveDashboardTab('?tab=dentists')).toBe('dentists');
    expect(MOBILE_BRIDGE_ROUTES.frontdesk).toBe('/mobile/dashboard?tab=frontdesk');
    expect(resolveDashboardTab('?tab=frontdesk')).toBe('frontdesk');
    expect(MOBILE_BRIDGE_ROUTES.notifications).toBe('/mobile/dashboard?tab=notifications');
    expect(resolveDashboardTab('?tab=notifications')).toBe('notifications');
    expect(MOBILE_BRIDGE_ROUTES.stock).toBe('/mobile/dashboard?tab=stock');
    expect(MOBILE_BRIDGE_LABELS.stock).toBe('Stock');
    expect(resolveDashboardTab('?tab=stock')).toBe('stock');
    expect(MOBILE_BRIDGE_ROUTES.library).toBe('/mobile/dashboard?tab=library');
    expect(MOBILE_BRIDGE_LABELS.library).toBe('Bibliothèque');
    expect(resolveDashboardTab('?tab=library')).toBe('library');
    expect(MOBILE_BRIDGE_ROUTES.marketplace).toBe('/mobile/dashboard?tab=marketplace');
    expect(MOBILE_BRIDGE_LABELS.marketplace).toBe('Marketplace');
    expect(resolveDashboardTab('?tab=marketplace')).toBe('marketplace');
  });

  it('keeps unknown dashboard destinations fail-safe on agenda', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});