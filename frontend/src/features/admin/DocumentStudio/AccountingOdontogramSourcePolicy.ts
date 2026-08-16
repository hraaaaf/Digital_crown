export interface AccountingOdontogramSourceItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
  category?: string;
  odontogramSurfaces?: string[];
  odontogramNotes?: string;
  odontogramTreatmentCode?: string;
}

export interface AccountingToothData {
  tooth_number: number;
  treatments: Array<{ code: string; name: string; price: number }>;
  surfaces: string[];
  notes: string;
}

function uniqueToothNumbers(values: number[] | undefined): number[] {
  return [...new Set((values || []).filter(value => Number.isInteger(value) && value > 0))].sort((a, b) => a - b);
}

function toothNumberFromKey(key: string | undefined): number | null {
  if (!key) return null;
  const value = Number(key.split('::', 1)[0]);
  return Number.isInteger(value) && value > 0 ? value : null;
}

export function canonicalToothNumbers(item: AccountingOdontogramSourceItem): number[] {
  const explicit = uniqueToothNumbers(item.toothNumbers);
  if (explicit.length > 0) return explicit;
  const keyed = toothNumberFromKey(item._odontogramKey);
  return keyed ? [keyed] : [];
}

export function canonicalDentLabel(item: AccountingOdontogramSourceItem): string {
  const teeth = canonicalToothNumbers(item);
  return teeth.length > 0 ? teeth.join('-') : item.dent;
}

export function normalizeStructuredAccountingItems<T extends AccountingOdontogramSourceItem>(items: T[]): T[] {
  return items.map(item => {
    const teeth = canonicalToothNumbers(item);
    if (teeth.length === 0) return item;
    return {
      ...item,
      dent: teeth.join('-'),
      toothNumbers: teeth,
    };
  });
}

export function buildTeethDataFromAccountingItems(items: AccountingOdontogramSourceItem[]): AccountingToothData[] {
  const byTooth = new Map<number, AccountingToothData>();

  items.forEach(item => {
    if (!item._odontogramKey) return;
    const toothNumber = toothNumberFromKey(item._odontogramKey);
    if (!toothNumber) return;

    const current = byTooth.get(toothNumber) || {
      tooth_number: toothNumber,
      treatments: [],
      surfaces: [],
      notes: '',
    };

    current.treatments.push({
      code: item.odontogramTreatmentCode || 'ACT',
      name: item.description,
      price: Number(item.price) || 0,
    });

    for (const surface of item.odontogramSurfaces || []) {
      if (surface && !current.surfaces.includes(surface)) current.surfaces.push(surface);
    }

    const notes = (item.odontogramNotes || '').trim();
    if (notes) {
      const existingNotes = current.notes ? current.notes.split('\n').filter(Boolean) : [];
      if (!existingNotes.includes(notes)) current.notes = [...existingNotes, notes].join('\n');
    }

    byTooth.set(toothNumber, current);
  });

  return [...byTooth.values()].sort((a, b) => a.tooth_number - b.tooth_number);
}

interface ArchivedTreatment {
  code?: string;
  name: string;
  price?: number;
}

export interface ArchivedToothData {
  tooth_number: number;
  treatments?: ArchivedTreatment[];
  surfaces?: string[];
  notes?: string | null;
}

export function hydrateAccountingItemsFromTeethData<T extends AccountingOdontogramSourceItem>(
  items: T[],
  teethData: ArchivedToothData[] | undefined,
): T[] {
  if (!teethData?.length) return normalizeStructuredAccountingItems(items);

  const usedItemIds = new Set<number>();
  const hydrated = items.map(item => ({ ...item })) as T[];

  teethData.forEach(tooth => {
    const toothNumber = Number(tooth.tooth_number);
    if (!Number.isInteger(toothNumber) || toothNumber <= 0) return;

    (tooth.treatments || []).forEach((treatment, treatmentIndex) => {
      const match = hydrated.find(item => {
        if (usedItemIds.has(item.id)) return false;
        const teeth = canonicalToothNumbers(item);
        const dentMatches = teeth.includes(toothNumber) || item.dent.trim() === String(toothNumber);
        return dentMatches && item.description.trim().toLocaleLowerCase() === treatment.name.trim().toLocaleLowerCase();
      });
      if (!match) return;

      usedItemIds.add(match.id);
      match.toothNumbers = [toothNumber];
      match.dent = String(toothNumber);
      match._odontogramKey = `${toothNumber}::archived-${treatmentIndex}-${match.id}`;
      match.odontogramTreatmentCode = treatment.code || 'ACT';
      match.odontogramSurfaces = [...new Set((tooth.surfaces || []).filter(Boolean))];
      match.odontogramNotes = tooth.notes || '';
    });
  });

  return normalizeStructuredAccountingItems(hydrated);
}
