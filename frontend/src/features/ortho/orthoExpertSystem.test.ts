import { describe, expect, it } from 'vitest';
import { evaluateCase, deriveDivision } from './orthoExpertSystem';
import type { DonneesEtape3 } from './cephaloTypes';

const base: DonneesEtape3 = {
  age: '', cvm: '', date_teles: '',
  dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
  osseuse: { angle_tweed: '', decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: '' },
  esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
  ddm_clinique: '', ddm_cephalo: '', division: '', classe_squelettique: '', pattern_vertical: '', profil: '',
  severite_ddm: '', subdivision: false, analyse_moulages_auto: '', selectedAnalysis: 'COM',
  denture_type: '', preference_technique: '',
};

describe('evaluateCase scientific-core fail-closed boundary', () => {
  it('returns a descriptive report and explicitly leaves treatment to the practitioner', () => {
    const report = evaluateCase(base, null);
    expect(report.rapportMarkdown).toContain('Synthèse descriptive ODF');
    expect(report.rapportMarkdown).toContain('non document');
    expect(report.rapportMarkdown).toContain('Décision thérapeutique');
    expect(report.rapportMarkdown).toContain('praticien');
  });

  it('preserves zero-valued measurements as observations', () => {
    const report = evaluateCase({
      ...base,
      dentaire: { ...base.dentaire, surplomb: 0, recouvrement: 0, impa: 0, i_francfort: 0 },
    }, 0);
    expect(report.rapportMarkdown).toContain('Surplomb : 0 mm');
    expect(report.rapportMarkdown).toContain('Recouvrement : 0 mm');
    expect(report.rapportMarkdown).toContain('DDM globale calculée en amont : 0.0 mm');
  });

  it('never exposes autonomous extraction, mechanics, appliance or imaging recommendations', () => {
    const report = evaluateCase({
      ...base,
      dentaire: { ...base.dentaire, surplomb: 12, recouvrement: -4, impa: 120, i_francfort: 125 },
      classe_squelettique: 'Classe II', pattern_vertical: 'hyperdivergent', profil: 'convexe',
      wits_mcnamara: { wits_appraisal: 12 },
    }, -12) as any;
    expect(report.extraction).toBeUndefined();
    expect(report.mecanique).toBeUndefined();
    expect(report.damon).toBeUndefined();
    expect(report.examens).toBeUndefined();
    expect(report.rapportMarkdown).not.toMatch(/Damon|Invisalign|Twin Block|TAD|mini-vis|CBCT|IRM|extraction de|élastiques de Classe/i);
  });

  it('Wits alone never creates surgery or extraction output', () => {
    for (const value of [10, -10]) {
      const report = evaluateCase({ ...base, wits_mcnamara: { wits_appraisal: value } }, null) as any;
      expect(report.extraction).toBeUndefined();
      expect(report.mecanique).toBeUndefined();
      expect(report.rapportMarkdown).not.toMatch(/chirurg|BSSO|ostéotomie|extraction/i);
    }
  });
});

describe('deriveDivision fail-closed', () => {
  it('does not resolve Division 1/2 without a documented real Classe II string', () => {
    expect(deriveDivision('Non classifiable', 5)).toBeNull();
    expect(deriveDivision('Indéterminée', 5)).toBeNull();
    expect(deriveDivision('', 5)).toBeNull();
  });
});
