import { describe, expect, it } from 'vitest';
import { arbitrateDentalAbscessAntibioticIndication, arbitrateMedication } from './DentalPharmacologyArbiter';
import { normalizeMedicationForPatient } from './normalizeMedicationForPatient';
import type { DrugItem } from './Forms/prescriptionTypes';

const baseDrug = (name: string, dosage = '', posologie = ''): DrugItem => ({
  id: 1,
  name,
  dosage,
  forme: 'COMPRIMÉS',
  posologie,
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
});

describe('DentalPharmacologyArbiter — evidence rules', () => {
  it('does not infer paediatric weight', () => {
    const result = arbitrateMedication('CLARITHROMYCINE', { ageYears: 7 });
    expect(result.status).toBe('requires_weight');
    expect(result.regimen).toBeNull();
  });

  it('uses the SDCEP age band for paediatric amoxicillin', () => {
    const result = arbitrateMedication('AMOXICILLINE', { ageYears: 4, weightKg: 16 });
    expect(result.status).toBe('applicable');
    expect(result.regimen?.dosage).toBe('250MG');
    expect(result.regimen?.posology).toBe('250MG 3 fois par jour');
  });

  it('does not auto-propose co-amoxiclav for dental abscess R1', () => {
    const result = arbitrateMedication('AMOXICILLINE + ACIDE CLAVULANIQUE', { ageYears: 40 });
    expect(result.status).toBe('requires_review');
    expect(result.regimen).toBeNull();
  });

  it('blocks automatic penicillin proposal when an immediate penicillin allergy is present', () => {
    const result = arbitrateMedication('AMOXICILLINE', {
      ageYears: 35,
      allergies: ['allergie pénicilline'],
    });
    expect(result.status).toBe('not_recommended_for_context');
    expect(result.regimen).toBeNull();
  });

  it('does not propose antibiotics for a controlled local abscess without spreading/systemic signs', () => {
    const result = arbitrateDentalAbscessAntibioticIndication({
      localMeasuresAttempted: true,
      localMeasuresEffective: true,
      spreadingInfection: false,
      systemicInvolvement: false,
      highRiskComplications: false,
    });
    expect(result.status).toBe('not_recommended_for_context');
  });
});

describe('normalizeMedicationForPatient — R1 cross-path invariants', () => {
  it('returns the same evidence dose for quick entry and line autocomplete', () => {
    const quick = normalizeMedicationForPatient({
      drug: baseDrug('AMOXICILLINE', '1G', 'adulte preset'),
      source: 'quick_entry',
      patient: { ageYears: 4, weightKg: 16 },
    });
    const line = normalizeMedicationForPatient({
      drug: baseDrug('AMOXICILLINE'),
      source: 'line_autocomplete',
      patient: { ageYears: 4, weightKg: 16 },
    });
    expect(quick.drug.dosage).toBe('250MG');
    expect(quick.drug.posologie).toBe('250MG 3 fois par jour');
    expect(line.drug.dosage).toBe(quick.drug.dosage);
    expect(line.drug.posologie).toBe(quick.drug.posologie);
  });

  it('uses a trusted resolved DCI for a commercial brand without renaming the displayed drug', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('CLAMOXYL'),
      moleculeName: 'AMOXICILLINE',
      source: 'quick_entry',
      patient: { ageYears: 4, weightKg: 16 },
    });
    expect(result.drug.name).toBe('CLAMOXYL');
    expect(result.arbitratedMolecule).toBe('AMOXICILLINE');
    expect(result.drug.dosage).toBe('250MG');
    expect(result.drug.posologie).toBe('250MG 3 fois par jour');
  });

  it('never guesses an unknown brand-to-DCI mapping', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('MARQUE_INCONNUE', '1G', 'ancien preset'),
      source: 'quick_entry',
      patient: { ageYears: 30 },
    });
    expect(result.arbitration.status).toBe('no_evidence');
    expect(result.drug.dosage).toBe('');
    expect(result.drug.posologie).toBe('');
  });

  it('preserves an explicit practitioner dosage and posology', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('AMOXICILLINE', '375MG', 'schéma explicitement saisi'),
      source: 'quick_entry',
      patient: { ageYears: 4, weightKg: 16 },
      practitionerExplicitDosage: true,
      practitionerExplicitPosology: true,
    });
    expect(result.drug.dosage).toBe('375MG');
    expect(result.drug.posologie).toBe('schéma explicitement saisi');
    expect(result.arbitration.regimen?.dosage).toBe('250MG');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('does not build a hybrid regimen after a partial explicit override', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('AMOXICILLINE', '1G', 'ancien preset automatique'),
      source: 'quick_entry',
      patient: { ageYears: 40 },
      practitionerExplicitDosage: true,
      practitionerExplicitPosology: false,
    });
    expect(result.drug.dosage).toBe('1G');
    expect(result.drug.posologie).toBe('');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('treats non-empty drug-library therapeutic fields as practitioner-explicit', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('AMOXICILLINE', '1G', '1 g matin et soir'),
      source: 'drug_library',
      patient: { ageYears: 40 },
    });
    expect(result.drug.dosage).toBe('1G');
    expect(result.drug.posologie).toBe('1 g matin et soir');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('clears unsupported automatic legacy dose and posology', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('MOLECULE_INCONNUE', '1G', 'ancien preset automatique'),
      source: 'system_protocol',
      patient: { ageYears: 30 },
    });
    expect(result.arbitration.status).toBe('no_evidence');
    expect(result.drug.dosage).toBe('');
    expect(result.drug.posologie).toBe('');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('preserves explicit practitioner values even when evidence is missing', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('MOLECULE_INCONNUE', '500MG', 'schéma praticien'),
      source: 'quick_entry',
      patient: { ageYears: 30 },
      practitionerExplicitDosage: true,
      practitionerExplicitPosology: true,
    });
    expect(result.drug.dosage).toBe('500MG');
    expect(result.drug.posologie).toBe('schéma praticien');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });

  it('fails closed when no sourced dental rule exists', () => {
    const result = normalizeMedicationForPatient({
      drug: baseDrug('MOLECULE_INCONNUE'),
      source: 'drug_library',
      patient: { ageYears: 30 },
    });
    expect(result.arbitration.status).toBe('no_evidence');
    expect(result.requiresPractitionerConfirmation).toBe(true);
  });
});
