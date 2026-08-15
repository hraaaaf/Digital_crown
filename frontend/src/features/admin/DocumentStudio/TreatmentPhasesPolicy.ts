export const NEUTRAL_CLINICAL_REASSESSMENT_LABEL =
  '--- CONTRÔLE CLINIQUE AVANT POURSUITE PROTHÉTIQUE ---';

const HEALING_DELAY_PATTERN = /d[ée]lai de cicatrisation/i;

export function neutralizeTreatmentPhaseDescription(description: string): string {
  if (!HEALING_DELAY_PATTERN.test(description)) return description;
  return NEUTRAL_CLINICAL_REASSESSMENT_LABEL;
}

export function neutralizeTreatmentPhaseItems<T extends { description: string }>(items: T[]): T[] {
  let changed = false;
  const next = items.map(item => {
    const description = neutralizeTreatmentPhaseDescription(item.description);
    if (description === item.description) return item;
    changed = true;
    return { ...item, description };
  });

  return changed ? next : items;
}
