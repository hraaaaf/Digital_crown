export interface OdontogramTreatmentSelection {
  toothNumber: number;
  treatmentId: string | number;
  name: string;
  price: number;
  category?: string;
}

export interface OdontogramAccountingItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  category?: string;
  toothNumbers?: number[];
  _odontogramKey?: string;
}

export function odontogramTreatmentKey(toothNumber: number, treatmentId: string | number): string {
  return `${toothNumber}::${treatmentId}`;
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
    .map(selection => ({
      id: idFactory(),
      description: selection.name,
      dent: String(selection.toothNumber),
      price: Number(selection.price) || 0,
      category: selection.category,
      toothNumbers: [selection.toothNumber],
      _odontogramKey: odontogramTreatmentKey(selection.toothNumber, selection.treatmentId),
    }));

  return [...manualItems, ...existingOdontogramItems, ...missingItems];
}
