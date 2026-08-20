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
    expect(details).toContain("type RadioTab = 'rvg' | 'panoramic' | 'cephalo'");
    expect(details).toContain("handleRadioTabChange('rvg')");
    expect(details).toContain('<PatientRvgPanel patientId={Number(id)} />');
    expect(details.indexOf('label="RVG"')).toBeLessThan(details.indexOf('label="Panoramique"'));
    expect(details.indexOf('label="Panoramique"')).toBeLessThan(details.indexOf('label="Céphalométrie"'));
  });

  it('mirrors backend imaging permissions including legacy defaults and fails closed on URL state', () => {
    expect(details).toContain("const legacyDentistEmployee = Boolean(user?.employer_id && role === 'DENTISTE' && !hasExplicitPermissions)");
    expect(details).toContain("userPermissions.panoramic === true");
    expect(details).toContain("userPermissions.cephalo === true");
    expect(details).toContain("const ownerOrAdmin = Boolean(user && (role === 'ADMIN' || (role === 'DENTISTE' && !user.employer_id)))");
    expect(details).toContain("const availableRadioTabs: RadioTab[] = [");
    expect(details).toContain("...(canPanoramic ? ['panoramic' as const] : [])");
    expect(details).toContain("...(canCephalo ? ['cephalo' as const] : [])");
    expect(details).toContain('availableRadioTabs.includes(requestedRadioTab)');
    expect(details).toContain("requestedRadioTab !== radioTab");
    expect(details).toContain('{canPanoramic && <ImagingButton');
    expect(details).toContain('{canCephalo && <ImagingButton');
  });

  it('never invents cephalometric demographics or auto-writes a treatment strategy', () => {
    expect(cephalo).not.toContain('age || 20');
    expect(cephalo).not.toContain("sexe: data.sexe || 'M'");
    expect(cephalo).not.toContain("setPatientData({ age: 20, sexe: 'M' })");
    expect(cephalo).not.toContain('generateTreatmentPlan(');
    expect(cephalo).toContain('patientDataError');
    expect(cephalo).toContain('Données Patient requises');
    expect(cephalo).toContain("data?.sexe === 'M' || data?.sexe === 'F'");
  });

  it('uses terminology matching the panoramic tooth-landmark contract', () => {
    for (const forbidden of ['Studio Panoramique IA', 'Détection SOTA', 'Intelligence Clinique IA', 'Zéro-Hallucination']) {
      expect(pano).not.toContain(forbidden);
    }
    expect(pano).toContain('Repérage dentaire automatique · validation praticien');
    expect(pano).toContain('Moteur déterministe • validation praticien');
    expect(pano).toContain('Constatations cliniques');
    expect(panoHistory).not.toContain('anomalie');
    expect(panoHistory).toContain('repère');
  });
});

describe('P4 recoverable imaging history UI', () => {
  it('uses trash and restore for panoramic history and excludes trash from active history', () => {
    expect(panoHistory).toContain('/panoramic-trash');
    expect(panoHistory).toContain('/panoramic/${analysis.id}/restore');
    expect(panoHistory).toContain('Mettre à la corbeille');
    expect(panoHistory).toContain('Restaurer');
    expect(panoHistory).toContain('const trashedIds = new Set<number>');
    expect(panoHistory).toContain('filter(item => !trashedIds.has(item.id))');
  });

  it('uses trash and restore for cephalometric history and excludes trash from active history', () => {
    expect(cephHistory).toContain('/cephalo-trash');
    expect(cephHistory).toContain('/cephalo/${analysis.id}/restore');
    expect(cephHistory).toContain('Mettre à la corbeille');
    expect(cephHistory).toContain('Restaurer');
    expect(cephHistory).toContain('const trashedIds = new Set<number>');
    expect(cephHistory).toContain('filter(item => !trashedIds.has(item.id))');
  });

  it('does not expose permanent deletion from either history surface', () => {
    expect(panoHistory).not.toContain('suppression permanente');
    expect(cephHistory).not.toContain('suppression permanente');
  });
});
