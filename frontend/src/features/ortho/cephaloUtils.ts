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
 * Calcule l'angle inter-incisif (1/1).
 */
export function computeInterIncisalAngle(u1i: Landmark, u1a: Landmark, l1i: Landmark, l1a: Landmark): number {
  return 180 - computeAngle(u1i, u1a, l1i, l1a);
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
 * Automate Step 3 data based on current landmarks, patient info, and Step 2 data.
 */
/**
 * Distance d'un point à une droite définie par deux points.
 */
export function computeDistanceToLine(p: Landmark, l1: Landmark, l2: Landmark, ratio: number, signed: boolean = false): number {
  const x0 = p.x; const y0 = p.y;
  const x1 = l1.x; const y1 = l1.y;
  const x2 = l2.x; const y2 = l2.y;
  
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

export function computeStep3Data(lms: Landmark[], age: number | '', sexe: 'M' | 'F', mmPerPixel: number | null, etape2: DonneesEtape2 | null = null): Partial<DonneesEtape3> {


  const g = (id: string) => lms.find(l => l.id.toLowerCase() === id.toLowerCase());
  const po = g('po'); const or_ = g('or'); const n = g('n');
  const a = g('a'); const b = g('b'); const s = g('s');
  const go = g('go'); const me = g('me');
  const sn = g('sn_soft') || g('sn'); const prn = g('prn') || g('nose_tip');
  const ls = g('ls_soft') || g('ls') || g('ul');
  const li = g('li_soft') || g('li') || g('ll'); const pogSoft = g('pog_soft') || g('stpog');
  const u1i = g('u1_incisal') || g('u1i');
  const u1a = g('u1_apex') || g('u1a');
  const l1i = g('l1_incisal') || g('l1i');
  const l1a = g('l1_apex') || g('l1a');

  const ratio = mmPerPixel;
  const results: Partial<DonneesEtape3> = {
    age: age,
    cvm: estimateCVM(age, sexe) || 'CS1',
    denture_type: age !== '' ? (age < 6 ? 'TEMPORAIRE' : age < 12 ? 'MIXTE' : 'PERMANENTE') : 'PERMANENTE',
    dentaire: {
      surplomb: '',
      recouvrement: '',
      impa: '',
      i_francfort: '',
      inter_incisif: ''
    },
    osseuse: {
      angle_tweed: '',
      decalage_ab: '',
      situation_a: '',
      situation_b: '',
      profondeur_faciale: '',
      sna: '',
      snb: '',
      anb: ''
    },
    esthetique: {
      ligne_e_ls: '',
      ligne_e_li: '',
      angle_nasolabial: ''
    }
  };

  // --- 1. CALCULS SYSTÉMATIQUES (TOUTES ANALYSES) ---
  
  // A. Tweed & Verticalité
  // pattern_vertical is no longer derived from a local fma<20/>30 threshold
  // here (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C) — it
  // stays unset (''), the same neutral state the type already models for
  // "not computed", since PatternVertical is a closed literal union and no
  // consumer needs to distinguish "present but unclassified" from "absent"
  // the way classe_squelettique's ANB fix did.
  if (po && or_ && go && me) {
    const fma = computeAngle(po, or_, go, me);
    results.osseuse!.angle_tweed = Math.round(fma);
  }

  // B. Steiner (ANB)
  if (s && n && a && b) {
    const sna = computeAngle(n, s, n, a);
    const snb = computeAngle(n, s, n, b);
    results.osseuse!.sna = Math.round(sna * 10) / 10;
    results.osseuse!.snb = Math.round(snb * 10) / 10;
    results.osseuse!.anb = Math.round((sna - snb) * 10) / 10;
  }

  // C. McNamara / COM (Projections FH)
  if (ratio !== null && s && n && po && or_) {
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

  // D. Dentaire (IMPA, Inter-incisif, Tweed specific, Steiner specific)
  if (u1i && u1a && l1i && l1a) {
    results.dentaire!.inter_incisif = Math.round(computeInterIncisalAngle(u1i, u1a, l1i, l1a));
    
    // Steiner specific (1/NA, 1/NB)
    if (n && a) {
      results.dentaire!.i_na_angle = Math.round(computeAngle(n, a, u1a, u1i));
      if (ratio !== null) results.dentaire!.i_na_mm = Math.round(computeDistanceToLine(u1i, n, a, ratio) * 10) / 10;
    }
    if (n && b) {
      results.dentaire!.i_nb_angle = Math.round(computeAngle(n, b, l1a, l1i));
      if (ratio !== null) results.dentaire!.i_nb_mm = Math.round(computeDistanceToLine(l1i, n, b, ratio) * 10) / 10;
    }
  }

  if (l1i && l1a && go && me) {
    results.dentaire!.impa = computeLocalImpa(lms) || '';
  }

  if (po && or_ && l1i && l1a) {
    const fmia = computeAngle(po, or_, l1a, l1i);
    results.dentaire!.fmia = Math.round(fmia);
  }

  if (u1i && u1a && po && or_) {
    results.dentaire!.i_francfort = computeAngle(u1a, u1i, po, or_);
  }

  if (ratio !== null && u1i && l1i && po && or_) {
    const overjet = computeDistanceToVertical(l1i, u1i, po, or_, ratio);
    results.dentaire!.surplomb = Math.round(Math.abs(overjet) * 10) / 10;
    const overbite = computeSignedOverbite(u1i, l1i, po, or_, ratio);
    if (overbite !== null) results.dentaire!.recouvrement = overbite;
  }

  // --- 2. LOGIQUE DE CONSENSUS SQUELETTIQUE ---
  // ANB ne classifie plus localement (CEPHALOMETRY-FRONTEND-AUTHORITY-REMOVAL-4B) :
  // seul le service normatif backend peut produire une classification autoritative, et le
  // registre actuel n'a aucun profil Steiner validé. "Indéterminée" reste réservé à
  // l'absence de valeur ANB ; "Non classifiable" distingue explicitement le cas où ANB
  // existe mais n'a pas de classification autoritative (pas une donnée manquante).
  const anb = results.osseuse!.anb !== '' ? Number(results.osseuse!.anb) : null;
  results.classe_squelettique = anb !== null ? 'Non classifiable' : 'Indéterminée';
  // Analyse Dentaire COM
  if (u1i && u1a && l1i && l1a) {
    results.dentaire!.inter_incisif = Math.round(computeInterIncisalAngle(u1i, u1a, l1i, l1a));
  }
  if (ratio !== null && u1i && l1i && po && or_) {
    const overjet = computeDistanceToVertical(l1i, u1i, po, or_, ratio);
    results.dentaire!.surplomb = Math.round(Math.abs(overjet) * 10) / 10;
    
    const overbite = computeSignedOverbite(u1i, l1i, po, or_, ratio);
    if (overbite !== null) results.dentaire!.recouvrement = overbite;
  }

  if (l1i && l1a && go && me) {
    results.dentaire!.impa = computeLocalImpa(lms) || '';
  }
  if (u1i && u1a && po && or_) {
    results.dentaire!.i_francfort = computeAngle(u1a, u1i, po, or_);
  }

  // Analyse Esthétique
  if (ratio !== null && prn && pogSoft && po && or_) {
    const eLineLs = computeSignedELineDistance(ls, prn, pogSoft, po, or_, ratio);
    const eLineLi = computeSignedELineDistance(li, prn, pogSoft, po, or_, ratio);
    if (eLineLs !== null) results.esthetique!.ligne_e_ls = Math.round(eLineLs * 10) / 10;
    if (eLineLi !== null) results.esthetique!.ligne_e_li = Math.round(eLineLi * 10) / 10;
    
    if (results.esthetique?.ligne_e_ls !== undefined && results.esthetique.ligne_e_ls !== '') {
      const ls_e = Number(results.esthetique.ligne_e_ls);
      if (ls_e > 2) results.profil = 'convexe';
      else if (ls_e < -4) results.profil = 'concave';
      else results.profil = 'droit';
    }
  }

  // Automatisation Analyse Moulage (depuis Étape 2)
  if (etape2) {
    const { molaire_droite, molaire_gauche, canine_droite, canine_gauche } = etape2.occlusal;
    let moulageText = `Classe Molaire : D:${molaire_droite} / G:${molaire_gauche}\n`;
    moulageText += `Classe Canine : D:${canine_droite} / G:${canine_gauche}\n`;
    results.analyse_moulages_auto = moulageText;
  }

  return results;


}


/**
 * Génère un plan de traitement orthodontique contemporain (Damon / Invisalign)
 */
export function generateTreatmentPlan(data: DonneesEtape3): string {
  // classe_squelettique/division are no longer read here: ANB stopped classifying locally
  // (CEPHALOMETRY-FRONTEND-AUTHORITY-REMOVAL-4B) and the skeletal-strategy branch that
  // consumed them was removed below, not merely disabled. pattern_vertical is no longer
  // read either, for the same reason applied to Tweed (CEPHALOMETRY-NORMATIVE-BACKEND-
  // WIRING-TWEED-IMPA-FRANCFORT-4C) — the vertical-control branch below was removed too.
  const { cvm, severite_ddm: ddmSev } = data;
  const impa = data.dentaire.impa === '' ? 90 : Number(data.dentaire.impa);
  const ifranc = data.dentaire.i_francfort === '' ? 107 : Number(data.dentaire.i_francfort);

  const denture_type = data.denture_type || '';
  const isMixteOrPediatric = denture_type === 'MIXTE' || denture_type === 'TEMPORAIRE';

  let plan = '';
  const isChild = cvm && ['CS1', 'CS2', 'CS3', 'CS4'].includes(cvm);

  if (isMixteOrPediatric) {
    plan += '⚠️ **DENTURE MIXTE / PATIENT EN CROISSANCE**\n';
    plan += 'Compte tenu de l\'âge et de la denture mixte, le plan thérapeutique doit être orienté vers une évaluation interceptive et une surveillance de croissance.\n';
    plan += 'La prescription d\'appareillage fixe multi-attaches (type Damon, High Torque) est prématurée à ce stade et doit être différée à la denture permanente.\n\n';
  }
  
  // 1. DÉCISION D'EXTRACTION (Logique Scientifique Moderne)
  // En méthode Damon, on extrait très rarement. Seulement si biprotrusion sévère ou IMPA critique.
  let indicateExtraction = false;
  if (ddmSev === 'sévère' && impa > 95) indicateExtraction = true;
  if (ifranc > 120 && impa > 100) indicateExtraction = true; // Biproalvéolie vraie
  
  if (indicateExtraction) {
    plan += '🔴 **INDICATIONS EXTRACTIONNELLES**\n';
    plan += '• DDM sévère avec protrusion (IMPA > 95° / I/F > 120°).\n';
    plan += '\n';
  } else {
    plan += '🟢 **PROTOCOLE NON-EXTRACTIONNEL (BONE ADAPTATION)**\n';
    if (ddmSev === 'modéré' || ddmSev === 'sévère') {
      plan += '• Résolution de l\'encombrement par expansion transversale et pro-inclinaison contrôlée.\n';
    }
    plan += '\n';
  }

  // 2. CHOIX TECHNOLOGIQUE (Damon vs Invisalign) — différé si denture mixte
  if (!isMixteOrPediatric) {
    plan += '⚙️ **CHOIX DU DISPOSITIF & BIOMÉCANIQUE**\n';
    if (indicateExtraction) {
      plan += '• **Option A : Méthode Classique (Ligatures actives)**\n';
      plan += '  - Recommandée pour le contrôle rigoureux du torque radiculaire (rétraction incisive).\n';
      plan += '  - Arcs acier forte section pour mécanique de glissement.\n';
      plan += '• **Option B : Invisalign (Cas Complexe)**\n';
      plan += '  - Taquets d\'ancrage maximum (G6) pour rétraction en masse.\n';
    } else {
      plan += '• **Option A : Méthode Damon Passive (Gold Standard)**\n';
      plan += '  - Forces légères, auto-ligaturant passif (sans friction).\n';
      plan += '  - Privilégie l\'expansion alvéolaire (arcs CuNiTi larges) pour corriger la DDM.\n';
      plan += '• **Option B : Aligneurs (Invisalign)**\n';
      plan += '  - Expansion séquentielle programmée via ClinCheck.\n';
      if (ddmSev === 'modéré') plan += '  - IPR (Stripping) localisé si nécessaire pour éviter la vestibulo-version.\n';
    }
    plan += '\n';
  }

  // 3. GESTION SQUELETTIQUE & OCCLUSALE
  // ANB ne classifie plus localement (CEPHALOMETRY-FRONTEND-AUTHORITY-REMOVAL-4B) : classe
  // ne vaut plus jamais "Classe I/II/III" (voir computeStep3Data ci-dessus), donc aucune
  // décision squelettique/chirurgicale n'est plus dérivée localement d'ANB. Explicite plutôt
  // que silencieusement vide, conformément au principe "RAW_ONLY/UNAVAILABLE plutôt qu'une
  // conclusion inventée" — aucun seuil ANB (8, -4, 4.5, 0) n'est réintroduit ni remplacé.
  plan += '🦴 **STRATÉGIE SQUELETTIQUE (' + (isChild ? 'En Croissance' : 'Adulte') + ')**\n';
  plan += '• Classification squelettique non disponible (ANB non interprété par le référentiel normatif).\n';

  // 4. GESTION VERTICALE
  // Tweed no longer classifies locally (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-
  // TWEED-IMPA-FRANCFORT-4C) — no fma threshold (20, 30) is reintroduced or
  // replaced, same "RAW_ONLY/UNAVAILABLE rather than an invented conclusion"
  // principle as the skeletal-strategy section above.
  plan += '\n📏 **GESTION VERTICALE**\n';
  plan += '• Typologie verticale non disponible (Tweed non interprété par le référentiel normatif).\n';

  return plan;
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
    forme_arcade: etape2?.type_arcade || null,
    age: (etape3?.age !== undefined && etape3.age !== '') ? Number(etape3.age) : null,
    cvm: etape3?.cvm || null,
    denture_type: etape3?.denture_type || null,
    preference_technique: etape3?.preference_technique || null
  },
  ai_diagnostic: {
    analyse_dentaire: diag.analyse_dentaire,
    diagnostic_squelettique: diag.diagnostic_squelettique,
    analyse_moulages: diag.analyse_moulages,
    synthese_diagnostique: diag.synthese_diagnostique,
    strategie_therapeutique: diag.strategie_therapeutique
  },
  mcnmara_projections: projections
});
