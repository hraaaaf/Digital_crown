import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  createPatientIdentityFormData,
  patientIdentityFromApi,
  patientIdentityToApiPayload,
  validatePatientIdentity,
} from './PatientIdentityContract';

const read = (name: string) => readFileSync(resolve(process.cwd(), `src/features/patients/${name}`), 'utf8');

describe('P6 shared patient identity contract', () => {
  it('starts without an implicit sex and validates only the four canonical required fields', () => {
    const form = createPatientIdentityFormData();
    expect(form.sexe).toBe('');
    expect(validatePatientIdentity(form)).toMatchObject({
      nom: expect.any(String),
      prenom: expect.any(String),
      date_naissance: expect.any(String),
      sexe: expect.any(String),
    });
  });

  it('never invents sex while mapping backend data', () => {
    expect(patientIdentityFromApi({ nom: 'A', prenom: 'B', date_naissance: '2000-01-01' }).sexe).toBe('');
    expect(patientIdentityFromApi({ sexe: 'M' }).sexe).toBe('M');
    expect(patientIdentityFromApi({ sexe: 'F' }).sexe).toBe('F');
    expect(patientIdentityFromApi({ sexe: 'X' }).sexe).toBe('');
  });

  it('serializes optional empty fields as null rather than invented values', () => {
    const payload = patientIdentityToApiPayload({
      ...createPatientIdentityFormData(),
      nom: 'BENMOUSSA',
      prenom: 'Achraf',
      date_naissance: '1990-01-01',
      sexe: 'M',
    });
    expect(payload.telephone).toBeNull();
    expect(payload.email).toBeNull();
    expect(payload.adresse).toBeNull();
    expect(payload.sexe).toBe('M');
  });

  it('is actually consumed by both Add and Edit forms', () => {
    const add = read('AddPatientForm.tsx');
    const edit = read('EditPatientForm.tsx');
    for (const source of [add, edit]) {
      expect(source).toContain("from './PatientIdentityContract'");
      expect(source).toContain('validatePatientIdentity');
      expect(source).toContain('patientIdentityToApiPayload');
    }
    expect(add).toContain('createPatientIdentityFormData');
    expect(edit).toContain('patientIdentityFromApi');
  });
});
