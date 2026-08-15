export type DocumentPaymentStatus = 'EN_ATTENTE' | 'PARTIEL' | 'PAYE';
export type AccountingPaymentMode = 'Espèces' | 'Chèque' | 'TPE' | 'Virement';
export type BackendPaymentMethod = 'ESPECES' | 'CHEQUE' | 'CARTE' | 'VIREMENT';

export const PARTIAL_PAYMENT_DISABLED_REASON =
  "Le paiement partiel doit être enregistré avec un montant encaissé explicite dans le flux d'encaissement dédié.";

export function mapPaymentModeToBackend(mode: AccountingPaymentMode): BackendPaymentMethod {
  switch (mode) {
    case 'Espèces': return 'ESPECES';
    case 'Chèque': return 'CHEQUE';
    case 'TPE': return 'CARTE';
    case 'Virement': return 'VIREMENT';
  }
}

export function validateExplicitCollectedAmount(amount: number): string | null {
  if (!Number.isFinite(amount) || amount <= 0) {
    return 'Le montant encaissé doit être strictement positif.';
  }
  return null;
}
