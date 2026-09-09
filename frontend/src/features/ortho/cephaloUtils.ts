import type { Landmark, CVMStage } from './cephaloShared';
import type { DiagnosticTexts, DonneesEtape2, DonneesEtape3 } from './cephaloTypes';

/**
 * Legacy compatibility boundary.
 *
 * The previous implementation converted an incisor-angle difference into
 * millimetres of space using a universal 2.5°/mm factor. That relationship is
 * not validated here as a patient-specific space model, so the function fails
 * closed instead of manufacturing a corrected DDM.
 */
export function calcDDMReelle(
  _ddmClinique: number | '',
  _valeurActuelle: number | null,
  _norme: number = 90,
): number | null {
  return null;
}

/**
 * Legacy compatibility boundary for the same unvalidated IMPA -> space rule.
 */
export function calcDDMCephalo(_impa: number | null): number | null {
  return null;
}

/**
 * CVM is a morphology-based assessment and is never inferred from chronological
 * age/sex alone. The practitioner or a future validated morphology pipeline must
 * provide the stage explicitly.
 */
export function estimateCVM(_age: number | '', _sexe: 'M' | 'F'): CVMStage | '' {
  return '';
}

/**
 * Calcule l'IMPA local basé sur les points actuels du tracé.
 */
export function computeLocalImpa(lms: Landmark[]): number | null {
  const g = (id: string) => lms.find(l => l.id === id);
  const l1i = g('L1_incisal');
  const l1a = g('L1_apex');
  const go = g('Go');
  const me = g('Me');
  if (!l1i || !l1a || !go || !me) return null;
  const ax = l1i.x - l1a.x;
  const ay = l1i.y - l1a.y;
  const mx = me.x - go.x;
  const my = me.y - go.y;
  const ma = Math.sqrt(ax * ax + ay * ay);
  const mm = Math.sqrt(mx * mx + my * my);
  if (ma < 0.1 || mm < 0.1) return null;
  const cos = Math.max(-1, Math.min(1, (ax * mx + ay * my) / (ma * mm)));
  const rawAngle = Math.acos(cos) * (180 / Math.PI);
  return Math.round((180 - rawAngle) * 10) / 10;
}

/**
 * Calcule l'angle entre deux segments (AB et CD).
 */
export function computeAngle(
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  p3: { x: number; y: number },
  p4: { x: number; y: number },
): number {
  const dx1 = p2.x - p1.x;
  const dy1 = p2.y - p1.y;
  const dx2 = p4.x - p3.x;
  const dy2 = p4.y - p3.y;
  const m1 = Math.sqrt(dx1 * dx1 + dy1 * dy1);
  const m2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
  if (m1 < 0.1 || m2 < 0.1) return 0;
  const cos = Math.max(-1, Math.min(1, (dx1 * dx2 + dy1 * dy2) / (m1 * m2)));
  return Math.round(Math.acos(cos) * (180 / Math.PI) * 10) / 10;
}

/**
 * Calcule l'angle inter-incisif (1/1).
 */
export function computeInterIncisalAngle(u1i: Landmark, u1a: Landmark, l1i: Landmark, l1a: Landmark): number {
  return 180 - computeAngle(u1i, u1a, l1i, l1a);
}

/**
 * Calcule la distance signée d'un point à une ligne perpendiculaire à une autre.
 * Utilisé pour McNamara (distance à la verticale de Nasion).
 */
export function computeDistanceToVertical(
  target: { x: number; y: number },
  origin: { x: number; y: number },
  refA: { x: number; y: number },
  refB: { x: number; y: number },
  ratio: number = 1,
): number {
  const dx = refB.x - refA.x;
  const dy = refB.y - refA.y;
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len < 0.1) return 0;
  const ux = dx / len;
  const uy = dy / len;
  const vx = target.x - origin.x;
  const vy = target.y - origin.y;
  return (vx * ux + vy * uy) * ratio;
}

/**
 * Signed overbite projected onto the Frankfort perpendicular. The direction is
 * fixed toward increasing image-y so frontend and backend share one convention.
 */
export function computeSignedOverbite(
  upperIncisal: { x: number; y: number } | undefined,
  lowerIncisal: { x: number; y: number } | undefined,
  po: { x: number; y: number } | undefined,
  or_: { x: number; y: number } | undefined,
  ratio: number | null,
): number | null {
  if (!upperIncisal || !lowerIncisal || !po || !or_ || ratio === null) return null;
  const dx = or_.x - po.x;
  const dy = or_.y - po.y;
  const length = Math.hypot(dx, dy);
  if (length < 0.1) return null;

  let perpX = -dy / length;
  let perpY = dx / length;
  if (perpY < 0) {
    perpX = -perpX;
    perpY = -perpY;
  }

  const projection = (upperIncisal.x - lowerIncisal.x) * perpX
    + (upperIncisal.y - lowerIncisal.y) * perpY;
  return Math.round(projection * ratio * 10) / 10;
}

/**
 * Projections McNamara (N', A', B') sur le plan de Francfort.
 */
export function computeMcNamaraProjections(lms: Landmark[]): {
  N_prime?: [number, number];
  A_prime?: [number, number];
  B_prime?: [number, number];
} {
  const g = (id: string) => lms.find(l => l.id === id);
  const po = g('Po');
  const or_ = g('Or');
  const n = g('N');
  const a = g('A');
  const b = g('B');

  if (!po || !or_) return {};

  const projections: {
    N_prime?: [number, number];
    A_prime?: [number, number];
    B_prime?: [number, number];
  } = {};

  const project = (
    px: number,
    py: number,
    ax: number,
    ay: number,
    bx: number,
    by: number,
  ): [number, number] | null => {
    const dx = bx - ax;
    const dy = by - ay;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return null;
    const t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
    return [ax + t * dx, ay + t * dy];
  };

  if (n) projections.N_prime = project(n.x, n.y, po.x, po.y, or_.x, or_.y) || undefined;
  if (a) projections.A_prime = project(a.x, a.y, po.x, po.y, or_.x, or_.y) || undefined;
  if (b) projections.B_prime = project(b.x, b.y, po.x, po.y, or_.x, or_.y) || undefined;
  return projections;
}

/**
 * Formate un nombre pour l'affichage clinique (ex: +2.5).
 */
export function fmtNum(v: number | null, dec = 1): string {
  if (v === null || Number.isNaN(v)) return '-';
  return (v >= 0 ? '+' : '') + v.toFixed(dec);
}

/**
 * Historical compatibility function. Missing apexes are no longer fabricated
 * from a fixed tooth length/angle. Geometry requiring an apex must remain
 * unavailable until a real point is supplied or detected.
 */
export function initializeDefaultApexes(landmarks: Landmark[]): Landmark[] {
  return [...landmarks];
}

/**
 * Distance d'un point à une droite définie par deux points.
 */
export function computeDistanceToLine(
  p: Landmark,
  l1: Landmark,
  l2: Landmark,
  ratio: number,
  signed: boolean = false,
): number {
  const x0 = p.x;
  const y0 = p.y;
  const x1 = l1.x;
  const y1 = l1.y;
  const x2 = l2.x;
  const y2 = l2.y;
  const num = (x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1);
  const den = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  if (den === 0) return 0;
  return signed ? (num / den) * ratio : (Math.abs(num) / den) * ratio;
}

/**
 * E-line distance signed by the anatomical posterior-to-anterior Po -> Or axis.
 * The epsilon is only a pixel-geometry guard, never a clinical threshold.
 */
export function computeSignedELineDistance(
  lip: { x: number; y: number } | undefined,
  prn: { x: number; y: number } | undefined,
  pogSoft: { x: number; y: number } | undefined,
  po: { x: number; y: number } | undefined,
  or_: { x: number; y: number } | undefined,
  ratio: number | null,
): number | null {
  if (!lip || !prn || !pogSoft || !po || !or_ || ratio === null) return null;

  const epsilon = 1e-6;
  const eX = pogSoft.x - prn.x;
  const eY = pogSoft.y - prn.y;
  const eLengthSq = eX * eX + eY * eY;
  const aX = or_.x - po.x;
  const aY = or_.y - po.y;
  const aLength = Math.hypot(aX, aY);
  if (eLengthSq <= epsilon * epsilon || aLength <= epsilon) return null;

  const t = ((lip.x - prn.x) * eX + (lip.y - prn.y) * eY) / eLengthSq;
  const qX = prn.x + t * eX;
  const qY = prn.y + t * eY;
  const rX = lip.x - qX;
  const rY = lip.y - qY;
  const magnitudePx = Math.hypot(rX, rY);
  if (magnitudePx <= epsilon) return 0;

  const anteriorScore = rX * (aX / aLength) + rY * (aY / aLength);
  if (Math.abs(anteriorScore) <= epsilon) return null;
  return Math.sign(anteriorScore) * magnitudePx * ratio;
}

export function computeStep3Data(
  lms: Landmark[],
  age: number | '',
  _sexe: 'M' | 'F',
  mmPerPixel: number | null,
  etape2: DonneesEtape2 | null = null,
): Partial<DonneesEtape3> {
  const g = (id: string) => lms.find(l => l.id.toLowerCase() === id.toLowerCase());
  const po = g('po');
  const or_ = g('or');
  const n = g('n');
  const a = g('a');
  const b = g('b');
  const s = g('s');
  const go = g('go');
  const me = g('me');
  const prn = g('prn') || g('nose_tip');
  const ls = g('ls_soft') || g('ls') || g('ul');
  const li = g('li_soft') || g('li') || g('ll');
  const pogSoft = g('pog_soft') || g('stpog');
  const u1i = g('u1_incisal') || g('u1i');
  const u1a = g('u1_apex') || g('u1a');
  const l1i = g('l1_incisal') || g('l1i');
  const l1a = g('l1_apex') || g('l1a');

  const ratio = mmPerPixel;
  const results: Partial<DonneesEtape3> = {
    age,
    // Never invent CVM or dentition stage from chronology.
    cvm: '',
    denture_type: '',
    dentaire: {
      surplomb: '',
      recouvrement: '',
      impa: '',
      i_francfort: '',
      inter_incisif: '',
    },
    osseuse: {
      angle_tweed: '',
      decalage_ab: '',
      situation_a: '',
      situation_b: '',
      profondeur_faciale: '',
      sna: '',
      snb: '',
      anb: '',
    },
    esthetique: {
      ligne_e_ls: '',
      ligne_e_li: '',
      angle_nasolabial: '',
    },
  };

  if (po && or_ && go && me) {
    results.osseuse!.angle_tweed = Math.round(computeAngle(po, or_, go, me));
  }

  if (s && n && a && b) {
    const sna = computeAngle(n, s, n, a);
    const snb = computeAngle(n, s, n, b);
    results.osseuse!.sna = Math.round(sna * 10) / 10;
    results.osseuse!.snb = Math.round(snb * 10) / 10;
    results.osseuse!.anb = Math.round((sna - snb) * 10) / 10;
  }

  if (ratio !== null && n && po && or_) {
    if (a) {
      const distA = computeDistanceToVertical(a, n, po, or_, ratio);
      results.osseuse!.situation_a = Math.round(distA * 10) / 10;
    }
    if (b) {
      const distB = computeDistanceToVertical(b, n, po, or_, ratio);
      results.osseuse!.situation_b = Math.round(distB * 10) / 10;
    }
    if (a && b) {
      const distA = computeDistanceToVertical(a, n, po, or_, ratio);
      const distB = computeDistanceToVertical(b, n, po, or_, ratio);
      results.osseuse!.decalage_ab = Math.round((distA - distB) * 10) / 10;
    }
    if (s) {
      const distS = computeDistanceToVertical(s, n, po, or_, ratio);
      results.osseuse!.profondeur_faciale = Math.round(Math.abs(distS) * 10) / 10;
    }
  }

  if (u1i && u1a && l1i && l1a) {
    results.dentaire!.inter_incisif = Math.round(computeInterIncisalAngle(u1i, u1a, l1i, l1a));
    if (n && a) {
      results.dentaire!.i_na_angle = Math.round(computeAngle(n, a, u1a, u1i));
      if (ratio !== null) results.dentaire!.i_na_mm = Math.round(computeDistanceToLine(u1i, n, a, ratio) * 10) / 10;
    }
    if (n && b) {
      results.dentaire!.i_nb_angle = Math.round(computeAngle(n, b, l1a, l1i));
      if (ratio !== null) results.dentaire!.i_nb_mm = Math.round(computeDistanceToLine(l1i, n, b, ratio) * 10) / 10;
    }
  }

  if (l1i && l1a && go && me) results.dentaire!.impa = computeLocalImpa(lms) || '';
  if (po && or_ && l1i && l1a) results.dentaire!.fmia = Math.round(computeAngle(po, or_, l1a, l1i));
  if (u1i && u1a && po && or_) results.dentaire!.i_francfort = computeAngle(u1a, u1i, po, or_);

  if (ratio !== null && u1i && l1i && po && or_) {
    const overjet = computeDistanceToVertical(l1i, u1i, po, or_, ratio);
    results.dentaire!.surplomb = Math.round(Math.abs(overjet) * 10) / 10;
    const overbite = computeSignedOverbite(u1i, l1i, po, or_, ratio);
    if (overbite !== null) results.dentaire!.recouvrement = overbite;
  }

  // Raw geometry is allowed; local diagnostic classification is not.
  const anb = results.osseuse!.anb !== '' ? Number(results.osseuse!.anb) : null;
  results.classe_squelettique = anb !== null ? 'Non classifiable' : 'Indéterminée';
  results.pattern_vertical = '';

  if (ratio !== null && prn && pogSoft && po && or_) {
    const eLineLs = computeSignedELineDistance(ls, prn, pogSoft, po, or_, ratio);
    const eLineLi = computeSignedELineDistance(li, prn, pogSoft, po, or_, ratio);
    if (eLineLs !== null) results.esthetique!.ligne_e_ls = Math.round(eLineLs * 10) / 10;
    if (eLineLi !== null) results.esthetique!.ligne_e_li = Math.round(eLineLi * 10) / 10;
    // No local E-line threshold is allowed to manufacture a facial-profile diagnosis.
  }

  if (etape2) {
    const { molaire_droite, molaire_gauche, canine_droite, canine_gauche } = etape2.occlusal;
    let moulageText = `Classe Molaire : D:${molaire_droite} / G:${molaire_gauche}\n`;
    moulageText += `Classe Canine : D:${canine_droite} / G:${canine_gauche}\n`;
    results.analyse_moulages_auto = moulageText;
  }

  return results;
}

/**
 * Compatibility export. Automatic treatment generation is deliberately disabled.
 */
export function generateTreatmentPlan(_data: DonneesEtape3): string {
  return '';
}

/**
 * Construit le payload consolidé pour l'API.
 */
export const buildPayload = (
  lms: Landmark[],
  max: number | null,
  mand: number | null,
  real: number | null,
  diag: DiagnosticTexts,
  projections: Record<string, any>,
  ratio: number | null = null,
  etape2: DonneesEtape2 | null = null,
  etape3: DonneesEtape3 | null = null,
) => ({
  landmarks: lms,
  mm_per_pixel: ratio,
  clinical_data: {
    ddm_maxillaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: max ?? 0 },
    ddm_mandibulaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: mand ?? 0 },
    ddm_reelle: real ?? 0,
    plan_traitement: diag.strategie_therapeutique || '',
    classe_molaire_droite: etape2?.occlusal.molaire_droite || null,
    classe_molaire_gauche: etape2?.occlusal.molaire_gauche || null,
    classe_canine_droite: etape2?.occlusal.canine_droite || null,
    classe_canine_gauche: etape2?.occlusal.canine_gauche || null,
    subdivision: etape2?.occlusal.molaire_droite !== etape2?.occlusal.molaire_gauche || etape2?.occlusal.canine_droite !== etape2?.occlusal.canine_gauche,
    forme_arcade: etape2?.type_arcade || null,
    age: etape3?.age !== undefined && etape3.age !== '' ? Number(etape3.age) : null,
    cvm: etape3?.cvm || null,
    denture_type: etape3?.denture_type || null,
    preference_technique: etape3?.preference_technique || null,
  },
  ai_diagnostic: {
    analyse_dentaire: diag.analyse_dentaire,
    diagnostic_squelettique: diag.diagnostic_squelettique,
    analyse_moulages: diag.analyse_moulages,
    synthese_diagnostique: diag.synthese_diagnostique,
    strategie_therapeutique: diag.strategie_therapeutique,
  },
  mcnmara_projections: projections,
});
