import { describe, expect, it } from 'vitest';
import { arbitrateMedicationSupplement } from './DentalPharmacologySupplement';
import { normalizeMedicationForPatient } from './normalizeMedicationForPatient';
import type { DrugItem } from './Forms/prescriptionTypes';

const drug = (name: string): DrugItem => ({
  id: 1,
  name,
  dosage: '',
  forme: '',
  posologie: '',
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
});

describe('DentalPharmacologySupplement', () => {
  it('provides the sourced nystatin regimen', () => {
    const result = arbitrateMedicationSupplement('NYSTATINE', { ageYears: 35 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.dosage).toBe('100000 UNITÉS/ML');
    expect(result?.regimen?.posology).toContain('4 fois par jour');
  });

  it('uses the aciclovir 6 months to under-2 age band', () => {
    const result = arbitrateMedicationSupplement('ACICLOVIR', { ageYears: 1 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.dosage).toBe('100MG');
  });

  it('uses the aciclovir 2 to 17 age band', () => {
    const result = arbitrateMedicationSupplement('ACICLOVIR', { ageYears: 8 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.dosage).toBe('200MG');
  });

  it('keeps hydrocortisone under 12 review-only', () => {
    const result = arbitrateMedicationSupplement('HYDROCORTISONE', { ageYears: 10 });
    expect(result?.status).toBe('requires_review');
    expect(result?.regimen).toBeNull();
  });

  it('allows the sourced hydrocortisone oromucosal regimen from age 12', () => {
    const result = arbitrateMedicationSupplement('HYDROCORTISONE', { ageYears: 12 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.dosage).toBe('2.5MG');
  });

  it('blocks fluoride toothpaste 2800 ppm before age 10', () => {
    const result = arbitrateMedicationSupplement('FLUORURE DE SODIUM 2800 PPM', { ageYears: 9 });
    expect(result?.status).toBe('requires_review');
  });

  it('allows fluoride toothpaste 2800 ppm from age 10', () => {
    const result = arbitrateMedicationSupplement('FLUORURE DE SODIUM 2800 PPM', { ageYears: 10 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.dosage).toContain('2800 PPM');
  });

  it('blocks fluoride toothpaste 5000 ppm before age 16', () => {
    const result = arbitrateMedicationSupplement('FLUORURE DE SODIUM 5000 PPM', { ageYears: 15 });
    expect(result?.status).toBe('requires_review');
  });

  it('allows fluoride mouthwash 0.05% from age 6', () => {
    const result = arbitrateMedicationSupplement('FLUORURE DE SODIUM 0.05%', { ageYears: 6 });
    expect(result?.status).toBe('applicable');
    expect(result?.regimen?.form).toBe('BAIN DE BOUCHE');
  });

  it('still requires Morocco practitioner confirmation through the canonical normalizer', () => {
    const result = normalizeMedicationForPatient({
      drug: drug('NYSTATINE'),
      source: 'line_autocomplete',
      patient: { ageYears: 35 },
    });
    expect(result.arbitration.status).toBe('applicable');
    expect(result.moroccoDecision.status).toBe('morocco_amm_unverified');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });
});
