export interface AccountingPhaseItem {
  description: string;
}

export type AccountingPhase = 'ASSAINISSEMENT' | 'CHIRURGIE' | 'PROTHETIQUE' | 'AUTRES';

export interface AccountingPhaseGroup<T extends AccountingPhaseItem> {
  phase: AccountingPhase;
  label: string;
  items: T[];
}

const PHASE_LABELS: Record<AccountingPhase, string> = {
  ASSAINISSEMENT: 'Phase 1 : Assainissement',
  CHIRURGIE: 'Phase 2 : Chirurgie',
  PROTHETIQUE: 'Phase 3 : Prothétique',
  AUTRES: 'Autres actes',
};

export function isAccountingPhaseSeparator(description: string): boolean {
  const value = (description || '').trim();
  return /^---\s+.+\s+---$/.test(value);
}

export function classifyAccountingPhase(description: string): AccountingPhase {
  const value = description.toLowerCase();
  if (/détartrage|detartrage|composite|carie|surfaçage|surfacage|endo|pulpectomie|traitement|obturation/.test(value)) {
    return 'ASSAINISSEMENT';
  }
  if (/extraction|implant|greffe|sinus|lambeau/.test(value)) {
    return 'CHIRURGIE';
  }
  if (/couronne|bridge|inlay|onlay|facette|prothèse|prothese/.test(value)) {
    return 'PROTHETIQUE';
  }
  return 'AUTRES';
}

export function groupAccountingItemsByPhase<T extends AccountingPhaseItem>(items: T[]): AccountingPhaseGroup<T>[] {
  const cleanItems = items.filter(item => !isAccountingPhaseSeparator(item.description));
  const buckets: Record<AccountingPhase, T[]> = {
    ASSAINISSEMENT: [],
    CHIRURGIE: [],
    PROTHETIQUE: [],
    AUTRES: [],
  };

  cleanItems.forEach(item => buckets[classifyAccountingPhase(item.description)].push(item));

  return (['ASSAINISSEMENT', 'CHIRURGIE', 'PROTHETIQUE', 'AUTRES'] as const)
    .filter(phase => buckets[phase].length > 0)
    .map(phase => ({ phase, label: PHASE_LABELS[phase], items: buckets[phase] }));
}
