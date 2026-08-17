import { describe, expect, it, vi } from 'vitest';
import { convertPlanActsToQuoteItems } from './AccountingPlanConversionPolicy';

describe('AccountingPlanConversionPolicy', () => {
  it('converts plan acts without inventing prices', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1000);
    const rows = convertPlanActsToQuoteItems([
      { suggested_act: 'Couronne zircone', fdi: 11, phase: 'PROTHETIQUE' },
      { act: 'Détartrage', phase: 'ASSAINISSEMENT' },
    ]);

    expect(rows).toEqual([
      {
        id: 1000,
        description: 'Couronne zircone',
        dent: '11',
        price: 0,
        toothNumbers: [11],
        category: 'PROTHETIQUE',
      },
      {
        id: 1001,
        description: 'Détartrage',
        dent: '0',
        price: 0,
        toothNumbers: [],
        category: 'ASSAINISSEMENT',
      },
    ]);
    vi.restoreAllMocks();
  });

  it('drops empty proposals', () => {
    expect(convertPlanActsToQuoteItems([{ act: '   ' }])).toEqual([]);
  });
});
