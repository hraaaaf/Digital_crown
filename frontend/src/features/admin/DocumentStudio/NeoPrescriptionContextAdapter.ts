import type { PatientPharmacologyContext } from './DentalPharmacologyArbiter';

export type NeoFactStatus = 'UNKNOWN' | 'NO' | 'YES';
export type NeoAllergyStatus = 'UNKNOWN' | 'NONE_KNOWN' | 'PRESENT';
export type NeoOrganStatus = 'UNKNOWN' | 'NO_KNOWN_IMPAIRMENT' | 'IMPAIRMENT_REPORTED';
export type NeoMedicationStatus = 'UNKNOWN' | 'NONE_REPORTED' | 'PRESENT';

export interface NeoStructuredPrescriptionContext {
  weight_kg?: number | null;
  medication_allergy_status?: NeoAllergyStatus;
  medication_allergies?: string[] | null;
  penicillin_allergy_status?: NeoAllergyStatus;
  renal_context_status?: NeoOrganStatus;
  hepatic_context_status?: NeoOrganStatus;
  pregnancy_status?: NeoFactStatus;
  breastfeeding_status?: NeoFactStatus;
  current_medications_status?: NeoMedicationStatus;
  current_medications?: string[] | null;
}

const triState = (value: NeoFactStatus | undefined): boolean | null => {
  if (value === 'YES') return true;
  if (value === 'NO') return false;
  return null;
};

const impairment = (value: NeoOrganStatus | undefined): boolean | null => {
  if (value === 'IMPAIRMENT_REPORTED') return true;
  if (value === 'NO_KNOWN_IMPAIRMENT') return false;
  return null;
};

export function adaptNeoContextToPharmacology(
  context: NeoStructuredPrescriptionContext | null | undefined,
  ageYears?: number | null,
): PatientPharmacologyContext {
  const source = context || {};
  const allergies = source.medication_allergy_status === 'PRESENT'
    ? (source.medication_allergies || []).filter(item => typeof item === 'string' && item.trim())
    : [];

  if (source.penicillin_allergy_status === 'PRESENT') {
    allergies.push('PENICILLIN_REPORTED');
  }

  return {
    ageYears: typeof ageYears === 'number' && Number.isFinite(ageYears) && ageYears >= 0 ? ageYears : null,
    weightKg: typeof source.weight_kg === 'number' && Number.isFinite(source.weight_kg) && source.weight_kg > 0
      ? source.weight_kg
      : null,
    pregnancy: triState(source.pregnancy_status),
    breastfeeding: triState(source.breastfeeding_status),
    renalImpairment: impairment(source.renal_context_status),
    hepaticImpairment: impairment(source.hepatic_context_status),
    anticoagulant: null,
    antiplatelet: null,
    allergies: [...new Set(allergies)],
  };
}

