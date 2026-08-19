import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

export type DocumentTab = CertifiableDocumentStudioTab;

export interface DocumentDirtySnapshot {
  prescription: boolean;
  certificate: boolean;
  accounting: boolean;
  installment: boolean;
  libre: boolean;
}

export function shouldGuardDocumentTabTransition(
  activeTab: DocumentTab,
  nextTab: DocumentTab,
  dirty: DocumentDirtySnapshot,
): boolean {
  if (activeTab === nextTab) return false;

  const accountingSwitch =
    (activeTab === 'devis' || activeTab === 'honoraires') &&
    (nextTab === 'devis' || nextTab === 'honoraires');
  if (accountingSwitch) return false;

  switch (activeTab) {
    case 'ordonnance':
      return dirty.prescription;
    case 'certificat':
      return dirty.certificate;
    case 'devis':
    case 'honoraires':
      return dirty.accounting;
    case 'echeancier':
      return dirty.installment;
    case 'libre':
      return dirty.libre;
    default:
      return false;
  }
}