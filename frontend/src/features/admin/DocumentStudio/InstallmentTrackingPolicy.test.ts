import { describe, expect, it } from 'vitest';
import { summarizeInstallmentPlan } from './InstallmentTrackingPolicy';

const plan = {
  id: 1,
  title: 'Traitement orthodontique',
  total_amount: 1000,
  installments: [
    { id: 1, label: 'Avance', amount: 300, due_date: '2026-07-01', paid_date: '2026-07-01', status: 'PAYE' },
    { id: 2, label: 'Mensualité 1', amount: 350, due_date: '2026-08-01', status: 'EN_ATTENTE' },
    { id: 3, label: 'Mensualité 2', amount: 350, due_date: '2026-09-01', status: 'EN_ATTENTE' },
  ],
};

describe('InstallmentTrackingPolicy', () => {
  it('computes paid, remaining and counts from backend status', () => {
    expect(summarizeInstallmentPlan(plan, '2026-08-16')).toMatchObject({
      paidTotal: 300,
      remainingTotal: 700,
      paidCount: 1,
      pendingCount: 2,
      overdueCount: 1,
    });
  });

  it('selects the earliest pending due date', () => {
    expect(summarizeInstallmentPlan(plan, '2026-08-16').nextPending?.id).toBe(2);
  });

  it('never returns a negative remaining amount', () => {
    const overpaid = { ...plan, total_amount: 200 };
    expect(summarizeInstallmentPlan(overpaid).remainingTotal).toBe(0);
  });

  it('uses cent arithmetic for financial summaries', () => {
    const centsPlan = {
      id: 2,
      title: 'Centimes',
      total_amount: 1000,
      installments: [
        { id: 1, label: 'A', amount: 333.33, due_date: '2026-08-01', status: 'PAYE' },
        { id: 2, label: 'B', amount: 333.33, due_date: '2026-09-01', status: 'PAYE' },
        { id: 3, label: 'C', amount: 333.34, due_date: '2026-10-01', status: 'EN_ATTENTE' },
      ],
    };
    expect(summarizeInstallmentPlan(centsPlan).paidTotal).toBe(666.66);
    expect(summarizeInstallmentPlan(centsPlan).remainingTotal).toBe(333.34);
  });
});
