import { describe, expect, it } from 'vitest';
import { resolveBridgeRoute, resolveDashboardTab } from './bridge';

describe('Digital Crown Pocket bridge routing', () => {
  it('keeps Patients as an internal Pocket tab while the general bridge opens Today', () => {
    expect(resolveBridgeRoute('patients')).toBe('/mobile/dashboard?tab=agenda');
    expect(resolveDashboardTab('?tab=patients')).toBe('patients');
  });

  it('retires historical module deep links and preserves bounded Pocket tabs', () => {
    expect(resolveDashboardTab('?tab=agenda')).toBe('agenda');
    expect(resolveDashboardTab('?tab=finance')).toBe('agenda');
    expect(resolveDashboardTab('?tab=lab')).toBe('agenda');
    expect(resolveDashboardTab('?tab=bot')).toBe('agenda');
    expect(resolveDashboardTab('?tab=dentists')).toBe('agenda');
    expect(resolveDashboardTab('?tab=stock')).toBe('agenda');
    expect(resolveDashboardTab('?tab=library')).toBe('agenda');
    expect(resolveDashboardTab('?tab=marketplace')).toBe('agenda');
    expect(resolveDashboardTab('?tab=securite')).toBe('securite');
    expect(resolveDashboardTab('?tab=notifications')).toBe('notifications');
    expect(resolveDashboardTab('?tab=waiting-room')).toBe('waiting-room');
    expect(resolveDashboardTab('?tab=frontdesk')).toBe('frontdesk');
  });

  it('fails safely to Today for unknown tabs', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
