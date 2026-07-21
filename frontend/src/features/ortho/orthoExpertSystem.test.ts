import { describe, expect, it } from 'vitest';
import { evaluateCase, deriveDivision } from './orthoExpertSystem';
import type { DonneesEtape3 } from './cephaloTypes';

const missingMeasurements: DonneesEtape3 = {
  age: '', cvm: '', date_teles: '',
  dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
  osseuse: { angle_tweed: '', decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: '' },
  esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
  ddm_clinique: '', ddm_cephalo: '', division: '', classe_squelettique: '', pattern_vertical: '', profil: '',
  severite_ddm: '', subdivision: false, analyse_moulages_auto: '', selectedAnalysis: 'COM',
  denture_type: '', preference_technique: '',
};

describe('evaluateCase missing measurements', () => {
  it('does not fabricate numeric clinical values or a no-extraction conclusion', () => {
    const report = evaluateCase(missingMeasurements, null);

    expect(report.rapportMarkdown).toContain('non disponible');
    expect(report.rapportMarkdown).toContain('À ÉVALUER (DDM indisponible)');
    expect(report.rapportMarkdown).not.toContain('IMPA: 90');
    expect(report.rapportMarkdown).not.toContain('I/F: 107');
    expect(report.damon.maxillaire).toBe('A déterminer');
    expect(report.damon.mandibulaire).toBe('A déterminer');
  });

  it('preserves zero-valued measurements as actual observations', () => {
    const data: DonneesEtape3 = {
      ...missingMeasurements,
      dentaire: { ...missingMeasurements.dentaire, surplomb: 0, recouvrement: 0, impa: 0, i_francfort: 0 },
    };
    const report = evaluateCase(data, 0);

    expect(report.rapportMarkdown).toContain('Surplomb 0mm');
    expect(report.rapportMarkdown).toContain('DDM Globale 0.0mm');
  });

  it('does not route a negative recouvrement to supraclusie mechanics', () => {
    const data: DonneesEtape3 = {
      ...missingMeasurements,
      dentaire: { ...missingMeasurements.dentaire, recouvrement: -2 },
    };
    const report = evaluateCase(data, null);

    expect(report.mecanique.join(' ')).toContain('Infraclusie/Béance');
    expect(report.mecanique.join(' ')).not.toContain('Supraclusie');
  });
});

describe('Wits Appraisal quarantine (unvalidated occlusal plane provenance)', () => {
  it('does not recommend surgery prep from a strongly positive Wits alone', () => {
    const data: DonneesEtape3 = {
      ...missingMeasurements,
      wits_mcnamara: { wits_appraisal: 10 },
    };
    const report = evaluateCase(data, null);

    expect(report.mecanique.join(' ')).not.toContain('Wits');
    expect(report.mecanique.join(' ')).not.toContain('Chirurgie Orthognathique');
  });

  it('does not recommend surgery prep from a strongly negative Wits alone', () => {
    const data: DonneesEtape3 = {
      ...missingMeasurements,
      wits_mcnamara: { wits_appraisal: -10 },
    };
    const report = evaluateCase(data, null);

    expect(report.mecanique.join(' ')).not.toContain('Wits');
    expect(report.mecanique.join(' ')).not.toContain('Chirurgie Orthognathique');
  });

  it('does not let Wits swing extraction tooth selection independently of skeletal class', () => {
    const severeCrowdingBase: DonneesEtape3 = {
      ...missingMeasurements,
      dentaire: { ...missingMeasurements.dentaire, impa: 96 },
      classe_squelettique: 'Classe I',
      profil: 'droit',
    };

    const withoutWits = evaluateCase(severeCrowdingBase, -8);
    const withStronglyPositiveWits = evaluateCase(
      { ...severeCrowdingBase, wits_mcnamara: { wits_appraisal: 10 } },
      -8,
    );

    expect(withoutWits.extraction.recommandee).toBe(true);
    expect(withStronglyPositiveWits.extraction.dents).toBe(withoutWits.extraction.dents);
    expect(withStronglyPositiveWits.extraction.dents).toBe('14, 24, 34, 44');
  });

  it('leaves behavior unchanged when Wits is missing (no default/substitution)', () => {
    const withWitsUndefined = evaluateCase(missingMeasurements, null);
    const withWitsExplicitlyEmpty = evaluateCase(
      { ...missingMeasurements, wits_mcnamara: { wits_appraisal: '' } },
      null,
    );

    expect(withWitsExplicitlyEmpty.mecanique).toEqual(withWitsUndefined.mecanique);
    expect(withWitsExplicitlyEmpty.extraction).toEqual(withWitsUndefined.extraction);
  });
});

describe('ANB no longer classifies via classe_squelettique (CEPHALOMETRY-FRONTEND-AUTHORITY-REMOVAL-4B)', () => {
  it('never routes to the Classe II extraction-teeth branch when classe_squelettique is the new non-authoritative value', () => {
    const severeCrowdingNonClassifiable: DonneesEtape3 = {
      ...missingMeasurements,
      dentaire: { ...missingMeasurements.dentaire, impa: 96 },
      classe_squelettique: 'Non classifiable',
      profil: 'droit',
    };
    const report = evaluateCase(severeCrowdingNonClassifiable, -8);

    expect(report.extraction.recommandee).toBe(true);
    // Class-II-specific tooth set ("35, 45...") must not appear — classe.includes('Classe II') can't match.
    expect(report.extraction.dents).toBe('14, 24, 34, 44');
  });

  it('same for "Indéterminée" (ANB missing entirely)', () => {
    const severeCrowdingIndeterminee: DonneesEtape3 = {
      ...missingMeasurements,
      dentaire: { ...missingMeasurements.dentaire, impa: 96 },
      classe_squelettique: 'Indéterminée',
      profil: 'droit',
    };
    const report = evaluateCase(severeCrowdingIndeterminee, -8);

    expect(report.extraction.dents).toBe('14, 24, 34, 44');
  });

  it('deriveDivision never resolves Division 1/2 without a real "Classe II" string', () => {
    // Consumed by Step3Clinical.tsx — confirms it can't be tricked by the new labels either.
    expect(deriveDivision('Non classifiable', 5)).toBeNull();
    expect(deriveDivision('Indéterminée', 5)).toBeNull();
  });
});
