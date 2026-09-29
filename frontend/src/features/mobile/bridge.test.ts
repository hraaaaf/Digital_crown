import { describe, expect, it } from 'vitest';
import { resolveBridgeRoute, resolveDashboardTab } from './bridge';

describe('Digital Crown Pocket bridge routing', () => {
  it('preserves Patients as a canonical Pocket deep-link and internal tab', () => {
    expect(resolveBridgeRoute('patients')).toBe('/mobile/dashboard?tab=patients');
    expect(resolveDashboardTab('?tab=patients')).toBe('patients');
  });

  it('preserves canonical Pocket module deep links', () => {
    for (const tab of [
      'agenda',
      'finance',
      'lab',
      'bot',
      'dentists',
      'stock',
      'library',
      'marketplace',
      'securite',
      'notifications',
      'waiting-room',
      'frontdesk',
    ]) {
      expect(resolveDashboardTab(`?tab=${tab}`)).toBe(tab);
    }
  });

  it('fails safely to Today for unknown tabs', () => {
    expect(resolveDashboardTab('?tab=unknown')).toBe('agenda');
  });
});
