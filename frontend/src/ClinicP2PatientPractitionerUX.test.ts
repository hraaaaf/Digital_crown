import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

describe('Clinic P2 patient practitioner UX contract', () => {
  it('mounts the additive practitioner context at the patient route boundary', () => {
    const source = read('./features/patients/PatientDetails.tsx');
    expect(source).toContain('PatientPractitionerContextPortal');
    expect(source).toContain('patientId={patientId}');
  });

  it('uses patient-scoped practitioner APIs and keeps local/document truth explicit', () => {
    const source = read('./features/patients/components/PatientPractitionerContextPortal.tsx');
    expect(source).toContain("/patients/_clinic/practitioners");
    expect(source).toContain("/practitioner`");
    expect(source).toContain('Dossier local');
    expect(source).toContain('Patients et documents locaux inchangés');
    expect(source).toContain('Encaissements non attribués');
    expect(source).toContain('Production par praticien');
  });

  it('does not make practitioner choice part of the canonical create/edit identity payload', () => {
    const add = read('./features/patients/AddPatientForm.tsx');
    const edit = read('./features/patients/EditPatientForm.tsx');
    expect(add).not.toContain('praticien_referent_id');
    expect(edit).not.toContain('praticien_referent_id');
  });
});
