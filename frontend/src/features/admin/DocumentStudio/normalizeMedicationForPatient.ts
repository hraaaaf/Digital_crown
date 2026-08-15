import type { DrugItem } from './Forms/prescriptionTypes';
import {
  arbitrateMedication,
  type PatientPharmacologyContext,
  type PharmacologyArbitration,
} from './DentalPharmacologyArbiter';
import { arbitrateMedicationSupplement } from './DentalPharmacologySupplement';
import {
  arbitrateForMorocco,
  type MoroccoMedicationEvidence,
  type MoroccoPolicyDecision,
} from './MoroccoPharmacologyPolicy';

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
  /**
   * Optional Morocco-specific evidence gathered for the actual molecule/
   * presentation. Absence means Morocco status is unverified and therefore
   * automatic adoption is forbidden, even if international support exists.
   */
  moroccoEvidence?: MoroccoMedicationEvidence;
}

export interface MedicationNormalizationResult {
  drug: DrugItem;
  arbitration: PharmacologyArbitration;
  moroccoDecision: MoroccoPolicyDecision;
  changedByEvidence: boolean;
  requiresPractitionerConfirmation: boolean;
  source: MedicationInputSource;
  arbitratedMolecule: string;
}

const canon = (value: string | undefined) => (value || '').trim().toUpperCase().replace(/\s+/g, ' ');

const defaultMoroccoEvidence = (
  molecule: string,
  arbitration: PharmacologyArbitration,
): MoroccoMedicationEvidence => ({
  molecule,
  ammVerified: false,
  moroccoRegimenEvidenceIds: [],
  internationalSupportEvidenceIds: arbitration.evidenceIds,
});

/**
 * R1 canonical medication pipeline.
 *
 * Invariants:
 * 1. Same resolved molecule + same patient context => same evidence arbitration,
 *    regardless of UI entry path.
 * 2. Core and supplementary source-backed dental rules are consumed through
 *    this same normalizer; supplements never bypass Morocco or practitioner gates.
 * 3. Brand-to-DCI resolution is external to this function. Unknown brands are
 *    never guessed here.
 * 4. No paediatric weight is inferred.
 * 5. Evidence-backed values may replace non-explicit preset/habit defaults,
 *    but never explicit practitioner-entered dose/posology.
 * 6. Drug-library values are treated as explicit only when the library UI
 *    actually supplies them.
 * 7. A practitioner override that diverges from the sourced regimen never gets
 *    silently paired with the other half of the sourced regimen.
 * 8. No therapeutic substitution is performed here.
 * 9. Missing/non-applicable evidence fails closed.
 * 10. International guidance may populate a visible support regimen, but it is
 *    never considered automatically adoptable for Morocco unless the Morocco
 *    policy gate explicitly allows it.
 */
export function normalizeMedicationForPatient(
  input: MedicationNormalizationInput,
): MedicationNormalizationResult {
  const arbitratedMolecule = input.moleculeName?.trim() || input.drug.name;
  const arbitration = arbitrateMedicationSupplement(arbitratedMolecule, input.patient)
    ?? arbitrateMedication(arbitratedMolecule, input.patient);
  const regimen = arbitration.regimen;
  const moroccoDecision = arbitrateForMorocco(
    input.moroccoEvidence ?? defaultMoroccoEvidence(arbitratedMolecule, arbitration),
  );

  const practitionerExplicitDosage = input.practitionerExplicitDosage
    ?? (input.source === 'drug_library' && Boolean(input.drug.dosage?.trim()));
  const practitionerExplicitPosology = input.practitionerExplicitPosology
    ?? (input.source === 'drug_library' && Boolean(input.drug.posologie?.trim()));

  if (input.drug.type === 'EXAMEN') {
    return {
      drug: { ...input.drug },
      arbitration,
      moroccoDecision,
      changedByEvidence: false,
      requiresPractitionerConfirmation: false,
      source: input.source,
      arbitratedMolecule,
    };
  }

  if (!regimen || arbitration.status !== 'applicable') {
    const next: DrugItem = { ...input.drug };
    let changedByEvidence = false;

    if (!practitionerExplicitDosage && next.dosage) {
      next.dosage = '';
      changedByEvidence = true;
    }
    if (!practitionerExplicitPosology && next.posologie) {
      next.posologie = '';
      changedByEvidence = true;
    }

    return {
      drug: next,
      arbitration,
      moroccoDecision,
      changedByEvidence,
      requiresPractitionerConfirmation: true,
      source: input.source,
      arbitratedMolecule,
    };
  }

  const next: DrugItem = { ...input.drug };
  let changedByEvidence = false;
  let requiresPractitionerConfirmation = !moroccoDecision.mayAutoProposeRegimen;

  const explicitDosageDiffers = Boolean(
    practitionerExplicitDosage && canon(next.dosage) !== canon(regimen.dosage),
  );
  const explicitPosologyDiffers = Boolean(
    practitionerExplicitPosology && canon(next.posologie) !== canon(regimen.posology),
  );

  if (explicitDosageDiffers || explicitPosologyDiffers) {
    requiresPractitionerConfirmation = true;

    if (explicitDosageDiffers && !practitionerExplicitPosology && next.posologie) {
      next.posologie = '';
      changedByEvidence = true;
    }
    if (explicitPosologyDiffers && !practitionerExplicitDosage && next.dosage) {
      next.dosage = '';
      changedByEvidence = true;
    }
  } else {
    if (!practitionerExplicitDosage && next.dosage !== regimen.dosage) {
      next.dosage = regimen.dosage;
      changedByEvidence = true;
    }

    if (!practitionerExplicitPosology && next.posologie !== regimen.posology) {
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
    moroccoDecision,
    changedByEvidence,
    requiresPractitionerConfirmation,
    source: input.source,
    arbitratedMolecule,
  };
}
