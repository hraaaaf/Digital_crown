import { describe, expect, it } from 'vitest';
import { buildInstallmentPlanCreatePayload } from './InstallmentPlanDraftPolicy';

describe('InstallmentPlanDraftPolicy', () => {
  it('builds a pending-only exact payload', () => {
    expect(buildInstallmentPlanCreatePayload('12', '  Ortho  ', 1000, [
      { label: ' Avance ', amount: 333.33, dueDate: '2026-09-01' },
      { label: 'Mensualité 2', amount: 333.33, dueDate: '2026-10-01' },
      { label: 'Mensualité 3', amount: 333.34, dueDate: '2026-11-01' },
    ])).toEqual({
      patient_id: 12,
      title: 'Ortho',
      total_amount: 1000,
      installments: [
        { label: 'Avance', amount: 333.33, due_date: '2026-09-01T00:00:00', status: 'EN_ATTENTE' },
        { label: 'Mensualité 2', amount: 333.33, due_date: '2026-10-01T00:00:00', status: 'EN_ATTENTE' },
        { label: 'Mensualité 3', amount: 333.34, due_date: '2026-11-01T00:00:00', status: 'EN_ATTENTE' },
      ],
    });
  });

  it('rejects an unbalanced draft', () => {
    expect(() => buildInstallmentPlanCreatePayload(1, 'Plan', 1000, [
      { label: 'A', amount: 500, dueDate: '2026-09-01' },
      { label: 'B', amount: 400, dueDate: '2026-10-01' },
    ])).toThrow(/égale au total/);
  });

  it('rejects invalid patient, title, rows and dates', () => {
    expect(() => buildInstallmentPlanCreatePayload(0, 'Plan', 100, [{ label: 'A', amount: 100, dueDate: '2026-09-01' }])).toThrow();
    expect(() => buildInstallmentPlanCreatePayload(1, ' ', 100, [{ label: 'A', amount: 100, dueDate: '2026-09-01' }])).toThrow();
    expect(() => buildInstallmentPlanCreatePayload(1, 'Plan', 100, [])).toThrow();
    expect(() => buildInstallmentPlanCreatePayload(1, 'Plan', 100, [{ label: 'A', amount: 100, dueDate: '01/09/2026' }])).toThrow();
  });

  it('rejects non-finite or non-positive amounts', () => {
    expect(() => buildInstallmentPlanCreatePayload(1, 'Plan', Number.NaN, [{ label: 'A', amount: 100, dueDate: '2026-09-01' }])).toThrow();
    expect(() => buildInstallmentPlanCreatePayload(1, 'Plan', 100, [{ label: 'A', amount: 0, dueDate: '2026-09-01' }])).toThrow();
  });
});
