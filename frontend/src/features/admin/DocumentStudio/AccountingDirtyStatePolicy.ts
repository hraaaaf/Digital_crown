export interface AccountingDirtyItem {
  description: string;
  dent: string;
  price: number | string;
  toothNumbers?: number[];
  category?: string;
  odontogramSurfaces?: string[];
  odontogramNotes?: string;
  odontogramTreatmentCode?: string;
}

export type AccountingDirtyTab = 'devis' | 'honoraires';

export function accountingDocumentFingerprint(
  tab: AccountingDirtyTab,
  items: AccountingDirtyItem[],
): string {
  return JSON.stringify({
    tab,
    items: items.map(item => ({
      description: item.description,
      dent: item.dent,
      price: Number(item.price),
      toothNumbers: [...(item.toothNumbers || [])],
      category: item.category || '',
      odontogramSurfaces: [...(item.odontogramSurfaces || [])],
      odontogramNotes: item.odontogramNotes || '',
      odontogramTreatmentCode: item.odontogramTreatmentCode || '',
    })),
  });
}

export function isAccountingDocumentDirty(
  tab: AccountingDirtyTab,
  items: AccountingDirtyItem[],
  baselineFingerprint: string | null,
): boolean {
  if (!items.some(item => item.description.trim())) return false;
  if (baselineFingerprint === null) return true;
  return accountingDocumentFingerprint(tab, items) !== baselineFingerprint;
}
