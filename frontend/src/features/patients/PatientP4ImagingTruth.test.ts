import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const src = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const details = src('src/features/patients/PatientDetailsInner.tsx');
const cephalo = src('src/features/ortho/CephaloWorkspace.tsx');
const pano = src('src/features/panoramic/PanoramicStudio.tsx');
const panoHistory = src('src/features/panoramic/PanoramicHistory.tsx');
const cephHistory = src('src/features/ortho/CephaloHistory.tsx');

describe('P4 unified imaging truth boundary', () => {
  it('exposes RVG, Panoramique and Céphalométrie as one imaging space', () => {
    expect(details).toContain("'rvg' | 'panoramic' | 'cephalo'");
    expect(details).toContain("handleRadioTabChange('rvg')");
    expect(details).toContain('<PatientRvgPanel patientId={Number(id)} />');
  });

  it('mirrors backend imaging permissions including legacy defaults', () => {
    expect(details).toContain("const canRvg = hasPatientPermission('patients')");
    expect(details).toContain("const canPanoramic = hasPatientPermission('panoramic')");
    expect(details).toContain("const canCephalo = hasPatientPermission('cephalo')");
    expect(details).toContain("user.role === 'DENTISTE'");
    expect(details).toContain("user.role === 'SECRETAIRE'");
    expect(details).toContain('{canRvg && (');
    expect(details).toContain('{canPanoramic && (');
    expect(details).toContain('{canCephalo && (');
    expect(details).toContain('const currentImagingAllowed =');
  });

  it('never invents cephalometric demographics or auto-writes a treatment strategy', () => {
    expect(cephalo).not.toContain('age || 20');
    expect(cephalo).not.toContain("sexe: data.sexe || 'M'");
    expect(cephalo).not.toContain("setPatientData({ age: 20, sexe: 'M' })");
    expect(cephalo).not.toContain('generateTreatmentPlan(');
    expect(cephalo).toContain('patientDataError');
    expect(cephalo).toContain('Réessayer');
  });

  it('uses terminology matching the panoramic tooth-landmark contract', () => {
    for (const forbidden of ['Studio Panoramique IA', 'Détection SOTA', 'Intelligence Clinique IA', 'Zéro-Hallucination']) {
      expect(pano).not.toContain(forbidden);
    }
    expect(pano).toContain('Repérage dentaire automatique · validation praticien');
    expect(pano).toContain('Constatations cliniques');
    expect(panoHistory).not.toContain('anomalie');
    expect(panoHistory).toContain('repère');
  });
});

describe('P4 recoverable imaging history UI', () => {
  it('uses trash and restore for panoramic history', () => {
    expect(panoHistory).toContain('/panoramic-trash');
    expect(panoHistory).toContain('/panoramic/${analysis.id}/restore');
    expect(panoHistory).toContain('Mettre à la corbeille');
    expect(panoHistory).toContain('Restaurer');
  });

  it('uses trash and restore for cephalometric history', () => {
    expect(cephHistory).toContain('/cephalo-trash');
    expect(cephHistory).toContain('/cephalo/${analysis.id}/restore');
    expect(cephHistory).toContain('Mettre à la corbeille');
    expect(cephHistory).toContain('Restaurer');
  });

  it('does not expose permanent deletion from either history surface', () => {
    expect(panoHistory).not.toContain('suppression permanente');
    expect(cephHistory).not.toContain('suppression permanente');
  });
});
