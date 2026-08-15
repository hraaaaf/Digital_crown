export interface AccountingInstallmentAmount {
  amount: number;
}

export interface InstallmentReconciliation {
  billedTotal: number;
  installmentTotal: number;
  difference: number;
  reconciled: boolean;
}

const toCents = (value: number): number => Math.round((Number(value) || 0) * 100);

export function reconcileInstallments(
  billedTotal: number,
  installments: AccountingInstallmentAmount[],
): InstallmentReconciliation {
  const billedCents = toCents(billedTotal);
  const installmentCents = installments.reduce((sum, item) => sum + toCents(item.amount), 0);
  const differenceCents = installmentCents - billedCents;

  return {
    billedTotal: billedCents / 100,
    installmentTotal: installmentCents / 100,
    difference: differenceCents / 100,
    reconciled: differenceCents === 0,
  };
}

export function validateInstallmentAmounts(
  billedTotal: number,
  installments: AccountingInstallmentAmount[],
): string | null {
  if (!Number.isFinite(billedTotal) || billedTotal < 0) {
    return 'Le total facturé est invalide.';
  }
  if (installments.length === 0) {
    return 'Ajoutez au moins une échéance.';
  }
  if (installments.some(item => !Number.isFinite(item.amount) || item.amount <= 0)) {
    return 'Chaque échéance doit avoir un montant strictement positif.';
  }

  const reconciliation = reconcileInstallments(billedTotal, installments);
  if (!reconciliation.reconciled) {
    const sign = reconciliation.difference > 0 ? 'supérieure' : 'inférieure';
    return `La somme des échéances est ${sign} au total facturé de ${Math.abs(reconciliation.difference).toFixed(2)} MAD.`;
  }
  return null;
}
