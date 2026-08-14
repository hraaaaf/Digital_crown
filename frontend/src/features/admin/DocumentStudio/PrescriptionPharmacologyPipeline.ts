import { api } from '../../../services/api';
import type { DrugItem } from './Forms/prescriptionTypes';
import type { PatientPharmacologyContext } from './DentalPharmacologyArbiter';
import {
  normalizeMedicationForPatient,
  type MedicationInputSource,
  type MedicationNormalizationResult,
} from './normalizeMedicationForPatient';

export interface PractitionerExplicitFields {
  dosage?: boolean;
  posology?: boolean;
}

const asNumber = (value: unknown): number | null => {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) && n > 0 ? n : null;
};

const asOptionalBoolean = (value: unknown): boolean | null =>
  typeof value === 'boolean' ? value : null;

const asString = (value: unknown): string | null =>
  typeof value === 'string' && value.trim() ? value.trim() : null;

const asStringArray = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.filter(v => typeof v === 'string' && v.trim()).map(v => v.trim());
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
};

/**
 * Build pharmacology context only from explicit structured fields.
 * Free-text antecedents are deliberately not converted into allergies,
 * pregnancy, renal/hepatic disease, etc. R1 does not infer clinical facts.
 */
export function buildPatientPharmacologyContext(assessment: any): PatientPharmacologyContext {
  const patient = assessment?.patient_context || {};
  const ageYears = asNumber(assessment?.age ?? patient?.age);
  const weightKg = asNumber(assessment?.weight ?? assessment?.poids ?? patient?.weight ?? patient?.poids);

  return {
    ageYears,
    weightKg,
    pregnancy: asOptionalBoolean(assessment?.pregnancy ?? patient?.pregnancy),
    breastfeeding: asOptionalBoolean(assessment?.breastfeeding ?? patient?.breastfeeding),
    renalImpairment: asOptionalBoolean(assessment?.renal_impairment ?? patient?.renal_impairment),
    hepaticImpairment: asOptionalBoolean(assessment?.hepatic_impairment ?? patient?.hepatic_impairment),
    anticoagulant: asString(assessment?.anticoagulant ?? patient?.anticoagulant),
    antiplatelet: asString(assessment?.antiplatelet ?? patient?.antiplatelet),
    allergies: [
      ...asStringArray(assessment?.allergies),
      ...asStringArray(patient?.allergies),
    ],
  };
}

/**
 * Resolve a commercial name to its DCI/substance using Digital Crown's local
 * medication dictionary. This is identity resolution only; it is NOT treated
 * as proof of current Moroccan AMM/commercialisation status.
 */
export async function resolveMedicationDci(
  name: string,
  dosage?: string,
): Promise<{ dci: string | null; dictionaryResult: any | null }> {
  if (!name.trim()) return { dci: null, dictionaryResult: null };
  try {
    const res = await api.get('/medications/validate', {
      params: { name, dosage: dosage || undefined },
    });
    const dci = typeof res.data?.dci === 'string' && res.data.dci.trim()
      ? res.data.dci.trim()
      : null;
    return { dci, dictionaryResult: res.data ?? null };
  } catch {
    return { dci: null, dictionaryResult: null };
  }
}

export async function resolveAndNormalizeMedication(args: {
  drug: DrugItem;
  source: MedicationInputSource;
  assessment: any;
  practitionerExplicit?: PractitionerExplicitFields;
}): Promise<MedicationNormalizationResult & { dictionaryResult: any | null }> {
  if (args.drug.type === 'EXAMEN') {
    const result = normalizeMedicationForPatient({
      drug: args.drug,
      source: args.source,
      patient: buildPatientPharmacologyContext(args.assessment),
    });
    return { ...result, dictionaryResult: null };
  }

  const { dci, dictionaryResult } = await resolveMedicationDci(args.drug.name, args.drug.dosage);
  const result = normalizeMedicationForPatient({
    drug: args.drug,
    source: args.source,
    patient: buildPatientPharmacologyContext(args.assessment),
    moleculeName: dci,
    practitionerExplicitDosage: args.practitionerExplicit?.dosage,
    practitionerExplicitPosology: args.practitionerExplicit?.posology,
  });

  return { ...result, dictionaryResult };
}

export function pharmacologyReviewMessage(result: MedicationNormalizationResult): string | null {
  if (!result.requiresPractitionerConfirmation) return null;
  const details = [
    ...result.arbitration.messages,
    ...result.moroccoDecision.messages,
  ].filter(Boolean);
  if (details.length > 0) return [...new Set(details)].join(' ');
  return 'Revue pharmacologique requise avant validation de cette ligne.';
}
