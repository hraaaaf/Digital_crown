import { describe, expect, it } from 'vitest';
import { formatLocalDateKey, getLocalDayBounds } from './localDate';

describe('Dashboard D7 — date locale', () => {
  it('construit la clé du jour depuis les composantes locales', () => {
    const date = new Date(2026, 7, 16, 23, 30, 0);
    expect(formatLocalDateKey(date)).toBe('2026-08-16');
  });

  it('construit les bornes de la journée locale sans conversion UTC', () => {
    const date = new Date(2026, 0, 2, 0, 15, 0);
    expect(getLocalDayBounds(date)).toEqual({
      start: '2026-01-02T00:00:00',
      end: '2026-01-02T23:59:59',
    });
  });
});
