import type { Landmark } from './CephaloTracingLayer';

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
export type CVMStage = 'CS1' | 'CS2' | 'CS3' | 'CS4' | 'CS5' | 'CS6';

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
    const mandAngle = Math.atan2(me.y - go.y, me.x - go.x);
    const toothAngle = mandAngle - Math.PI / 2;
    const l1a = { id: 'L1_apex', x: Math.round((l1i.x + TOOTH_LENGTH * Math.cos(toothAngle)) * 100) / 100, y: Math.round((l1i.y + TOOTH_LENGTH * Math.sin(toothAngle)) * 100) / 100 };
    const idx = newLandmarks.findIndex(l => l.id === 'L1_apex');
    if (idx >= 0) newLandmarks[idx] = l1a; else newLandmarks.push(l1a);
  }
  
  if (u1i && po && or_) {
    const fhAngle = Math.atan2(or_.y - po.y, or_.x - po.x);
    const toothAngle = fhAngle - (107 * Math.PI / 180);
    const u1a = { id: 'U1_apex', x: Math.round((u1i.x + TOOTH_LENGTH * Math.cos(toothAngle)) * 100) / 100, y: Math.round((u1i.y + TOOTH_LENGTH * Math.sin(toothAngle)) * 100) / 100 };
    const idx = newLandmarks.findIndex(l => l.id === 'U1_apex');
    if (idx >= 0) newLandmarks[idx] = u1a; else newLandmarks.push(u1a);
  }
  
  return newLandmarks;
}
