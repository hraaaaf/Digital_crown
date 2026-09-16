import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('Mutuelles CNSS UI contract', () => {
  it('exposes preparation only from canonical NOTE archives', () => {
    const source = read('./features/patients/PatientDocuments.tsx');
    expect(source).toContain("doc.type.toUpperCase() === 'NOTE'");
    expect(source).toContain('canonicalId !== null');
    expect(source).toContain('<CnssInsuranceAction');
    expect(source).toContain('honorairesDocumentId={canonicalId}');
  });

  it('keeps the UI flow on the authenticated insurance facade', () => {
    const source = read('./features/patients/CnssInsuranceAction.tsx');
    expect(source).toContain("'/documents/insurance-submissions/prepare'");
    expect(source).toContain("'/documents/insurance-submissions/validate'");
    expect(source).toContain("'/documents/insurance-submissions/finalize'");
    expect(source).toContain("onClick={() => void handlePrepare('CNSS')}");
    expect(source).toContain("type SupportedOrganization = 'CNSS' | 'CNOPS'");
    expect(source).toContain('result.original_filename');
  });

  it('never exposes upper insured fields in the validated review zone', () => {
    const source = read('./features/patients/CnssInsuranceSubmissionReview.tsx');
    expect(source).toContain('partie supérieure réservée à l’assuré reste volontairement vierge');
    expect(source).not.toContain('data-cnss-field="insured_');
    expect(source).toContain('data-cnss-field="beneficiary_full_name"');
    expect(source).toContain('data-cnss-field="practitioner_inpe"');
  });

  it('matches the backend finalization response contract', () => {
    const source = read('./features/patients/InsuranceSubmissionTypes.ts');
    expect(source).toContain('is_new_version: boolean');
    expect(source).toContain('file_hash: string');
    expect(source).toContain('original_filename: string');
    expect(source).not.toContain('sha256: string');
  });
});
