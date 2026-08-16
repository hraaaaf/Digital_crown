import { describe, expect, it } from 'vitest';
import { resolveNamedDevisActPrice } from './AccountingNamedActPricePolicy';

describe('AccountingNamedActPricePolicy', () => {
  it('uses the managed catalog price', () => {
    expect(resolveNamedDevisActPrice('Détartrage', [
      { name: 'Détartrage', base_price: 650, category: 'PREVENTION' },
    ])).toEqual({ price: 650, category: 'PREVENTION', source: 'CATALOG' });
  });

  it('fails closed when the named act is absent from the catalog', () => {
    expect(resolveNamedDevisActPrice('Semestre ODF', [])).toEqual({
      price: 0,
      category: undefined,
      source: 'UNRESOLVED',
    });
  });

  it('rejects zero or invalid catalog amounts', () => {
    expect(resolveNamedDevisActPrice('Consultation', [
      { name: 'Consultation', base_price: 0 },
    ]).source).toBe('UNRESOLVED');
  });
});
