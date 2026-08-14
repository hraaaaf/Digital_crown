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
   * True only when the practitioner explicitly entered a dose/posology.
   * Explicit practitioner input is preserved and never silently overwritten.
   */
  practitionerExplicitDosage?: boolean;
  practitionerExplicitPosology?: boolean;
}

export interface MedicationNormalizationResult {
  drug: DrugItem;
  arbitration: PharmacologyArbitration;
  changedByEvidence: boolean;
  requiresPractitionerConfirmation: boolean;
  source: MedicationInputSource;
}

/**
 * R1 canonical medication pipeline.
 *
 * Invariants:
 * 1. Same molecule + same patient context => same evidence arbitration,
 *    regardless of UI entry path.
 * 2. No paediatric weight is inferred.
 * 3. Evidence-backed values may replace non-explicit preset/habit defaults,
 *    but never explicit practitioner-entered dose/posology.
 * 4. No therapeutic substitution is performed here.
 * 5. Missing evidence fails closed to practitioner confirmation.
 */
export function normalizeMedicationForPatient(
  input: MedicationNormalizationInput,
): MedicationNormalizationResult {
  const arbitration = arbitrateMedication(input.drug.name, input.patient);
  const regimen = arbitration.regimen;

  if (input.drug.type === 'EXAMEN' || !regimen || arbitration.status !== 'applicable') {
    return {
      drug: { ...input.drug },
      arbitration,
      changedByEvidence: false,
      requiresPractitionerConfirmation: input.drug.type !== 'EXAMEN',
      source: input.source,
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
  };
}
