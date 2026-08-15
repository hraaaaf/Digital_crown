export type DocumentPaymentStatus = 'EN_ATTENTE' | 'PARTIEL' | 'PAYE';
export type AccountingPaymentMode = 'Espèces' | 'Chèque' | 'TPE' | 'Virement';
export type BackendPaymentMethod = 'ESPECES' | 'CHEQUE' | 'CARTE' | 'VIREMENT';

export interface DocumentPaymentStatusOption {
  id: DocumentPaymentStatus;
  label: string;
  enabled: boolean;
  reason?: string;
}

export const PARTIAL_PAYMENT_DISABLED_REASON =
  "Le paiement partiel doit être enregistré avec un montant encaissé explicite dans le flux d'encaissement dédié.";

export function getDocumentPaymentStatusOptions(): DocumentPaymentStatusOption[] {
  return [
    { id: 'EN_ATTENTE', label: 'Attente', enabled: true },
    {
      id: 'PARTIEL',
      label: 'Partiel',
      enabled: false,
      reason: PARTIAL_PAYMENT_DISABLED_REASON,
    },
    { id: 'PAYE', label: 'Réglé', enabled: true },
  ];
}

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
