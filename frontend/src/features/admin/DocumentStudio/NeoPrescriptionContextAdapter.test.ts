import { describe, expect, it } from 'vitest';
import {
  adaptNeoContextToPharmacology,
  neoContextHasUnresolvedMedicationIdentity,
} from './NeoPrescriptionContextAdapter';

describe('NeoPrescriptionContextAdapter', () => {
  it('maps only structured facts and preserves UNKNOWN as null', () => {
    expect(adaptNeoContextToPharmacology({
      weight_kg: 24,
      medication_allergy_status: 'UNKNOWN',
      penicillin_allergy_status: 'UNKNOWN',
      renal_context_status: 'UNKNOWN',
      hepatic_context_status: 'UNKNOWN',
      pregnancy_status: 'UNKNOWN',
      breastfeeding_status: 'UNKNOWN',
    }, 8)).toEqual({
      ageYears: 8,
      weightKg: 24,
      pregnancy: null,
      breastfeeding: null,
      renalImpairment: null,
      hepaticImpairment: null,
      anticoagulant: null,
      antiplatelet: null,
      allergies: [],
    });
  });

  it('maps explicit patient facts without free-text inference', () => {
    const mapped = adaptNeoContextToPharmacology({
      medication_allergy_status: 'PRESENT',
      medication_allergies: ['Latex', 'Drug X'],
      penicillin_allergy_status: 'PRESENT',
      renal_context_status: 'NO_KNOWN_IMPAIRMENT',
      hepatic_context_status: 'IMPAIRMENT_REPORTED',
      pregnancy_status: 'NO',
      breastfeeding_status: 'YES',
      current_medications_status: 'PRESENT',
      current_medications: ['Xarelto 20 mg'],
    }, 35);

    expect(mapped.allergies).toEqual(['Latex', 'Drug X', 'PENICILLIN_REPORTED']);
    expect(mapped.renalImpairment).toBe(false);
    expect(mapped.hepaticImpairment).toBe(true);
    expect(mapped.pregnancy).toBe(false);
    expect(mapped.breastfeeding).toBe(true);
    expect(mapped.anticoagulant).toBeNull();
    expect(mapped.antiplatelet).toBeNull();
    expect(neoContextHasUnresolvedMedicationIdentity({
      current_medications_status: 'PRESENT',
      current_medications: ['Xarelto 20 mg'],
    })).toBe(true);
  });
});
