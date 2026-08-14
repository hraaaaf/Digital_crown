// Legacy compatibility facade for Document Studio pharmacology.
//
// R1 deliberately retires the former hand-written dosing/brand table from the
// active Ordonnance decision path. Canonical pharmacology now lives in
// DentalPharmacologyArbiter.ts and brand → DCI identity is resolved through the
// medication dictionary before arbitration.
//
// Keep this module only because a few legacy components/tests still import its
// public symbols. It MUST fail closed rather than recreate old unsourced rules.

import { arbitrateMedication } from './DentalPharmacologyArbiter';

export type DrugCategory =
  | 'Antalgiques'
  | 'AINS'
  | 'Antibiotiques'
  | 'Corticoïdes'
  | 'Antiseptiques'
  | 'Antifongiques';

export interface ClinicalRule {
  molecule: string;
  category: DrugCategory;
  adult_dose: string;
  adult_posology: string;
  pediatric_calc: (weight: number) => { dosage: string; posology: string };
  contraindications: string[];
  available_strengths_mg?: number[];
  max_mg_per_kg_day?: number;
  notes?: string;
}

const CATEGORY_BY_MOLECULE: Record<string, DrugCategory> = {
  PARACETAMOL: 'Antalgiques',
  IBUPROFENE: 'AINS',
  PHENOXYMETHYLPENICILLINE: 'Antibiotiques',
  AMOXICILLINE: 'Antibiotiques',
  METRONIDAZOLE: 'Antibiotiques',
  CLINDAMYCINE: 'Antibiotiques',
  CLARITHROMYCINE: 'Antibiotiques',
  MICONAZOLE: 'Antifongiques',
  FLUCONAZOLE: 'Antifongiques',
  CHLORHEXIDINE: 'Antiseptiques',
  BENZYDAMINE: 'Antalgiques',
};

/**
 * Compatibility inventory only.
 * Adult values are derived from the canonical arbiter at module load.
 * The old weight-only pediatric callback cannot represent current age-banded
 * evidence safely, therefore it fails closed. Use getAgeAwareDosing instead.
 */
export const MOROCCAN_CLINICAL_RULES: Record<string, ClinicalRule> = Object.fromEntries(
  Object.entries(CATEGORY_BY_MOLECULE).map(([molecule, category]) => {
    const adult = arbitrateMedication(molecule, { ageYears: 30 });
    return [molecule, {
      molecule,
      category,
      adult_dose: adult.status === 'applicable' ? adult.regimen?.dosage || '' : '',
      adult_posology: adult.status === 'applicable' ? adult.regimen?.posology || '' : '',
      pediatric_calc: () => ({ dosage: '', posology: '' }),
      contraindications: [],
      notes: 'Legacy compatibility only — canonical rules are in DentalPharmacologyArbiter.',
    } satisfies ClinicalRule];
  }),
);

/**
 * Deprecated: weight alone is not sufficient to select age-banded paediatric
 * regimens. R1 refuses to infer age from weight and returns null.
 */
export function getPediatricGuide(_moleculeName: string, _weight: number) {
  return null;
}

/**
 * No hard-coded brand aliases are allowed in the pharmacology arbiter.
 * Brand identity must be resolved by the medication dictionary / current
 * regulator data. This intentionally removes historical errors such as
 * HEXTRIL → CHLORHEXIDINE (HEXTRIL is hexetidine).
 */
export const BRAND_TO_RULE: Record<string, string> = {};

export function resolveRule(name: string): ClinicalRule | null {
  const upper = (name || '').toUpperCase().trim();
  if (!upper) return null;
  return MOROCCAN_CLINICAL_RULES[upper] || null;
}

/** Missing weight must remain unknown; never synthesize weight from age. */
export function estimateWeightFromAge(_age: number): number {
  return 0;
}

export type ValidationLevel = 'ok' | 'info' | 'warn' | 'danger' | 'unknown';

export interface DrugValidation {
  level: ValidationLevel;
  molecule: string | null;
  messages: string[];
}

export function parseDosageToMg(dosage: string): number | null {
  if (!dosage) return null;
  const m = dosage.toUpperCase().replace(/\s/g, '').match(/(\d+(?:[.,]\d+)?)(MG|G)\b/);
  if (!m) return null;
  const val = parseFloat(m[1].replace(',', '.'));
  return m[2] === 'G' ? val * 1000 : val;
}

/**
 * Legacy inline validator used by DrugRow.
 * It no longer parses free-text antecedents nor uses a second rule table.
 * Canonical per-line review is emitted by the R1 parent pipeline. This facade
 * only exposes arbiter state for exact DCI names and otherwise stays unknown.
 */
export function validatePrescriptionLine(
  name: string,
  _dosage: string,
  age: number | null | undefined,
  _antecedents?: string | null,
): DrugValidation {
  const upper = (name || '').toUpperCase().trim();
  if (!CATEGORY_BY_MOLECULE[upper]) {
    return { level: 'unknown', molecule: null, messages: [] };
  }

  const arbitration = arbitrateMedication(upper, {
    ageYears: typeof age === 'number' && Number.isFinite(age) && age > 0 ? age : null,
  });

  if (arbitration.status === 'applicable') {
    return { level: 'ok', molecule: arbitration.regimen?.molecule || upper, messages: [] };
  }

  const level: ValidationLevel = arbitration.status === 'not_recommended_for_context'
    ? 'danger'
    : 'warn';
  return {
    level,
    molecule: upper,
    messages: arbitration.messages,
  };
}

/**
 * Compatibility entry point now delegated to the canonical evidence arbiter.
 * For children, a real positive weight is mandatory whenever the encoded rule
 * requires it. No age-derived weight or old brand alias is used.
 */
export function getAgeAwareDosing(
  name: string,
  age: number | null | undefined,
  weight?: number | null,
): { dosage: string; posology: string; pediatric: boolean; weight?: number } | null {
  if (typeof age !== 'number' || !Number.isFinite(age) || age <= 0) return null;
  const upper = (name || '').toUpperCase().trim();
  if (!CATEGORY_BY_MOLECULE[upper]) return null;

  const arbitration = arbitrateMedication(upper, {
    ageYears: age,
    weightKg: typeof weight === 'number' && Number.isFinite(weight) && weight > 0 ? weight : null,
  });
  if (arbitration.status !== 'applicable' || !arbitration.regimen) return null;

  return {
    dosage: arbitration.regimen.dosage,
    posology: arbitration.regimen.posology,
    pediatric: Boolean(arbitration.regimen.paediatric),
    ...(typeof weight === 'number' && weight > 0 ? { weight } : {}),
  };
}
