const toCents = (value: number, label: string): number => {
  if (!Number.isFinite(value) || value < 0) {
    throw new Error(`${label} invalide.`);
  }
  return Math.round(value * 100);
};

export interface InstallmentAllocation {
  advanceAmount: number;
  monthlyAmounts: number[];
  totalAmount: number;
}

export function buildExactInstallmentAllocation(
  totalAmount: number,
  advanceAmount: number,
  monthsCount: number,
): InstallmentAllocation {
  if (!Number.isInteger(monthsCount) || monthsCount < 1) {
    throw new Error('Le nombre de mensualités doit être un entier positif.');
  }

  const totalCents = toCents(totalAmount, 'Montant total');
  const advanceCents = toCents(advanceAmount, 'Avance');
  if (advanceCents > totalCents) {
    throw new Error('L’avance ne peut pas dépasser le montant total.');
  }

  const remainderCents = totalCents - advanceCents;
  const baseMonthlyCents = Math.floor(remainderCents / monthsCount);
  const residualCents = remainderCents % monthsCount;
  const monthlyAmounts = Array.from({ length: monthsCount }, (_, index) =>
    (baseMonthlyCents + (index < residualCents ? 1 : 0)) / 100,
  );

  return {
    advanceAmount: advanceCents / 100,
    monthlyAmounts,
    totalAmount: totalCents / 100,
  };
}
