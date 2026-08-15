export type QuickActPayer = 'SELF' | 'THIRD_PARTY';

export interface QuickActInput {
  name: string;
  price: number;
  category?: string;
}

const normalize = (value: string) => value.trim().toLocaleLowerCase('fr-FR');

const resolveCanonicalName = (name: string, payer: QuickActPayer): string => {
  const normalized = normalize(name);

  if (/^(composite|composite 1 face|restauration composite)$/.test(normalized)) {
    return payer === 'THIRD_PARTY' ? 'Restauration composite' : 'Composite';
  }

  if (/^(endodontie|traitement endodontique)$/.test(normalized)) {
    return payer === 'THIRD_PARTY' ? 'Traitement endodontique' : 'Endodontie';
  }

  return name.trim();
};

export function normalizeQuickActTerminology<T extends QuickActInput>(
  act: T,
  payer: QuickActPayer = 'SELF',
): T {
  return {
    ...act,
    name: resolveCanonicalName(act.name, payer),
  };
}

export function normalizeQuickActs<T extends QuickActInput>(
  acts: T[],
  payer: QuickActPayer = 'SELF',
): T[] {
  return acts.map(act => normalizeQuickActTerminology(act, payer));
}
