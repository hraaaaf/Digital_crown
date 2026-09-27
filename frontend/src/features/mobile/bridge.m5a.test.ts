import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_LABELS, MOBILE_BRIDGE_ROUTES, resolveDashboardTab } from './bridge';

describe('Digital Crown Pocket bounded routing', () => {
  it('keeps the general bridge canonical and the Pocket shell bounded', () => {
    expect(MOBILE_BRIDGE_ROUTES).toEqual({ agenda: '/mobile/dashboard?tab=agenda' });
    expect(MOBILE_BRIDGE_LABELS).toEqual({ agenda: 'Digital Crown Pocket' });

    expect(resolveDashboardTab('?tab=agenda')).toBe('agenda');
    expect(resolveDashboardTab('?tab=patients')).toBe('patients');
    expect(resolveDashboardTab('?tab=waiting-room')).toBe('waiting-room');
    expect(resolveDashboardTab('?tab=frontdesk')).toBe('frontdesk');
    expect(resolveDashboardTab('?tab=notifications')).toBe('notifications');
    expect(resolveDashboardTab('?tab=securite')).toBe('securite');
  });

  it('fails closed from retired mobile modules to Today', () => {
    expect(resolveDashboardTab('?tab=dentists')).toBe('agenda');
    expect(resolveDashboardTab('?tab=finance')).toBe('agenda');
    expect(resolveDashboardTab('?tab=lab')).toBe('agenda');
    expect(resolveDashboardTab('?tab=bot')).toBe('agenda');
    expect(resolveDashboardTab('?tab=stock')).toBe('agenda');
    expect(resolveDashboardTab('?tab=library')).toBe('agenda');
    expect(resolveDashboardTab('?tab=marketplace')).toBe('agenda');
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
