import { describe, expect, it } from 'vitest';
import type { DrugItem } from './Forms/prescriptionTypes';
import { normalizeMedicationForPatient } from './normalizeMedicationForPatient';

const baseDrug = (dosage = '', posologie = ''): DrugItem => ({
  id: 1,
  name: 'AMOXICILLINE',
  dosage,
  forme: 'GÉLULES OU SUSPENSION ORALE',
  posologie,
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
});

describe('severe dental abscess — amoxicillin age/weight safety', () => {
  it('does not change the existing age-band regimen when severe infection is not explicitly set', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 7, weightKg: 20 },
      dentalAbscessContext: { severeInfection: false },
    });

    expect(result.arbitration.status).toBe('applicable');
    expect(result.drug.dosage).toBe('500MG');
    expect(result.drug.posologie).toBe('500MG 3 fois par jour');
  });

  it('requires a real weight for severe infection between 6 months and 11 years', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 7 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_weight');
    expect(result.arbitration.regimen).toBeNull();
    expect(result.arbitration.messages.join(' ')).toContain('poids réel requis');
    expect(result.drug.dosage).toBe('');
    expect(result.drug.posologie).toBe('');
  });

  it('computes only the source-backed ceiling and does not auto-select a severe paediatric dose', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 7, weightKg: 20 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_review');
    expect(result.arbitration.regimen).toBeNull();
    expect(result.arbitration.messages.join(' ')).toContain('30 mg/kg');
    expect(result.arbitration.messages.join(' ')).toContain('600 mg par prise');
    expect(result.drug.dosage).toBe('');
    expect(result.drug.posologie).toBe('');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('caps the severe paediatric ceiling at 1 g per dose', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 11, weightKg: 50 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_review');
    expect(result.arbitration.messages.join(' ')).toContain('1000 mg par prise');
    expect(result.arbitration.regimen).toBeNull();
  });

  it('requires weight in a severe adolescent before reconciling age-based SDCEP and weight-based SmPC guidance', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 13 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_weight');
    expect(result.arbitration.regimen).toBeNull();
    expect(result.arbitration.messages.join(' ')).toContain('adolescent');
  });

  it('fails closed for a severe adolescent even when weight is known', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 13, weightKg: 35 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_review');
    expect(result.arbitration.regimen).toBeNull();
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('preserves an explicit practitioner regimen even when severe-infection safety requires review', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('500MG', '500 mg 3 fois par jour'),
      source: 'quick_entry',
      patient: { ageYears: 7, weightKg: 20 },
      dentalAbscessContext: { severeInfection: true },
      practitionerExplicitDosage: true,
      practitionerExplicitPosology: true,
    });

    expect(result.arbitration.status).toBe('requires_review');
    expect(result.drug.dosage).toBe('500MG');
    expect(result.drug.posologie).toBe('500 mg 3 fois par jour');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('does not auto-select a severe adult regimen from an international range', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug(),
      source: 'line_autocomplete',
      patient: { ageYears: 35, weightKg: 70 },
      dentalAbscessContext: { severeInfection: true },
    });

    expect(result.arbitration.status).toBe('requires_review');
    expect(result.arbitration.regimen).toBeNull();
    expect(result.drug.dosage).toBe('');
    expect(result.drug.posologie).toBe('');
  });
});
