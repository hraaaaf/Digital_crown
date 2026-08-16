export type AccountingOdontogramType = 'ADULT' | 'PEDIATRIC';

const ADULT_MAXILLA = [11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28];
const ADULT_MANDIBLE = [31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48];
const PEDIATRIC_MAXILLA = [51, 52, 53, 54, 55, 61, 62, 63, 64, 65];
const PEDIATRIC_MANDIBLE = [71, 72, 73, 74, 75, 81, 82, 83, 84, 85];

const ADULT_GROUPS: Record<string, number[]> = {
  all: [...ADULT_MAXILLA, ...ADULT_MANDIBLE],
  maxillaire: ADULT_MAXILLA,
  mandibule: ADULT_MANDIBLE,
  Q1: [11, 12, 13, 14, 15, 16, 17, 18],
  Q2: [21, 22, 23, 24, 25, 26, 27, 28],
  Q3: [31, 32, 33, 34, 35, 36, 37, 38],
  Q4: [41, 42, 43, 44, 45, 46, 47, 48],
  S1: [14, 15, 16, 17, 18],
  S2: [13, 12, 11, 21, 22, 23],
  S3: [24, 25, 26, 27, 28],
  S4: [34, 35, 36, 37, 38],
  S5: [33, 32, 31, 41, 42, 43],
  S6: [44, 45, 46, 47, 48],
};

const PEDIATRIC_GROUPS: Record<string, number[]> = {
  all: [...PEDIATRIC_MAXILLA, ...PEDIATRIC_MANDIBLE],
  maxillaire: PEDIATRIC_MAXILLA,
  mandibule: PEDIATRIC_MANDIBLE,
  Q5: [51, 52, 53, 54, 55],
  Q6: [61, 62, 63, 64, 65],
  Q7: [71, 72, 73, 74, 75],
  Q8: [81, 82, 83, 84, 85],
};

export function odontogramQuickGroupKeys(type: AccountingOdontogramType): string[] {
  return type === 'PEDIATRIC'
    ? ['Q5', 'Q6', 'Q7', 'Q8']
    : ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6'];
}

export function odontogramGroupSelection(type: AccountingOdontogramType, group: string): number[] {
  if (group === 'none') return [];
  const groups = type === 'PEDIATRIC' ? PEDIATRIC_GROUPS : ADULT_GROUPS;
  return [...(groups[group] || [])];
}

export function isToothCompatibleWithOdontogramType(type: AccountingOdontogramType, toothNumber: number): boolean {
  const all = type === 'PEDIATRIC' ? PEDIATRIC_GROUPS.all : ADULT_GROUPS.all;
  return all.includes(toothNumber);
}
