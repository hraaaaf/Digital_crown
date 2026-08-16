import type { HubDocumentType } from '../DocumentHub';
import { requiresDevisToHonorairesConfirmation } from './AccountingDocumentTransitionPolicy';

export type DocumentDirtySource = 'accounting' | 'prescription' | 'libre' | 'diagnostic';

export interface DocumentDirtyStateSnapshot {
  accountingDirty: boolean;
  prescriptionDirty: boolean;
  libreDirty: boolean;
  diagnosticDirty: boolean;
}

export interface DocumentNavigationDecision {
  allow: boolean;
  requiresTransitionConfirmation: boolean;
  discardSource: DocumentDirtySource | null;
}

const isAccountingTab = (tab: HubDocumentType): boolean => tab === 'devis' || tab === 'honoraires';

export function resolveDocumentNavigation(
  activeTab: HubDocumentType,
  targetTab: HubDocumentType,
  dirty: DocumentDirtyStateSnapshot,
): DocumentNavigationDecision {
  if (activeTab === targetTab) {
    return { allow: false, requiresTransitionConfirmation: false, discardSource: null };
  }

  const isAccountingSwitch = isAccountingTab(activeTab) && isAccountingTab(targetTab);
  const requiresTransitionConfirmation = requiresDevisToHonorairesConfirmation(activeTab, targetTab);

  if (activeTab === 'ordonnance' && dirty.prescriptionDirty) {
    return { allow: false, requiresTransitionConfirmation, discardSource: 'prescription' };
  }
  if (activeTab === 'libre' && dirty.libreDirty) {
    return { allow: false, requiresTransitionConfirmation, discardSource: 'libre' };
  }
  if (activeTab === 'plan' && dirty.diagnosticDirty) {
    return { allow: false, requiresTransitionConfirmation, discardSource: 'diagnostic' };
  }
  if (isAccountingTab(activeTab) && dirty.accountingDirty && !isAccountingSwitch) {
    return { allow: false, requiresTransitionConfirmation, discardSource: 'accounting' };
  }

  return { allow: true, requiresTransitionConfirmation, discardSource: null };
}
