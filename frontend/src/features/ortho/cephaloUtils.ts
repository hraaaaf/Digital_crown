import type { Landmark, CVMStage } from './cephaloShared';
import type { DiagnosticTexts, DonneesEtape2, DonneesEtape3 } from './cephaloTypes';

/**
 * Calcule la DDM Réelle selon la convention COM.
 */
export function calcDDMReelle(ddmClinique: number | '', valeurActuelle: number | null, norme: number = 90): number | null {
  if (ddmClinique === '' || valeurActuelle === null) return null;
  const ddmCephalo = (valeurActuelle - norme) / 2.5;
  return Number(ddmClinique) + ddmCephalo;
}

/**
 * Calcule l'impact céphalométrique sur la DDM.
 */
export function calcDDMCephalo(impa: number | null): number | null {
  if (impa === null) return null;
  return (impa - 90) / 2.5;
}

/**
 * Calcule le stade CVM estimé selon Baccetti basé sur l'âge et le sexe.
 */

export function estimateCVM(age: number | '', sexe: 'M' | 'F'): CVMStage | '' {
  if (age === '') return '';
  if (sexe === 'F') {
    if (age < 9.5) return 'CS1';
    if (age < 10.5) return 'CS2';
    if (age >= 10.5 && age < 12) return 'CS3';
    if (age >= 12 && age < 13.5) return 'CS4';
    if (age >= 13.5 && age < 15) return 'CS5';
    return 'CS6';
  } else {
    if (age < 10.5) return 'CS1';
    if (age < 11.5) return 'CS2';
    if (age >= 11.5 && age < 13.5) return 'CS3';
    if (age >= 13.5 && age < 15) return 'CS4';
    if (age >= 15 && age < 17) return 'CS5';
    return 'CS6';
  }
}

/**
 * Calcule l'IMPA local basé sur les points actuels du tracé.
 */
export function computeLocalImpa(lms: Landmark[]): number | null {
  const g  = (id: string) => lms.find(l => l.id === id);
  const l1i = g('L1_incisal');
  const l1a = g('L1_apex');
  const go  = g('Go');
  const me  = g('Me');
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
export function computeAngle(p1: {x:number, y:number}, p2: {x:number, y:number}, p3: {x:number, y:number}, p4: {x:number, y:number}): number {
  const dx1 = p2.x - p1.x; const dy1 = p2.y - p1.y;
  const dx2 = p4.x - p3.x; const dy2 = p4.y - p3.y;
  const m1 = Math.sqrt(dx1*dx1 + dy1*dy1);
  const m2 = Math.sqrt(dx2*dx2 + dy2*dy2);
  if (m1 < 0.1 || m2 < 0.1) return 0;
  const cos = Math.max(-1, Math.min(1, (dx1*dx2 + dy1*dy2) / (m1*m2)));
  return Math.round(Math.acos(cos) * (180 / Math.PI) * 10) / 10;
}

/**
 * Calcule la distance signée d'un point à une ligne perpendiculaire à une autre.
 * Utilisé pour McNamara (distance à la verticale de Nasion).
 */
export function computeDistanceToVertical(target: {x:number, y:number}, origin: {x:number, y:number}, refA: {x:number, y:number}, refB: {x:number, y:number}, ratio: number = 1): number {
  // Ligne de référence (ex: Francfort Po-Or)
  const dx = refB.x - refA.x; const dy = refB.y - refA.y;
  const len = Math.sqrt(dx*dx + dy*dy);
  if (len < 0.1) return 0;
  
  // Vecteur directeur normalisé de Francfort
  const ux = dx / len; const uy = dy / len;
  
  // Vecteur de origin à target
  const vx = target.x - origin.x; const vy = target.y - origin.y;
  
  // Projection de V sur U (distance le long de Francfort)
  const dist = (vx * ux + vy * uy);
  return dist * ratio;
}

/**
 * Projections McNamara (N', A', B') sur le plan de Francfort.
 */
export function computeMcNamaraProjections(lms: Landmark[]): { N_prime?: [number, number]; A_prime?: [number, number]; B_prime?: [number, number] } {
  const g = (id: string) => lms.find(l => l.id === id);
  const po = g('Po');
  const or_ = g('Or');
  const n = g('N');
  const a = g('A');
  const b = g('B');
  
  if (!po || !or_) return {};
  
  const projections: { N_prime?: [number, number]; A_prime?: [number, number]; B_prime?: [number, number] } = {};
  
  const project = (px: number, py: number, ax: number, ay: number, bx: number, by: number): [number, number] | null => {
    const dx = bx - ax; const dy = by - ay;
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
  if (v === null) return '-';
  return (v >= 0 ? '+' : '') + v.toFixed(dec);
}

/**
 * Initialisation des apex par défaut si manquants.
 */
export function initializeDefaultApexes(landmarks: Landmark[]): Landmark[] {
  const g = (id: string) => landmarks.find(l => l.id === id);
  const u1i = g('U1_incisal');
  const l1i = g('L1_incisal');
  const go = g('Go');
  const me = g('Me');
  const po = g('Po');
  const or_ = g('Or');
  
  const newLandmarks = [...landmarks];
  const TOOTH_LENGTH = 85; 
  
  if (l1i && go && me) {
    const dx = me.x - go.x;
    const dy = me.y - go.y;
    const len = Math.hypot(dx, dy);
    if (len > 0) {
      const nx = dx / len;
      const ny = dy / len;
      const signX = nx >= 0 ? 1 : -1;
      const perpX = -ny * signX;
      const perpY = nx * signX;
      
      const l1a = { 
        id: 'L1_apex', 
        x: Math.round((l1i.x + TOOTH_LENGTH * perpX) * 100) / 100, 
        y: Math.round((l1i.y + TOOTH_LENGTH * perpY) * 100) / 100 
      };
      const idx = newLandmarks.findIndex(l => l.id === 'L1_apex');
      if (idx >= 0) newLandmarks[idx] = l1a; else newLandmarks.push(l1a);
    }
  }
  
  if (u1i && po && or_) {
    const dx = or_.x - po.x;
    const dy = or_.y - po.y;
    const fhAngle = Math.atan2(dy, dx);
    const toothAngle = dx >= 0 
      ? fhAngle - (107 * Math.PI / 180) 
      : fhAngle + (107 * Math.PI / 180);
      
    const u1a = { 
      id: 'U1_apex', 
      x: Math.round((u1i.x + TOOTH_LENGTH * Math.cos(toothAngle)) * 100) / 100, 
      y: Math.round((u1i.y + TOOTH_LENGTH * Math.sin(toothAngle)) * 100) / 100 
    };
    const idx = newLandmarks.findIndex(l => l.id === 'U1_apex');
    if (idx >= 0) newLandmarks[idx] = u1a; else newLandmarks.push(u1a);
  }
  
  return newLandmarks;
}

/**
 * Automate Step 3 data based on current landmarks and patient info.
 */
export function computeStep3Data(lms: Landmark[], age: number | '', sexe: 'M' | 'F', mmPerPixel: number | null): Partial<DonneesEtape3> {
  const g = (id: string) => lms.find(l => l.id.toLowerCase() === id.toLowerCase());
  const po = g('po'); const or_ = g('or'); const n = g('n');
  const a = g('a'); const b = g('b'); const s = g('s');
  const go = g('go'); const me = g('me');
  const sn = g('sn'); const prn = g('prn') || g('nose_tip');
  const cm = g('cm'); const ls = g('ls') || g('ul');
  const li = g('li') || g('ll'); const pogSoft = g('pog_soft') || g('stpog');

  const ratio = mmPerPixel || 0.1; // Fallback to 0.1 if not calibrated
  const results: Partial<DonneesEtape3> = {
    age: age,
    cvm: estimateCVM(age, sexe) || 'CS1',
    denture_type: age !== '' ? (age < 6 ? 'TEMPORAIRE' : age < 12 ? 'MIXTE' : 'PERMANENTE') : 'PERMANENTE',
  };

  // Analyse Osseuse
  if (po && or_ && go && me) {
    const fma = computeAngle(po, or_, go, me);
    results.osseuse = { ...results.osseuse, angle_tweed: Math.round(fma) } as any;
    
    // Synthèse Verticalité
    if (fma < 20) results.pattern_vertical = 'hypodivergent';
    else if (fma > 30) results.pattern_vertical = 'hyperdivergent';
    else results.pattern_vertical = 'normodivergent';
  }

  if (s && n) {
    if (a) {
      const sna = computeAngle(s, n, n, a);
      results.osseuse = { ...results.osseuse, sna: Math.round(sna * 10) / 10 } as any;
    }
    if (b) {
      const snb = computeAngle(s, n, n, b);
      results.osseuse = { ...results.osseuse, snb: Math.round(snb * 10) / 10 } as any;
    }
    if (results.osseuse?.sna && results.osseuse?.snb) {
      const anb = Math.round((results.osseuse.sna - results.osseuse.snb) * 10) / 10;
      results.osseuse.anb = anb;
      
      // Synthèse Classe Squelettique
      if (anb < 0) results.classe_squelettique = 'Classe III';
      else if (anb > 4) results.classe_squelettique = 'Classe II';
      else results.classe_squelettique = 'Classe I';
    }
  }

  if (po && or_ && n) {
    if (a) {
      const distA = computeDistanceToVertical(a, n, po, or_, ratio);
      results.osseuse = { ...results.osseuse, situation_a: Math.round(distA * 10) / 10 } as any;
    }
    if (b) {
      const distB = computeDistanceToVertical(b, n, po, or_, ratio);
      results.osseuse = { ...results.osseuse, situation_b: Math.round(distB * 10) / 10 } as any;
    }
    if (a && b) {
      const distA = computeDistanceToVertical(a, n, po, or_, ratio);
      const distB = computeDistanceToVertical(b, n, po, or_, ratio);
      results.osseuse = { ...results.osseuse, decalage_ab: Math.round((distA - distB) * 10) / 10 } as any;
    }
    if (s) {
      const distS = computeDistanceToVertical(s, n, po, or_, ratio);
      results.osseuse = { ...results.osseuse, profondeur_faciale: Math.round(Math.abs(distS) * 10) / 10 } as any;
    }
  }

  // Analyse Esthétique
  if (prn && pogSoft) {
    const projectOnE = (p: {x:number, y:number}) => computeDistanceToVertical(p, pogSoft, pogSoft, prn, ratio);
    if (ls) results.esthetique = { ...results.esthetique, ligne_e_ls: Math.round(projectOnE(ls) * 10) / 10 } as any;
    if (li) results.esthetique = { ...results.esthetique, ligne_e_li: Math.round(projectOnE(li) * 10) / 10 } as any;
    
    // Synthèse Profil
    if (results.esthetique?.ligne_e_ls !== undefined) {
      const ls_e = Number(results.esthetique.ligne_e_ls);
      if (ls_e > 0) results.profil = 'convexe';
      else if (ls_e < -4) results.profil = 'concave';
      else results.profil = 'droit';
    }
  }

  if (cm && sn && ls) {
    const angleNL = computeAngle(cm, sn, sn, ls);
    results.esthetique = { ...results.esthetique, angle_nasolabial: Math.round(angleNL) } as any;
  }

  return results;
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
  etape3: DonneesEtape3 | null = null
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
    forme_arcade: etape3?.type_arcade || null,
    age: (etape3?.age !== undefined && etape3.age !== '') ? Number(etape3.age) : null,
    cvm: etape3?.cvm || null,
    denture_type: etape3?.denture_type || null,
    preference_technique: etape3?.preference_technique || null
  },
  ai_diagnostic: {
    diagnostic_squelettique: diag.diagnostic_squelettique,
    analyse_moulages: diag.analyse_moulages,
    synthese_diagnostique: diag.synthese_diagnostique,
    strategie_therapeutique: diag.strategie_therapeutique
  },
  mcnmara_projections: projections
});
