export interface TrackedInstallment {
  id: number;
  label: string;
  amount: number;
  due_date: string;
  paid_date?: string | null;
  status: string;
}

export interface TrackedInstallmentPlan {
  id: number;
  title: string;
  total_amount: number;
  installments: TrackedInstallment[];
}

export interface InstallmentPlanSummary {
  paidTotal: number;
  remainingTotal: number;
  paidCount: number;
  pendingCount: number;
  nextPending: TrackedInstallment | null;
  overdueCount: number;
}

function cents(value: number): number {
  return Math.round((Number(value) || 0) * 100);
}

function normalizedStatus(value: string): string {
  return String(value || '').trim().toUpperCase();
}

export function isTrackedInstallmentPaid(item: TrackedInstallment): boolean {
  return normalizedStatus(item.status) === 'PAYE';
}

export function summarizeInstallmentPlan(
  plan: TrackedInstallmentPlan,
  todayIso?: string,
): InstallmentPlanSummary {
  const paid = plan.installments.filter(isTrackedInstallmentPaid);
  const pending = plan.installments.filter(item => !isTrackedInstallmentPaid(item));
  const paidCents = paid.reduce((sum, item) => sum + cents(item.amount), 0);
  const totalCents = cents(plan.total_amount);
  const remainingCents = Math.max(totalCents - paidCents, 0);

  const nextPending = [...pending]
    .filter(item => Boolean(item.due_date))
    .sort((left, right) => left.due_date.localeCompare(right.due_date))[0] || null;

  const today = todayIso ? todayIso.slice(0, 10) : null;
  const overdueCount = today
    ? pending.filter(item => Boolean(item.due_date) && item.due_date.slice(0, 10) < today).length
    : 0;

  return {
    paidTotal: paidCents / 100,
    remainingTotal: remainingCents / 100,
    paidCount: paid.length,
    pendingCount: pending.length,
    nextPending,
    overdueCount,
  };
}
