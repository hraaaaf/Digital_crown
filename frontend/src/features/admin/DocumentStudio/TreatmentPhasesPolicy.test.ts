import { describe, expect, it } from 'vitest';
import {
  NEUTRAL_CLINICAL_REASSESSMENT_LABEL,
  neutralizeTreatmentPhaseDescription,
  neutralizeTreatmentPhaseItems,
} from './TreatmentPhasesPolicy';

describe('TreatmentPhasesPolicy', () => {
  it('supprime la durée de cicatrisation non sourcée du séquençage legacy', () => {
    const result = neutralizeTreatmentPhaseDescription(
      '--- DÉLAI DE CICATRISATION (ESTIMÉ : 3 MOIS) ---',
    );

    expect(result).toBe(NEUTRAL_CLINICAL_REASSESSMENT_LABEL);
    expect(result).not.toMatch(/\b\d+\s*(mois|semaines?|jours?)\b/i);
  });

  it('laisse les autres phases intactes', () => {
    expect(neutralizeTreatmentPhaseDescription('--- PHASE 3 : PROTHÉTIQUE ---')).toBe(
      '--- PHASE 3 : PROTHÉTIQUE ---',
    );
  });

  it('ne recrée un tableau que si une phase doit être neutralisée', () => {
    const safe = [{ description: '--- PHASE 1 : ASSAINISSEMENT ---' }];
    expect(neutralizeTreatmentPhaseItems(safe)).toBe(safe);

    const unsafe = [{ description: '--- DÉLAI DE CICATRISATION (ESTIMÉ : 3 MOIS) ---' }];
    expect(neutralizeTreatmentPhaseItems(unsafe)).toEqual([
      { description: NEUTRAL_CLINICAL_REASSESSMENT_LABEL },
    ]);
  });
});
