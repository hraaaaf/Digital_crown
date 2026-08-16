import { describe, expect, it } from 'vitest';
import { installmentsAfterGlobalNoteToggle } from './AccountingHonorairesInstallmentPolicy';

const oldPlan = [{ id: 1, date: '2026-01-01', amount: 700, label: 'Ancien plan' }];

describe('AccountingHonorairesInstallmentPolicy', () => {
  it('clears inherited installments when a new global note starts', () => {
    expect(installmentsAfterGlobalNoteToggle(false, true, oldPlan)).toEqual([]);
  });

  it('keeps the current draft stable while already global', () => {
    expect(installmentsAfterGlobalNoteToggle(true, true, oldPlan)).toEqual(oldPlan);
  });

  it('does not mutate installment state on non-global transitions', () => {
    expect(installmentsAfterGlobalNoteToggle(false, false, oldPlan)).toEqual(oldPlan);
    expect(installmentsAfterGlobalNoteToggle(true, false, oldPlan)).toEqual(oldPlan);
  });
});
