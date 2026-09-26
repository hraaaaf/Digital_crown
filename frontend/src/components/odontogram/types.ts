/**
 * Types pour l'odontogramme interactif - Architecture 5 Surfaces
 * Système FDI (ISO 3950) - 11-18, 21-28, 31-38, 41-48
 * Devise: MAD (Dirham Marocain)
 */

export type ToothNumberFDI = 
  | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18  // Haut droit
  | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28  // Haut gauche
  | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38  // Bas gauche
  | 41 | 42 | 43 | 44 | 45 | 46 | 47 | 48; // Bas droit

// Dents de lait (pédiatrique) - Système FDI
export type PediatricToothNumber = 
  | 51 | 52 | 53 | 54 | 55  // Haut droit
  | 61 | 62 | 63 | 64 | 65  // Haut gauche
  | 71 | 72 | 73 | 74 | 75  // Bas gauche
  | 81 | 82 | 83 | 84 | 85; // Bas droit

export type Quadrant = 1 | 2 | 3 | 4;

// Type d'odontogramme (Adulte ou Pédiatrique)
export type OdontogramType = 'ADULT' | 'PEDIATRIC';

/**
 * Surfaces dentaires — deux niveaux :
 *
 * ── ACTIF (rendu SVG + hotzone dans OdontogramSVG.tsx) ──────────────────────
 *   M   Mésiale      — face vers la ligne médiane
 *   D   Distale      — face opposée à la ligne médiane
 *   O   Occlusale    — face masticatrice (postérieures) / Incisale (antérieures)
 *   V   Vestibulaire — face externe (joue/lèvre), alias Buccale
 *   P   Palatine     — face interne (palais/langue), alias Linguale
 *
 * ── LEGACY (données existantes / import externe uniquement) ─────────────────
 *   B   Buccale      → utiliser V à la place dans tout nouveau code
 *   L   Linguale     → utiliser P à la place dans tout nouveau code
 *   I   Incisale     → utiliser O à la place dans tout nouveau code
 *   MOD / MO / DO    Combinaisons multi-surfaces (lecture seule, non rendues)
 *   MV / DV / MP / DP
 *   ALL              Toutes surfaces (ex: couronne complète)
 *
 * ⚠️  OdontogramSVG ne rend que M | D | O | V | P.
 *     Les valeurs legacy sont conservées pour compatibilité avec des données
 *     importées (ex: anciens dossiers patients) mais ne génèrent pas de hotzone.
 */
export type ToothSurface = 'M' | 'D' | 'O' | 'V' | 'P' | 'B' | 'L' | 'I' | 'MOD' | 'MO' | 'DO' | 'MV' | 'DV' | 'MP' | 'DP' | 'ALL';

// État clinique d'une surface individuelle
export type SurfaceState = 
  | 'HEALTHY'           // Sain - blanc
  | 'CARIES'            // Carie - rouge
  | 'CARIES_TO_TREAT'   // Carie à traiter - rouge clair
  | 'FILLING_COMPOSITE' // Composite - bleu
  | 'FILLING_AMALGAM'   // Amalgame - gris
  | 'FILLING_GOLD'      // Or - doré
  | 'FILLING_CERAMIC'   // Céramique - blanc cassé
  | 'RESTORED'          // Restaurée (générique)
  | 'CROWN'             // Couronne - or/céramique
  | 'CROWN_CERAMIC'     // Couronne céramique
  | 'INLAY'             // Inlay
  | 'ONLAY'             // Onlay
  | 'ROOT_CANAL'        // Dévitalisé
  | 'POORLY_TREATED'    // Mal traitée
  | 'IMPLANT'           // Implant
  | 'IMPLANT_CROWN'     // Implant + couronne
  | 'ABSENT'            // Absent
  | 'ABUTMENT'          // Pilier
  | 'FRACTURE'          // Fracture
  | 'SEALANT'           // Sceau de fissure
  | 'SELECTED';         // Sélectionné

// Statut global de la dent (pour compatibilité et états spéciaux)
export type ToothStatus = 
  | 'HEALTHY'
  | 'CARIES'
  | 'CARIES_TO_TREAT'
  | 'FILLING_AMALGAM'
  | 'FILLING_COMPOSITE'
  | 'FILLING_GOLD'
  | 'FILLING_CERAMIC'
  | 'RESTORED'
  | 'CROWN'
  | 'CROWN_CERAMIC'
  | 'ROOT_CANAL'
  | 'ROOT_CANAL_TO_DO'
  | 'POORLY_TREATED'
  | 'POST'
  | 'IMPLANT'
  | 'IMPLANT_CROWN'
  | 'ABUTMENT'
  | 'BRIDGE'
  | 'ABSENT'
  | 'ABSENT_TO_EXTRACT'
  | 'EXTRACTED'
  | 'FRACTURE'
  | 'ROOT_RESIDUE'
  | 'IMPACTED'
  | 'MOBILITY_1'
  | 'MOBILITY_2'
  | 'MOBILITY_3'
  | 'PERIODONTAL_ISSUE'
  | 'SURGERY'
  | 'SEALANT'
  | 'SELECTED';

// État détaillé par surface pour une dent
export interface ToothSurfaceState {
  M: SurfaceState;  // Mésial
  D: SurfaceState;  // Distal
  O: SurfaceState;  // Occlusal (postérieures) / Incisal (antérieures)
  V: SurfaceState;  // Vestibulaire / Buccale
  P: SurfaceState;  // Palatin (maxillaire) / Lingual (mandibule)
}

// État complet d'une dent avec ses surfaces
export interface ToothState {
  number: ToothNumberFDI;
  status: ToothStatus;
  surfaces: ToothSurfaceState;
  treatments?: ToothTreatment[];
  notes?: string;
  mobility?: 0 | 1 | 2 | 3;
  lastUpdated?: string;
}

// État initial par défaut (toutes surfaces saines)
export const DEFAULT_SURFACE_STATE: ToothSurfaceState = {
  M: 'HEALTHY',
  D: 'HEALTHY',
  O: 'HEALTHY',
  V: 'HEALTHY',
  P: 'HEALTHY',
};

export interface ToothTreatment {
  id: string;
  code?: string;
  name: string;
  description?: string;
  category: string;
  catalogActId?: number;
  price: number;
  surfaces?: ToothSurface[];
  suggestedSurfaces?: ToothSurface[];
  duration?: number;
  anesthesia?: boolean;
  requiresXray?: boolean;
  scope?: 'UNITAIRE' | 'MULTIDENTS' | 'GLOBAL';
}



// Données de sélection avec surface spécifique
export interface SelectedSurfaceData {
  toothNumber: number;
  surface: ToothSurface;
  treatments: ToothTreatment[];
  notes?: string;
}

// Ancienne interface (pour compatibilité)
export interface SelectedToothWithTreatment {
  toothNumber: ToothNumberFDI;
  treatments: ToothTreatment[];
  surfaces: ToothSurface[];
  notes?: string;
}

export interface OdontogramData {
  patientId: number;
  teeth: Record<ToothNumberFDI, ToothState>;
  lastUpdated: string;
}

export interface OdontogramConfig {
  readOnly?: boolean;
  showNumbers?: boolean;
  showLegend?: boolean;
  compact?: boolean;
  enableMultiSelect?: boolean;
  highlightSelected?: boolean;
}

export type OdontogramMode = 
  | 'VIEW'
  | 'EDIT_STATUS'
  | 'PLAN_TREATMENT'
  | 'SELECT_FOR_DOCUMENT';

export type OdontogramTool = 
  | 'SELECT'
  | 'HEALTHY'
  | 'CARIES'
  | 'FILLING_COMPOSITE'
  | 'CROWN'
  | 'ABSENT'
  | 'ROOT_CANAL';

// Couleurs pour les surfaces (architecture 5 surfaces)
export const SURFACE_COLORS: Record<SurfaceState, { fill: string; stroke: string; hoverFill: string }> = {
  HEALTHY: { fill: '#ffffff', stroke: '#cbd5e1', hoverFill: '#f1f5f9' },
  CARIES: { fill: '#ef4444', stroke: '#dc2626', hoverFill: '#f87171' },
  CARIES_TO_TREAT: { fill: '#fca5a5', stroke: '#ef4444', hoverFill: '#fecaca' },
  FILLING_AMALGAM: { fill: '#94a3b8', stroke: '#64748b', hoverFill: '#cbd5e1' },
  FILLING_COMPOSITE: { fill: '#0ea5e9', stroke: '#0284c7', hoverFill: '#38bdf8' },
  FILLING_GOLD: { fill: '#fbbf24', stroke: '#d97706', hoverFill: '#fcd34d' },
  FILLING_CERAMIC: { fill: '#f8fafc', stroke: '#94a3b8', hoverFill: '#f1f5f9' },
  RESTORED: { fill: '#60a5fa', stroke: '#2563eb', hoverFill: '#93c5fd' },
  CROWN: { fill: '#fde68a', stroke: '#d97706', hoverFill: '#fef3c7' },
  CROWN_CERAMIC: { fill: '#f8fafc', stroke: '#cbd5e1', hoverFill: '#f1f5f9' },
  INLAY: { fill: '#e0e7ff', stroke: '#6366f1', hoverFill: '#e0e7ff' },
  ONLAY: { fill: '#ddd6fe', stroke: '#7c3aed', hoverFill: '#e9d5ff' },
  ROOT_CANAL: { fill: '#e2e8f0', stroke: '#64748b', hoverFill: '#f1f5f9' },
  POORLY_TREATED: { fill: '#c084fc', stroke: '#9333ea', hoverFill: '#d8b4fe' },
  IMPLANT: { fill: '#94a3b8', stroke: '#475569', hoverFill: '#cbd5e1' },
  IMPLANT_CROWN: { fill: '#f8fafc', stroke: '#64748b', hoverFill: '#f1f5f9' },
  ABSENT: { fill: '#f1f5f9', stroke: '#94a3b8', hoverFill: '#e2e8f0' },
  ABUTMENT: { fill: '#d1d5db', stroke: '#6b7280', hoverFill: '#e5e7eb' },
  FRACTURE: { fill: '#fee2e2', stroke: '#dc2626', hoverFill: '#fecaca' },
  SEALANT: { fill: '#dbeafe', stroke: '#3b82f6', hoverFill: '#bfdbfe' },
  SELECTED: { fill: '#dbeafe', stroke: '#3b82f6', hoverFill: '#bfdbfe' },
};

// Couleurs legacy pour compatibilité
export const STATUS_COLORS: Record<ToothStatus, { fill: string; stroke: string }> = {
  HEALTHY: { fill: '#ffffff', stroke: '#1e293b' },
  CARIES: { fill: '#fee2e2', stroke: '#dc2626' },
  CARIES_TO_TREAT: { fill: '#fecaca', stroke: '#dc2626' },
  FILLING_AMALGAM: { fill: '#94a3b8', stroke: '#475569' },
  FILLING_COMPOSITE: { fill: '#3b82f6', stroke: '#1d4ed8' },
  FILLING_GOLD: { fill: '#fbbf24', stroke: '#d97706' },
  FILLING_CERAMIC: { fill: '#f8fafc', stroke: '#cbd5e1' },
  RESTORED: { fill: '#60a5fa', stroke: '#2563eb' },
  CROWN: { fill: '#fef3c7', stroke: '#d97706' },
  CROWN_CERAMIC: { fill: '#f8fafc', stroke: '#94a3b8' },
  ROOT_CANAL: { fill: '#e2e8f0', stroke: '#475569' },
  ROOT_CANAL_TO_DO: { fill: '#fecaca', stroke: '#dc2626' },
  POORLY_TREATED: { fill: '#c084fc', stroke: '#9333ea' },
  POST: { fill: '#e2e8f0', stroke: '#1e293b' },
  IMPLANT: { fill: '#c0c0c0', stroke: '#64748b' },
  IMPLANT_CROWN: { fill: '#f8fafc', stroke: '#64748b' },
  ABUTMENT: { fill: '#d1d5db', stroke: '#6b7280' },
  BRIDGE: { fill: '#fef3c7', stroke: '#d97706' },
  ABSENT: { fill: '#f1f5f9', stroke: '#94a3b8' },
  ABSENT_TO_EXTRACT: { fill: '#fee2e2', stroke: '#dc2626' },
  EXTRACTED: { fill: '#e2e8f0', stroke: '#64748b' },
  FRACTURE: { fill: '#fee2e2', stroke: '#dc2626' },
  ROOT_RESIDUE: { fill: '#e2e8f0', stroke: '#475569' },
  IMPACTED: { fill: '#fef3c7', stroke: '#d97706' },
  MOBILITY_1: { fill: '#ffffff', stroke: '#22c55e' },
  MOBILITY_2: { fill: '#ffffff', stroke: '#f59e0b' },
  MOBILITY_3: { fill: '#ffffff', stroke: '#dc2626' },
  PERIODONTAL_ISSUE: { fill: '#fef9c3', stroke: '#a16207' },
  SURGERY: { fill: '#ddd6fe', stroke: '#7c3aed' },
  SEALANT: { fill: '#dbeafe', stroke: '#2563eb' },
  SELECTED: { fill: '#dbeafe', stroke: '#3b82f6' },
};

// Labels des surfaces en français
export const SURFACE_LABELS: Record<string, string> = {
  M: 'Mésiale',
  D: 'Distale',
  O: 'Occlusale',
  V: 'Vestibulaire',
  P: 'Palatine',
  B: 'Buccale',
  L: 'Linguale',
  I: 'Incisale',
};

// Noms des dents en français (système FDI)
export const TOOTH_NAMES: Record<ToothNumberFDI, string> = {
  // Quadrant 1 - Haut droit (18→11)
  18: '3ème molaire', 17: '2ème molaire', 16: '1ère molaire',
  15: '2ème prémolaire', 14: '1ère prémolaire', 13: 'Canine',
  12: 'Incisive latérale', 11: 'Incisive centrale',
  // Quadrant 2 - Haut gauche (21→28)
  21: 'Incisive centrale', 22: 'Incisive latérale', 23: 'Canine',
  24: '1ère prémolaire', 25: '2ème prémolaire', 26: '1ère molaire',
  27: '2ème molaire', 28: '3ème molaire',
  // Quadrant 3 - Bas gauche (38→31)
  38: '3ème molaire', 37: '2ème molaire', 36: '1ère molaire',
  35: '2ème prémolaire', 34: '1ère prémolaire', 33: 'Canine',
  32: 'Incisive latérale', 31: 'Incisive centrale',
  // Quadrant 4 - Bas droit (41→48)
  41: 'Incisive centrale', 42: 'Incisive latérale', 43: 'Canine',
  44: '1ère prémolaire', 45: '2ème prémolaire', 46: '1ère molaire',
  47: '2ème molaire', 48: '3ème molaire',
};

// Noms des dents de lait (pédiatrique)
export const PEDIATRIC_TOOTH_NAMES: Record<PediatricToothNumber, string> = {
  // Quadrant 5 - Haut droit
  55: '2ème molaire', 54: '1ère molaire', 53: 'Canine',
  52: 'Incisive latérale', 51: 'Incisive centrale',
  // Quadrant 6 - Haut gauche
  61: 'Incisive centrale', 62: 'Incisive latérale', 63: 'Canine',
  64: '1ère molaire', 65: '2ème molaire',
  // Quadrant 7 - Bas gauche
  75: '2ème molaire', 74: '1ère molaire', 73: 'Canine',
  72: 'Incisive latérale', 71: 'Incisive centrale',
  // Quadrant 8 - Bas droit
  81: 'Incisive centrale', 82: 'Incisive latérale', 83: 'Canine',
  84: '1ère molaire', 85: '2ème molaire',
};

// Ordre d'affichage des dents
export const UPPER_RIGHT_ORDER: ToothNumberFDI[] = [18, 17, 16, 15, 14, 13, 12, 11];
export const UPPER_LEFT_ORDER: ToothNumberFDI[] = [21, 22, 23, 24, 25, 26, 27, 28];
export const LOWER_LEFT_ORDER: ToothNumberFDI[] = [38, 37, 36, 35, 34, 33, 32, 31];
export const LOWER_RIGHT_ORDER: ToothNumberFDI[] = [41, 42, 43, 44, 45, 46, 47, 48];

export const ALL_TEETH_FDI: ToothNumberFDI[] = [
  ...UPPER_RIGHT_ORDER,
  ...UPPER_LEFT_ORDER,
  ...LOWER_LEFT_ORDER,
  ...LOWER_RIGHT_ORDER,
];

// Ordre des dents de lait
export const PEDIATRIC_UPPER_RIGHT: PediatricToothNumber[] = [55, 54, 53, 52, 51];
export const PEDIATRIC_UPPER_LEFT: PediatricToothNumber[] = [61, 62, 63, 64, 65];
export const PEDIATRIC_LOWER_LEFT: PediatricToothNumber[] = [75, 74, 73, 72, 71];
export const PEDIATRIC_LOWER_RIGHT: PediatricToothNumber[] = [81, 82, 83, 84, 85];

export const ALL_TEETH_PEDIATRIC: PediatricToothNumber[] = [
  ...PEDIATRIC_UPPER_RIGHT,
  ...PEDIATRIC_UPPER_LEFT,
  ...PEDIATRIC_LOWER_LEFT,
  ...PEDIATRIC_LOWER_RIGHT,
];

/** @deprecated Faute de frappe conservée pour rétrocompatibilité — utiliser ALL_TEETH_PEDIATRIC */
export const ALL_TEETH_PEDRIATIC = ALL_TEETH_PEDIATRIC;

// Configuration des arcades pour le rendu SVG
export interface ArcadeConfig {
  yOffset: number;
  isUpper: boolean;
  label: string;
  labelY: number;
}

export const ARCADE_CONFIG: Record<number, ArcadeConfig> = {
  1: { yOffset: 45, isUpper: true, label: 'Quadrant 1 (18→11)', labelY: 15 },
  2: { yOffset: 45, isUpper: true, label: 'Quadrant 2 (21→28)', labelY: 15 },
  3: { yOffset: 180, isUpper: false, label: 'Quadrant 3 (38→31)', labelY: 260 },
  4: { yOffset: 180, isUpper: false, label: 'Quadrant 4 (41→48)', labelY: 260 },
};

// ============================================================================
// MAPPING ANATOMIQUE POUR RENDU PHOTOGRAPHIQUE
// Coordonnées en pourcentage (%) par rapport à l'image de référence
// ============================================================================

export interface ToothPosition {
  x: number;  // Position X en % (0-100)
  y: number;  // Position Y en % (0-100)
  r?: number; // Rayon de la hotzone (optionnel, défaut: 3%)
}

// Mapping pour odontogramme adulte (32 dents)
export const ANATOMICAL_MAPPING_ADULT: Record<ToothNumberFDI, ToothPosition> = {
  18:{x:6.28,y:42.01,r:3.8},17:{x:12.26,y:41.57,r:3.8},16:{x:18.78,y:41.33,r:3.8},
  15:{x:24.93,y:41.86,r:3.4},14:{x:31.02,y:41.70,r:3.4},13:{x:36.38,y:41.59,r:3.4},
  12:{x:41.44,y:41.88,r:3.2},11:{x:46.88,y:42.18,r:3.2},21:{x:52.13,y:42.34,r:3.2},
  22:{x:57.31,y:42.09,r:3.2},23:{x:62.96,y:41.67,r:3.4},24:{x:68.45,y:41.73,r:3.4},
  25:{x:74.04,y:41.79,r:3.4},26:{x:79.63,y:41.76,r:3.8},27:{x:85.14,y:41.41,r:3.8},
  28:{x:92.20,y:41.86,r:3.8},
  48:{x:6.19,y:58.08,r:3.8},47:{x:12.27,y:58.33,r:3.8},46:{x:18.46,y:58.45,r:3.8},
  45:{x:24.55,y:58.58,r:3.4},44:{x:30.53,y:58.08,r:3.4},43:{x:35.84,y:58.20,r:3.4},
  42:{x:40.75,y:57.96,r:3.2},41:{x:46.37,y:58.03,r:3.2},31:{x:51.62,y:57.71,r:3.2},
  32:{x:56.83,y:58.02,r:3.2},33:{x:62.02,y:58.20,r:3.4},34:{x:67.35,y:58.17,r:3.4},
  35:{x:72.96,y:58.11,r:3.4},36:{x:79.27,y:58.60,r:3.8},37:{x:85.55,y:58.17,r:3.8},
  38:{x:92.39,y:58.17,r:3.8},
};

// Mapping pour odontogramme pédiatrique (20 dents de lait)
export const ANATOMICAL_MAPPING_PEDIATRIC: Record<PediatricToothNumber, ToothPosition> = {
  55:{x:8.46,y:41.16,r:4.6},54:{x:18.25,y:40.54,r:4.6},53:{x:28.13,y:40.92,r:4.2},
  52:{x:36.73,y:41.23,r:4.0},51:{x:45.30,y:41.92,r:4.0},61:{x:54.62,y:41.85,r:4.0},
  62:{x:63.20,y:41.22,r:4.0},63:{x:71.86,y:40.91,r:4.2},64:{x:81.88,y:40.52,r:4.6},
  65:{x:91.61,y:41.19,r:4.6},
  85:{x:8.32,y:61.31,r:4.6},84:{x:18.27,y:61.62,r:4.6},83:{x:28.66,y:61.56,r:4.2},
  82:{x:37.04,y:61.61,r:4.0},81:{x:45.36,y:61.07,r:4.0},71:{x:54.59,y:61.04,r:4.0},
  72:{x:62.96,y:61.60,r:4.0},73:{x:71.31,y:61.54,r:4.2},74:{x:81.72,y:61.59,r:4.6},
  75:{x:91.66,y:61.33,r:4.6},
};

// Export combiné pour utilisation générique
export const ANATOMICAL_MAPPING = {
  ADULT: ANATOMICAL_MAPPING_ADULT,
  PEDIATRIC: ANATOMICAL_MAPPING_PEDIATRIC,
};

// Chemins des images de référence
export const ODONTOGRAM_IMAGES = {
  ADULT: '/assets/odontogram/digital-crown-adult-reference-v2.png',
  PEDIATRIC: '/assets/odontogram/digital-crown-child-reference-v2.png',
};
