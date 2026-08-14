import { describe, expect, it } from 'vitest';
import { buildPatientPharmacologyContext, pharmacologyReviewMessage } from './PrescriptionPharmacologyPipeline';
import { normalizeMedicationForPatient } from './normalizeMedicationForPatient';
import type { DrugItem } from './Forms/prescriptionTypes';

const drug = (name: string): DrugItem => ({
  id: 1,
  name,
  dosage: '',
  forme: 'COMPRIMÉS',
  posologie: '',
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
});

describe('PrescriptionPharmacologyPipeline — structured context', () => {
  it('does not infer an allergy from free-text antecedents', () => {
    const context = buildPatientPharmacologyContext({
      age: 42,
      patient_context: { antecedents: 'allergie pénicilline signalée dans le texte libre' },
    });
    expect(context.ageYears).toBe(42);
    expect(context.allergies).toEqual([]);
  });

  it('uses only explicit structured allergy fields', () => {
    const context = buildPatientPharmacologyContext({
      age: 42,
      patient_context: {
        antecedents: 'texte libre quelconque',
        allergies: ['Pénicilline'],
      },
    });
    expect(context.allergies).toEqual(['Pénicilline']);
  });

  it('never fabricates missing paediatric weight', () => {
    const context = buildPatientPharmacologyContext({ age: 8 });
    expect(context.ageYears).toBe(8);
    expect(context.weightKg).toBeNull();
  });
});

describe('PrescriptionPharmacologyPipeline — Morocco-first review', () => {
  it('keeps an international-support regimen visible but practitioner-review required when Morocco evidence is absent', () => {
    const result = normalizeMedicationForPatient({
      drug: drug('AMOXICILLINE'),
      source: 'line_autocomplete',
      patient: { ageYears: 30 },
    });
    expect(result.arbitration.status).toBe('applicable');
    expect(result.drug.dosage).not.toBe('');
    expect(result.moroccoDecision.status).toBe('morocco_amm_unverified');
    expect(result.requiresPractitionerConfirmation).toBe(true);
    expect(pharmacologyReviewMessage(result)).toContain('Maroc');
  });

  it('allows automatic adoption only when the explicit Morocco gate passes', () => {
    const result = normalizeMedicationForPatient({
      drug: drug('PARACETAMOL'),
      source: 'line_autocomplete',
      patient: { ageYears: 30 },
      moroccoEvidence: {
        molecule: 'PARACETAMOL',
        ammVerified: true,
        ammEvidenceId: 'MOROCCO_AMMPS_MEDICINES',
        moroccoRegimenEvidenceIds: ['MOROCCO_PARACETAMOL'],
        internationalSupportEvidenceIds: ['SDCEP_PARACETAMOL'],
      },
    });
    expect(result.moroccoDecision.status).toBe('morocco_verified');
    expect(result.requiresPractitionerConfirmation).toBe(false);
  });
});
