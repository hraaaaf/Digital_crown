import fs from 'node:fs';
import { describe, expect, it } from 'vitest';

const addSource = fs.readFileSync(new URL('./AddPatientForm.tsx', import.meta.url), 'utf8');
const editSource = fs.readFileSync(new URL('./EditPatientForm.tsx', import.meta.url), 'utf8');

describe('P0-B patient identity truth contract', () => {
  it('never preselects female sex for patient creation', () => {
    expect(addSource).toContain("sexe: ''");
    expect(addSource).toContain('<option value="">Sélectionner</option>');
    expect(addSource).not.toContain("sexe: 'F'");
  });

  it('never fabricates female sex when editing legacy or incomplete identity data', () => {
    expect(editSource).toContain("sexe: patient.sexe || ''");
    expect(editSource).not.toContain("patient.sexe || 'F'");
  });

  it('fails closed when dossier availability cannot be verified', () => {
    expect(addSource).toContain("setDossierStatus({ status: 'unknown' })");
    expect(editSource).toContain("setDossierStatus({ status: 'unknown' })");
    expect(addSource).not.toContain("setDossierStatus({ status: 'available' }); // Fallback silent");
  });

  it('blocks creation when duplicate precheck fails', () => {
    expect(addSource).toContain('Promise<boolean | null>');
    expect(addSource).toContain('if (hasDuplicate === null || hasDuplicate) return');
    expect(addSource).toContain('Vérification anti-doublon indisponible');
  });
});
