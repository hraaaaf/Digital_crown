import { describe, expect, it } from 'vitest';

import { resolveAccountingBundles } from './AccountingBundlePolicy';

describe('AccountingBundlePolicy', () => {
  it('ignores legacy bundle prices and uses the managed catalog price', () => {
    expect(resolveAccountingBundles(
      [{ name: 'Polissage', price: 100, category: 'Prévention' }],
      [{ name: 'Polissage', base_price: 350, category: 'PREVENTION' }],
    )).toEqual([
      { name: 'Polissage', price: 350, category: 'PREVENTION', priceSource: 'CATALOG' },
    ]);
  });

  it('keeps a missing catalog tariff unresolved instead of trusting a hard-coded price', () => {
    expect(resolveAccountingBundles(
      [{ name: 'Radio Alvéolaire', price: 100, category: 'Radiologie' }],
      [],
    )).toEqual([
      { name: 'Radio Alvéolaire', price: 0, category: 'Radiologie', priceSource: 'UNRESOLVED' },
    ]);
  });

  it('deduplicates suggestions by normalized name', () => {
    expect(resolveAccountingBundles(
      [{ name: 'Polissage', price: 100 }, { name: ' polissage ', price: 200 }],
      [{ name: 'Polissage', base_price: 350 }],
    )).toHaveLength(1);
  });
});
