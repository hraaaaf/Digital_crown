import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('Mutuelles CNOPS UI contract', () => {
  it('exposes CNOPS from the same canonical NOTE insurance action', () => {
    const documents = read('./features/patients/PatientDocuments.tsx');
    const action = read('./features/patients/CnssInsuranceAction.tsx');
    expect(documents).toContain("doc.type.toUpperCase() === 'NOTE'");
    expect(documents).toContain('<CnssInsuranceAction');
    expect(action).toContain('data-insurance-action="prepare-cnops"');
    expect(action).toContain("handlePrepare('CNOPS')");
    expect(action).toContain("'/documents/insurance-submissions/prepare'");
    expect(action).toContain("'/documents/insurance-submissions/validate'");
    expect(action).toContain("'/documents/insurance-submissions/finalize'");
  });

  it('matches the backend CNOPS fail-closed administrative gate', () => {
    const source = read('./features/patients/CnopsInsuranceSubmissionReview.tsx');
    for (const field of [
      'request_nature',
      'insured_full_name',
      'insured_affiliation_number',
      'insured_registration_number',
      'insured_national_id',
      'insured_address',
      'beneficiary_full_name',
      'beneficiary_birth_date',
      'beneficiary_national_id',
      'beneficiary_sex',
      'practitioner_inpe',
      'care_type',
    ]) {
      expect(source).toContain(`'${field}'`);
      expect(source).toContain(`data-cnops-field="${field}"`);
    }
    expect(source).toContain('Digital Crown ne déduit ni affiliation, ni immatriculation, ni identité assuré.');
  });

  it('keeps optional CNOPS form marks explicit and never invents signature or insurer decisions', () => {
    const source = read('./features/patients/CnopsInsuranceSubmissionReview.tsx');
    expect(source).toContain('<option value="CONJOINT">Conjoint</option>');
    expect(source).toContain('<option value="ENFANT">Enfant</option>');
    expect(source).toContain('prior_approval_number');
    expect(source).toContain('accident_date');
    expect(source).not.toContain('signature');
    expect(source).not.toContain('cachet');
    expect(source).not.toContain('decision_assureur');
  });

  it('carries the distinct CNOPS affiliation number in the frontend contract', () => {
    const source = read('./features/patients/InsuranceSubmissionTypes.ts');
    expect(source).toContain('insured_affiliation_number?: string | null');
    expect(source).toContain("export type InsuranceRequestNature = 'EXECUTION' | 'PRIOR_APPROVAL'");
  });
});
