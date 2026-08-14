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
 * 5. No therapeutic substitution is performed here.
 * 6. Missing/non-applicable evidence fails closed: automatic legacy dose and
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

  if (!input.practitionerExplicitDosage && next.dosage !== regimen.dosage) {
    next.dosage = regimen.dosage;
    changedByEvidence = true;
  }

  if (!input.practitionerExplicitPosology && next.posologie !== regimen.posology) {
    next.posologie = regimen.posology;
    changedByEvidence = true;
  }

  if (!next.forme?.trim() && regimen.form) {
    next.forme = regimen.form;
    changedByEvidence = true;
  }

  return {
    drug: next,
    arbitration,
    changedByEvidence,
    requiresPractitionerConfirmation: false,
    source: input.source,
    arbitratedMolecule,
  };
}
