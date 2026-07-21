import { describe, expect, it } from 'vitest';
import { computeSignedELineDistance, computeSignedOverbite, computeStep3Data, generateTreatmentPlan } from './cephaloUtils';
import type { DonneesEtape3 } from './cephaloTypes';

const landmarks = [
  { id: 's', x: 50, y: 60 }, { id: 'n', x: 70, y: 40 },
  { id: 'po', x: 40, y: 40 }, { id: 'or', x: 80, y: 40 },
  { id: 'a', x: 90, y: 90 }, { id: 'b', x: 85, y: 130 },
  { id: 'go', x: 60, y: 150 }, { id: 'me', x: 85, y: 170 },
  { id: 'u1i', x: 100, y: 100 }, { id: 'u1a', x: 105, y: 80 },
  { id: 'l1i', x: 92, y: 120 }, { id: 'l1a', x: 88, y: 140 },
] as any;

describe('computeStep3Data without calibration', () => {
  it('keeps angles and leaves millimeter values empty', () => {
    const result = computeStep3Data(landmarks, 20, 'M', null);

    expect(result.osseuse?.sna).not.toBe('');
    expect(result.osseuse?.snb).not.toBe('');
    expect(result.osseuse?.anb).not.toBe('');
    expect(result.osseuse?.angle_tweed).not.toBe('');
    expect(result.dentaire?.surplomb).toBe('');
    expect(result.dentaire?.recouvrement).toBe('');
    expect(result.osseuse?.situation_a).toBe('');
    expect(result.osseuse?.situation_b).toBe('');
    expect(result.osseuse?.decalage_ab).toBe('');
  });
});

describe('nasolabial angle quarantine', () => {
  it('does not generate a local clinical nasolabial value', () => {
    const result = computeStep3Data([
      ...landmarks,
      { id: 'cm', x: 80, y: 50 },
      { id: 'sn', x: 90, y: 60 },
      { id: 'ls', x: 95, y: 80 },
    ] as any, 20, 'M', 0.2);

    expect(result.esthetique?.angle_nasolabial).toBe('');
  });
});

describe('computeSignedOverbite', () => {
  const po = { x: 0, y: 0 };
  const or_ = { x: 100, y: 0 };
  const upper = { x: 50, y: 30 };
  const lower = { x: 50, y: 20 };

  const rotate = ({ x, y }: { x: number; y: number }, degrees = 30) => {
    const radians = degrees * Math.PI / 180;
    return {
      x: x * Math.cos(radians) - y * Math.sin(radians),
      y: x * Math.sin(radians) + y * Math.cos(radians),
    };
  };

  it('preserves positive, zero, and negative overbite values', () => {
    expect(computeSignedOverbite(upper, lower, po, or_, 1)).toBe(10);
    expect(computeSignedOverbite(upper, upper, po, or_, 1)).toBe(0);
    expect(computeSignedOverbite(upper, { x: 50, y: 40 }, po, or_, 1)).toBe(-10);
  });

  it('is invariant under rotation and horizontal mirroring', () => {
    const baseline = computeSignedOverbite(upper, lower, po, or_, 1);
    expect(computeSignedOverbite(rotate(upper), rotate(lower), rotate(po), rotate(or_), 1)).toBe(baseline);
    expect(computeSignedOverbite(upper, lower, { x: 100, y: 0 }, { x: 0, y: 0 }, 1)).toBe(baseline);
  });

  it('returns unavailable when the Frankfurt points are missing', () => {
    expect(computeSignedOverbite(upper, lower, undefined, or_, 1)).toBeNull();
    expect(computeSignedOverbite(upper, lower, po, undefined, 1)).toBeNull();
  });
});

describe('computeSignedELineDistance', () => {
  const prn = { x: 0, y: 0 };
  const pogSoft = { x: 0, y: 10 };
  const po = { x: -10, y: 0 };
  const or_ = { x: 10, y: 0 };

  const rotate = ({ x, y }: { x: number; y: number }, degrees: number) => {
    const radians = degrees * Math.PI / 180;
    return {
      x: x * Math.cos(radians) - y * Math.sin(radians),
      y: x * Math.sin(radians) + y * Math.cos(radians),
    };
  };

  const mirror = ({ x, y }: { x: number; y: number }) => ({ x: -x, y });

  it('returns positive, negative, and zero values for both lips', () => {
    expect(computeSignedELineDistance({ x: 2, y: 5 }, prn, pogSoft, po, or_, 1)).toBe(2); // Ls ahead
    expect(computeSignedELineDistance({ x: -3, y: 5 }, prn, pogSoft, po, or_, 1)).toBe(-3); // Li behind
    expect(computeSignedELineDistance({ x: 0, y: 5 }, prn, pogSoft, po, or_, 1)).toBe(0);
  });

  it('is invariant under mirror, rotation, and E-line endpoint reversal', () => {
    const lip = { x: 2, y: 5 };
    const baseline = computeSignedELineDistance(lip, prn, pogSoft, po, or_, 1);
    expect(computeSignedELineDistance(mirror(lip), mirror(prn), mirror(pogSoft), mirror(po), mirror(or_), 1)).toBe(baseline);

    for (const degrees of [30, -45, 90]) {
      expect(computeSignedELineDistance(rotate(lip, degrees), rotate(prn, degrees), rotate(pogSoft, degrees), rotate(po, degrees), rotate(or_, degrees), 1)).toBeCloseTo(baseline ?? 0, 10);
    }

    expect(computeSignedELineDistance(lip, pogSoft, prn, po, or_, 1)).toBe(baseline);
  });

  it('returns unavailable for missing calibration, orientation, or degenerate geometry', () => {
    const lip = { x: 2, y: 5 };
    expect(computeSignedELineDistance(lip, prn, pogSoft, po, or_, null)).toBeNull();
    expect(computeSignedELineDistance(undefined, prn, pogSoft, po, or_, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, undefined, pogSoft, po, or_, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, prn, undefined, po, or_, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, prn, pogSoft, undefined, or_, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, prn, pogSoft, po, undefined, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, prn, prn, po, or_, 1)).toBeNull();
    expect(computeSignedELineDistance(lip, prn, pogSoft, po, po, 1)).toBeNull();
  });

  it('returns unavailable when the E-line side cannot be resolved against Frankfurt', () => {
    expect(computeSignedELineDistance(
      { x: 5, y: 2 },
      { x: 0, y: 0 },
      { x: 10, y: 0 },
      { x: 0, y: -10 },
      { x: 10, y: -10 },
      1,
    )).toBeNull();
  });
});

describe('custom McNamara measurements quarantine', () => {
  it('does not derive a skeletal class from A-B when ANB is unavailable', () => {
    const result = computeStep3Data([
      { id: 's', x: 0, y: 100 }, { id: 'n', x: 0, y: 0 },
      { id: 'po', x: 0, y: 0 }, { id: 'or', x: 100, y: 0 },
      { id: 'a', x: 100, y: 100 }, { id: 'b', x: -100, y: 100 },
    ] as any, 20, 'M', 1);

    expect(result.osseuse?.decalage_ab).not.toBe('');
    expect(result.classe_squelettique).not.toContain('discordance');
  });
});

describe('Steiner ANB classification removed from frontend (CEPHALOMETRY-FRONTEND-AUTHORITY-REMOVAL-4B)', () => {
  // S/N fixed, A/B swept so ANB (= SNA - SNB) lands strongly positive, strongly
  // negative, and near-neutral — previously "Classe II" / "Classe III" / "Classe I".
  const base = [
    { id: 's', x: 50, y: 60 }, { id: 'n', x: 70, y: 40 },
    { id: 'po', x: 40, y: 40 }, { id: 'or', x: 80, y: 40 },
  ];

  it('never produces "Classe I/II/III" regardless of ANB value', () => {
    const strongPositive = computeStep3Data([...base, { id: 'a', x: 95, y: 90 }, { id: 'b', x: 60, y: 130 }] as any, 30, 'M', 1);
    const strongNegative = computeStep3Data([...base, { id: 'a', x: 60, y: 90 }, { id: 'b', x: 95, y: 130 }] as any, 30, 'M', 1);
    const neutral = computeStep3Data([...base, { id: 'a', x: 90, y: 90 }, { id: 'b', x: 85, y: 130 }] as any, 30, 'M', 1);

    for (const result of [strongPositive, strongNegative, neutral]) {
      expect(result.classe_squelettique).not.toMatch(/Classe (I|II|III)\b/);
    }
  });

  it('reports "Non classifiable" when ANB has a value, distinct from "Indéterminée" (no ANB at all)', () => {
    const withAnb = computeStep3Data([...base, { id: 'a', x: 95, y: 90 }, { id: 'b', x: 60, y: 130 }] as any, 30, 'M', 1);
    const withoutAnb = computeStep3Data([
      { id: 'po', x: 40, y: 40 }, { id: 'or', x: 80, y: 40 },
    ] as any, 30, 'M', 1);

    expect(withAnb.classe_squelettique).toBe('Non classifiable');
    expect(withoutAnb.classe_squelettique).toBe('Indéterminée');
  });

  it('generateTreatmentPlan no longer derives a surgical decision from ANB', () => {
    const dataTemplate: DonneesEtape3 = {
      age: 30, cvm: '', date_teles: '',
      dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
      osseuse: { angle_tweed: '', decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: 0 },
      esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
      ddm_clinique: '', ddm_cephalo: '', division: '', classe_squelettique: 'Non classifiable',
      pattern_vertical: '', profil: '',
      severite_ddm: '', subdivision: false, analyse_moulages_auto: '', selectedAnalysis: 'COM',
      denture_type: '', preference_technique: '',
    };

    for (const anb of [12, -8, 0]) {
      const plan = generateTreatmentPlan({ ...dataTemplate, osseuse: { ...dataTemplate.osseuse, anb } });
      expect(plan).not.toContain('Classe II chirurgicale');
      expect(plan).not.toContain('Classe III chirurgicale');
      expect(plan).not.toContain('BSSO');
      expect(plan).not.toContain('Ostéotomie bimaxillaire');
      expect(plan).toContain('Classification squelettique non disponible');
    }
  });
});

describe('Tweed pattern_vertical classification removed from frontend (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C)', () => {
  // po/or fixed, go/me swept so the FMA angle (po-or vs go-me) lands strongly
  // hyperdivergent, strongly hypodivergent, and near-normodivergent — previously
  // 'hyperdivergent' / 'hypodivergent' / 'normodivergent'.
  const base = [
    { id: 'po', x: 40, y: 40 }, { id: 'or', x: 80, y: 40 },
  ];

  it('never sets pattern_vertical regardless of the FMA angle', () => {
    const steep = computeStep3Data([...base, { id: 'go', x: 40, y: 40 }, { id: 'me', x: 200, y: 200 }] as any, 30, 'M', 1);
    const shallow = computeStep3Data([...base, { id: 'go', x: 40, y: 40 }, { id: 'me', x: 200, y: 45 }] as any, 30, 'M', 1);

    for (const result of [steep, shallow]) {
      expect(result.pattern_vertical).not.toBe('hyperdivergent');
      expect(result.pattern_vertical).not.toBe('hypodivergent');
      expect(result.pattern_vertical).not.toBe('normodivergent');
      expect(result.pattern_vertical).toBeUndefined();
    }
  });

  it('generateTreatmentPlan no longer derives a vertical-control decision from Tweed', () => {
    const dataTemplate: DonneesEtape3 = {
      age: 30, cvm: '', date_teles: '',
      dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
      osseuse: { angle_tweed: 0, decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: '' },
      esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
      ddm_clinique: '', ddm_cephalo: '', division: '', classe_squelettique: 'Non classifiable',
      pattern_vertical: '', profil: '',
      severite_ddm: '', subdivision: false, analyse_moulages_auto: '', selectedAnalysis: 'COM',
      denture_type: '', preference_technique: '',
    };

    for (const angle_tweed of [35, 15, 26]) {
      const plan = generateTreatmentPlan({ ...dataTemplate, osseuse: { ...dataTemplate.osseuse, angle_tweed } });
      expect(plan).not.toContain('CONTRÔLE VERTICAL STRICT');
      expect(plan).not.toContain('ESTHÉTIQUE VERTICALE');
      expect(plan).not.toContain('Face longue');
      expect(plan).not.toContain('Face courte');
      expect(plan).toContain('GESTION VERTICALE');
      expect(plan).toContain('Typologie verticale non disponible');
    }
  });
});