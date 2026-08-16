export type AccountingDocumentTab = 'devis' | 'honoraires';

export function requiresDevisToHonorairesConfirmation(
  activeTab: string,
  targetTab: string,
): boolean {
  return activeTab === 'devis' && targetTab === 'honoraires';
}
