import { describe, expect, it } from 'vitest';
import {
  filterLearnableAccountingRows,
  shouldLearnAccountingAct,
} from './AccountingActLearningPolicy';

describe('P3-D2 accounting act learning', () => {
  it('learns only after a successful archive', () => {
    expect(shouldLearnAccountingAct('SELECT')).toBe(false);
    expect(shouldLearnAccountingAct('EDIT')).toBe(false);
    expect(shouldLearnAccountingAct('PREVIEW')).toBe(false);
    expect(shouldLearnAccountingAct('GENERATE')).toBe(false);
    expect(shouldLearnAccountingAct('ARCHIVE_SUCCESS')).toBe(true);
  });

  it('excludes visual phase rows and malformed acts from learning', () => {
    const rows = filterLearnableAccountingRows([
      { description: 'Composite', price: 600 },
      { description: '--- PHASE 1 ---', price: 0 },
      { description: ' ', price: 100 },
      { description: 'Couronne', price: Number.NaN },
    ]);
    expect(rows).toEqual([{ description: 'Composite', price: 600 }]);
  });
});
