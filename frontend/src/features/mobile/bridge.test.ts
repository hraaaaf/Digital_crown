import { describe, expect, it } from 'vitest';
import { resolveBridgeRoute, resolveDashboardTab } from './bridge';

describe('mobile bridge MOB-4', () => {
  it('resolves the new Patients deep link', () => {
    expect(resolveBridgeRoute('patients')).toBe('/mobile/dashboard?tab=patients');
    expect(resolveDashboardTab('?tab=patients')).toBe('patients');
  });

  it('preserves historical dashboard deep links', () => {
    expect(resolveDashboardTab('?tab=agenda')).toBe('agenda');
    expect(resolveDashboardTab('?tab=finance')).toBe('finance');
    expect(resolveDashboardTab('?tab=lab')).toBe('lab');
    expect(resolveDashboardTab('?tab=bot')).toBe('bot');
    expect(resolveDashboardTab('?tab=securite')).toBe('securite');
  });

  it('fails safely to agenda for unknown tabs', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
