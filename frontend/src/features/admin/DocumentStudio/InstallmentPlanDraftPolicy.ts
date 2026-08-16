export interface InstallmentDraftRow {
  label: string;
  amount: number;
  dueDate: string;
}

export interface InstallmentPlanCreatePayload {
  patient_id: number;
  title: string;
  total_amount: number;
  installments: Array<{
    label: string;
    amount: number;
    due_date: string;
    status: 'EN_ATTENTE';
  }>;
}

function cents(value: number): number {
  if (!Number.isFinite(value)) throw new Error('Montant non fini.');
  return Math.round(value * 100);
}

export function buildInstallmentPlanCreatePayload(
  patientId: string | number,
  title: string,
  totalAmount: number,
  rows: InstallmentDraftRow[],
): InstallmentPlanCreatePayload {
  const normalizedPatientId = Number(patientId);
  if (!Number.isInteger(normalizedPatientId) || normalizedPatientId <= 0) {
    throw new Error('Patient invalide.');
  }

  const normalizedTitle = String(title || '').trim();
  if (!normalizedTitle) throw new Error('Titre du plan requis.');

  const totalCents = cents(totalAmount);
  if (totalCents <= 0) throw new Error('Total strictement positif requis.');
  if (rows.length === 0) throw new Error('Au moins une échéance est requise.');

  const installments = rows.map(row => {
    const label = String(row.label || '').trim();
    if (!label) throw new Error("Chaque échéance doit avoir un libellé.");
    const amountCents = cents(row.amount);
    if (amountCents <= 0) throw new Error("Chaque échéance doit avoir un montant positif.");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.dueDate)) throw new Error("Date d'échéance invalide.");
    return {
      label,
      amount: amountCents / 100,
      due_date: `${row.dueDate}T00:00:00`,
      status: 'EN_ATTENTE' as const,
    };
  });

  const installmentCents = installments.reduce((sum, row) => sum + cents(row.amount), 0);
  if (installmentCents !== totalCents) {
    throw new Error('La somme des échéances doit être égale au total du plan.');
  }

  return {
    patient_id: normalizedPatientId,
    title: normalizedTitle,
    total_amount: totalCents / 100,
    installments,
  };
}
