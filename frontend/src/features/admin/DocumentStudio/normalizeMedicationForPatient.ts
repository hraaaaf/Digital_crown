import type { DrugItem } from './Forms/prescriptionTypes';
import {
  arbitrateMedication,
  type PatientPharmacologyContext,
  type PharmacologyArbitration,
} from './DentalPharmacologyArbiter';

export type MedicationInputSource =
  | 'quick_entry'
  | 'line_autocomplete'
  | 'system_protocol'
  | 'user_protocol'
  | 'drug_library'
  | 'assessment';

export interface MedicationNormalizationInput {
  drug: DrugItem;
  source: MedicationInputSource;
  patient: PatientPharmacologyContext;
  /**
   * DCI / substance active resolved from a trusted medication dictionary.
   * If absent, the displayed drug name is used and unknown brands fail closed.
   */
  moleculeName?: string | null;
  /** True only when the practitioner explicitly entered the value. */
  practitionerExplicitDosage?: boolean;
  practitionerExplicitPosology?: boolean;
}

export interface MedicationNormalizationResult {
  drug: DrugItem;
  arbitration: PharmacologyArbitration;
  changedByEvidence: boolean;
  requiresPractitionerConfirmation: boolean;
  source: MedicationInputSource;
  arbitratedMolecule: string;
}

const canon = (value: string | undefined) => (value || '').trim().toUpperCase().replace(/\s+/g, ' ');

/**
 * R1 canonical medication pipeline.
 *
 * Invariants:
 * 1. Same resolved molecule + same patient context => same evidence arbitration,
 *    regardless of UI entry path.
 * 2. Brand-to-DCI resolution is external to this function. Unknown brands are
 *    never guessed here.
 * 3. No paediatric weight is inferred.
 * 4. Evidence-backed values may replace non-explicit preset/habit defaults,
 *    but never explicit practitioner-entered dose/posology.
 * 5. A practitioner override that diverges from the sourced regimen never gets
 *    silently paired with the other half of the sourced regimen.
 * 6. No therapeutic substitution is performed here.
 * 7. Missing/non-applicable evidence fails closed: automatic legacy dose and
 *    posology are cleared, while explicit practitioner input is preserved for
 *    visible/manual review.
 */
export function normalizeMedicationForPatient(
  input: MedicationNormalizationInput,
): MedicationNormalizationResult {
  const arbitratedMolecule = input.moleculeName?.trim() || input.drug.name;
  const arbitration = arbitrateMedication(arbitratedMolecule, input.patient);
  const regimen = arbitration.regimen;

  if (input.drug.type === 'EXAMEN') {
    return {
      drug: { ...input.drug },
      arbitration,
      changedByEvidence: false,
      requiresPractitionerConfirmation: false,
      source: input.source,
      arbitratedMolecule,
    };
  }

  if (!regimen || arbitration.status !== 'applicable') {
    const next: DrugItem = { ...input.drug };
    let changedByEvidence = false;

    if (!input.practitionerExplicitDosage && next.dosage) {
      next.dosage = '';
      changedByEvidence = true;
    }
    if (!input.practitionerExplicitPosology && next.posologie) {
      next.posologie = '';
      changedByEvidence = true;
    }

    return {
      drug: next,
      arbitration,
      changedByEvidence,
      requiresPractitionerConfirmation: true,
      source: input.source,
      arbitratedMolecule,
    };
  }

  const next: DrugItem = { ...input.drug };
  let changedByEvidence = false;
  let requiresPractitionerConfirmation = false;

  const explicitDosageDiffers = Boolean(
    input.practitionerExplicitDosage && canon(next.dosage) !== canon(regimen.dosage),
  );
  const explicitPosologyDiffers = Boolean(
    input.practitionerExplicitPosology && canon(next.posologie) !== canon(regimen.posology),
  );

  if (explicitDosageDiffers || explicitPosologyDiffers) {
    requiresPractitionerConfirmation = true;

    // Do not construct a hybrid regimen by pairing an explicit override with
    // the untouched half of a different evidence regimen.
    if (explicitDosageDiffers && !input.practitionerExplicitPosology && next.posologie) {
      next.posologie = '';
      changedByEvidence = true;
    }
    if (explicitPosologyDiffers && !input.practitionerExplicitDosage && next.dosage) {
      next.dosage = '';
      changedByEvidence = true;
    }
  } else {
    if (!input.practitionerExplicitDosage && next.dosage !== regimen.dosage) {
      next.dosage = regimen.dosage;
      changedByEvidence = true;
    }

    if (!input.practitionerExplicitPosology && next.posologie !== regimen.posology) {
      next.posologie = regimen.posology;
      changedByEvidence = true;
    }
  }

  if (!next.forme?.trim() && regimen.form) {
    next.forme = regimen.form;
    changedByEvidence = true;
  }

  return {
    drug: next,
    arbitration,
    changedByEvidence,
    requiresPractitionerConfirmation,
    source: input.source,
    arbitratedMolecule,
  };
}
