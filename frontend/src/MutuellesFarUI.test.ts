import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('Mutuelles FAR UI contract', () => {
  it('exposes FAR from the same canonical NOTE insurance action', () => {
    const documents = read('./features/patients/PatientDocuments.tsx');
    const action = read('./features/patients/CnssInsuranceAction.tsx');
    expect(documents).toContain("doc.type.toUpperCase() === 'NOTE'");
    expect(documents).toContain('<CnssInsuranceAction');
    expect(action).toContain('data-insurance-action="prepare-far"');
    expect(action).toContain("handlePrepare('FAR')");
    expect(action).toContain('<FarInsuranceSubmissionReview');
  });

  it('matches the FAR fail-closed administrative contract', () => {
    const source = read('./features/patients/FarInsuranceSubmissionReview.tsx');
    for (const field of [
      'insured_national_id',
      'insured_account_number',
      'insured_phone',
      'insured_full_name',
      'insured_grade',
      'insured_unit',
      'insured_address',
      'beneficiary_full_name',
      'beneficiary_birth_date',
      'relationship_to_insured',
      'claim_context',
      'practitioner_inpe',
    ]) {
      expect(source).toContain(`'${field}'`);
      expect(source).toContain(`data-far-field="${field}"`);
    }
    expect(source).toContain('ne sont jamais déduits automatiquement');
    expect(source).toContain('Maximum 6 lignes dentaires');
  });

  it('keeps the prescription a separate fail-closed role', () => {
    const source = read('./features/patients/FarInsuranceSubmissionReview.tsx');
    expect(source).toContain('Ordonnance — sous-document indépendant');
    expect(source).toContain('Aucune molécule, dose, posologie, durée ou fréquence n’est déduite');
    expect(source).toContain('source_ordonnance_document_id');
    expect(source).toContain('validation séparée requise');
  });

  it('carries FAR-specific explicit fields in the shared frontend type', () => {
    const source = read('./features/patients/InsuranceSubmissionTypes.ts');
    expect(source).toContain("export type InsuranceClaimContext = 'MALADIE' | 'MATERNITE' | 'ACCIDENT'");
    expect(source).toContain('insured_account_number?: string | null');
    expect(source).toContain('insured_phone?: string | null');
    expect(source).toContain('insured_grade?: string | null');
    expect(source).toContain('insured_unit?: string | null');
    expect(source).toContain('source_ordonnance_document_id?: number | null');
  });
});
