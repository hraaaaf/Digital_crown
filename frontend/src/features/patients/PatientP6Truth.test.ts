import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patientsDir = resolve(process.cwd(), 'src/features/patients');
const add = readFileSync(resolve(patientsDir, 'AddPatientForm.tsx'), 'utf8');
const edit = readFileSync(resolve(patientsDir, 'EditPatientForm.tsx'), 'utf8');
const identity = readFileSync(resolve(patientsDir, 'PatientIdentityContract.ts'), 'utf8');
const details = readFileSync(resolve(patientsDir, 'PatientDetailsInner.tsx'), 'utf8');
const finances = readFileSync(resolve(patientsDir, 'components/PatientFinances.tsx'), 'utf8');

describe('Patient P6 identity truth boundary', () => {
  it('uses one shared identity contract and never invents sex', () => {
    expect(identity).toContain("sexe: ''");
    expect(identity).not.toContain("sexe: 'F'");
    expect(identity).toContain("patient.sexe === 'M' || patient.sexe === 'F'");
    expect(identity).toContain('Le sexe doit être renseigné explicitement.');
    for (const form of [add, edit]) {
      expect(form).toContain('PatientIdentityContract');
      expect(form).toContain('createPatientIdentityFormData');
      expect(form).toContain('validatePatientIdentity');
      expect(form).toContain('patientIdentityToApiPayload');
      expect(form).toContain('<option value="">Choisir');
    }
    expect(edit).toContain('patientIdentityFromApi');
  });

  it('fails closed when duplicate/dossier checks or patient loading fail', () => {
    expect(add).toContain('Promise<boolean | null>');
    expect(add).toContain('Vérification anti-doublon indisponible');
    expect(add).toContain('if (hasDuplicate === null) return');
    expect(add).toContain('Disponibilité non vérifiée');
    expect(edit).toContain('Impossible de charger le patient');
    expect(edit).toContain("Le formulaire n'est pas affiché avec des valeurs par défaut.");
    expect(edit).toContain('Disponibilité non vérifiée');
  });
});

describe('Patient P6 financial truth and visible RBAC', () => {
  it('guards the finance tab, rendering, URL and quick collection action', () => {
    expect(details).toContain('const canFinance = Boolean(');
    expect(details).toContain("userPermissions.accounting === true || userPermissions.payments === true");
    expect(details).toContain("if (!canFinance && activeTab === 'finances')");
    expect(details).toContain("canFinance && <TabButton");
    expect(details).toContain("canFinance && activeTab === 'finances'");
    expect(details).toContain('{canFinance && (');
    expect(details).toContain('setIsPayModalOpen(false)');
  });

  it('uses factual KPIs and refuses false financial zero states', () => {
    expect(finances).toContain('snapshot.has_billing_data === true');
    expect(finances).toContain('Facturé');
    expect(finances).toContain('Encaissé');
    expect(finances).toContain('Reste dû');
    expect(finances).toContain('Prochaine échéance');
    expect(finances).toContain('Indéterminé');
    expect(finances).toContain('Situation d’impayé indéterminée');
    expect(finances).toContain('Aucun solde n’est déduit d’une lecture incomplète.');
    expect(finances).toContain('Impossible de charger les finances');
    expect(finances).not.toContain('Taux Recouvrement');
    expect(finances).not.toContain('const recoveryRate =');
  });
});
