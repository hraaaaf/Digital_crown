import { describe, expect, it } from 'vitest';

import { accountingDocumentTotal } from './AccountingTotalPolicy';

describe('AccountingTotalPolicy', () => {
  it('sums real treatment rows', () => {
    expect(accountingDocumentTotal([
      { description: 'Composite', price: 500 },
      { description: 'Couronne', price: '2500' },
    ])).toBe(3000);
  });

  it('never lets visual phase rows affect the total', () => {
    expect(accountingDocumentTotal([
      { description: '--- PHASE 1 : ASSAINISSEMENT ---', price: 9999 },
      { description: 'Détartrage', price: 500 },
    ])).toBe(500);
  });

  it('treats invalid prices as zero', () => {
    expect(accountingDocumentTotal([
      { description: 'Acte', price: 'not-a-number' },
    ])).toBe(0);
  });
});
