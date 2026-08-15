import { describe, expect, it } from 'vitest';
import { buildExactInstallmentAllocation } from './InstallmentAllocationPolicy';

describe('P4-A installment allocation policy', () => {
  it('réconcilie exactement au centime quand la division n’est pas entière', () => {
    const allocation = buildExactInstallmentAllocation(1000, 0, 3);

    expect(allocation.monthlyAmounts).toEqual([333.34, 333.33, 333.33]);
    expect(allocation.monthlyAmounts.reduce((sum, amount) => sum + amount, allocation.advanceAmount)).toBeCloseTo(1000, 2);
  });

  it('préserve une avance explicite et répartit uniquement le reste', () => {
    const allocation = buildExactInstallmentAllocation(2900, 500, 7);

    expect(allocation.advanceAmount).toBe(500);
    expect(allocation.monthlyAmounts).toHaveLength(7);
    expect(allocation.monthlyAmounts.reduce((sum, amount) => sum + amount, allocation.advanceAmount)).toBeCloseTo(2900, 2);
  });

  it('refuse les entrées financières incohérentes', () => {
    expect(() => buildExactInstallmentAllocation(1000, 1200, 3)).toThrow(/avance/i);
    expect(() => buildExactInstallmentAllocation(1000, 0, 0)).toThrow(/mensualités/i);
    expect(() => buildExactInstallmentAllocation(Number.NaN, 0, 3)).toThrow(/montant total/i);
  });
});
