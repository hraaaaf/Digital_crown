export interface OdontogramTreatmentSelection {
  toothNumber: number;
  treatmentId: string | number;
  name: string;
  price: number;
  category?: string;
  dent?: string;
  surfaces?: string[];
  notes?: string;
  treatmentCode?: string;
}

export interface OdontogramAccountingItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  category?: string;
  toothNumbers?: number[];
  _odontogramKey?: string;
  odontogramSurfaces?: string[];
  odontogramNotes?: string;
  odontogramTreatmentCode?: string;
}

export function odontogramTreatmentKey(toothNumber: number, treatmentId: string | number): string {
  return `${toothNumber}::${treatmentId}`;
}

function itemFromSelection(
  selection: OdontogramTreatmentSelection,
  id: number,
): OdontogramAccountingItem {
  return {
    id,
    description: selection.name,
    dent: selection.dent ?? String(selection.toothNumber),
    price: Number(selection.price) || 0,
    category: selection.category,
    toothNumbers: [selection.toothNumber],
    _odontogramKey: odontogramTreatmentKey(selection.toothNumber, selection.treatmentId),
    odontogramSurfaces: [...new Set(selection.surfaces || [])],
    odontogramNotes: selection.notes || '',
    odontogramTreatmentCode: selection.treatmentCode || 'ACT',
  };
}

export function mergeOdontogramSelections(
  currentItems: OdontogramAccountingItem[],
  selections: OdontogramTreatmentSelection[],
  idFactory: () => number = () => Date.now() + Math.random(),
): OdontogramAccountingItem[] {
  const activeKeys = new Set(
    selections.map(selection => odontogramTreatmentKey(selection.toothNumber, selection.treatmentId)),
  );

  const manualItems = currentItems.filter(item => !item._odontogramKey);
  const existingOdontogramItems = currentItems.filter(
    item => item._odontogramKey && activeKeys.has(item._odontogramKey),
  );
  const existingKeys = new Set(existingOdontogramItems.map(item => item._odontogramKey));

  const missingItems = selections
    .filter(selection => !existingKeys.has(odontogramTreatmentKey(selection.toothNumber, selection.treatmentId)))
    .map(selection => itemFromSelection(selection, idFactory()));

  return [...manualItems, ...existingOdontogramItems, ...missingItems];
}

export function replaceOdontogramToothSelections(
  currentItems: OdontogramAccountingItem[],
  toothNumber: number,
  selections: OdontogramTreatmentSelection[],
  idFactory: () => number = () => Date.now() + Math.random(),
): OdontogramAccountingItem[] {
  const prefix = `${toothNumber}::`;
  const existingForTooth = new Map(
    currentItems
      .filter(item => item._odontogramKey?.startsWith(prefix))
      .map(item => [item._odontogramKey as string, item]),
  );
  const preserved = currentItems.filter(item => !item._odontogramKey?.startsWith(prefix));

  const replacements = selections.map(selection => {
    const normalizedSelection = { ...selection, toothNumber };
    const key = odontogramTreatmentKey(toothNumber, normalizedSelection.treatmentId);
    const existing = existingForTooth.get(key);
    if (existing) {
      return {
        ...existing,
        description: normalizedSelection.name,
        dent: normalizedSelection.dent ?? String(toothNumber),
        price: Number(normalizedSelection.price) || 0,
        category: normalizedSelection.category,
        toothNumbers: [toothNumber],
        odontogramSurfaces: [...new Set(normalizedSelection.surfaces || [])],
        odontogramNotes: normalizedSelection.notes || '',
        odontogramTreatmentCode: normalizedSelection.treatmentCode || existing.odontogramTreatmentCode || 'ACT',
      };
    }
    return itemFromSelection(normalizedSelection, idFactory());
  });

  return [...preserved, ...replacements];
}