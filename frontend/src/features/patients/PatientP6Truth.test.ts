import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patientsDir = resolve(process.cwd(), 'src/features/patients');
const add = readFileSync(resolve(patientsDir, 'AddPatientForm.tsx'), 'utf8');
const edit = readFileSync(resolve(patientsDir, 'EditPatientForm.tsx'), 'utf8');
const details = readFileSync(resolve(patientsDir, 'PatientDetailsInner.tsx'), 'utf8');
const finances = readFileSync(resolve(patientsDir, 'components/PatientFinances.tsx'), 'utf8');

describe('Patient P6 identity truth boundary', () => {
  it('never invents sex and blocks create when duplicate precheck is unavailable', () => {
    expect(add).toContain("sexe: ''");
    expect(add).not.toContain("sexe: 'F'");
    expect(add).toContain('<option value="">Choisir');
    expect(add).toContain('Le sexe doit être renseigné explicitement.');
    expect(add).toContain('Promise<boolean | null>');
    expect(add).toContain('Vérification anti-doublon indisponible');
    expect(add).toContain('if (hasDuplicate === null) return');
    expect(add).toContain('Disponibilité non vérifiée');
  });

  it('never substitutes or visually invents edit values after a patient load failure', () => {
    expect(edit).toContain("sexe: ''");
    expect(edit).not.toContain("patient.sexe || 'F'");
    expect(edit).toContain('<option value="">Choisir');
    expect(edit).toContain('Impossible de charger le patient');
    expect(edit).toContain("Le formulaire n'est pas affiché avec des valeurs par défaut.");
    expect(edit).toContain('Disponibilité non vérifiée');
  });
});

describe('Patient P6 financial truth and visible RBAC', () => {
  it('guards the finance tab, rendering and quick collection action', () => {
    expect(details).toContain('const canFinance =');
    expect(details).toContain("if (!canFinance && activeTab === 'finances')");
    expect(details).toContain("canFinance && <TabButton");
    expect(details).toContain("canFinance && activeTab === 'finances'");
    expect(details).toContain('{canFinance && (');
  });

  it('uses factual KPIs and refuses false financial zero states', () => {
    expect(finances).toContain('Boolean(snapshot.has_billing_data)');
    expect(finances).toContain('Facturé');
    expect(finances).toContain('Encaissé');
    expect(finances).toContain('Reste dû');
    expect(finances).toContain('Prochaine échéance');
    expect(finances).toContain('Indéterminé');
    expect(finances).toContain('État des impayés indéterminé');
    expect(finances).toContain('Impossible de charger les finances');
    expect(finances).not.toContain('Taux Recouvrement');
    expect(finances).not.toContain('const recoveryRate =');
  });
});
