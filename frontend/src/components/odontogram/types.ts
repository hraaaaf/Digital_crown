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
  category: 'PREVENTION' | 'CONSERVATRICE' | 'ENDODONTIE' | 'PARODONTOLOGIE' | 
            'CHIRURGIE' | 'PROTHESE' | 'ORTHODONTIE' | 'ESTHETIQUE';
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
  // Quadrant 1 - Haut gauche (11→18) — coordonnées calibrées sur image réelle
  11: { x: 42.53, y: 6.01,  r: 3   },
  12: { x: 34.97, y: 8.42,  r: 3   },
  13: { x: 26.94, y: 12.86, r: 3.5 },
  14: { x: 21.98, y: 17.56, r: 3.5 },
  15: { x: 18.67, y: 21.99, r: 3.5 },
  16: { x: 17.01, y: 27.5,  r: 4   },
  17: { x: 13.71, y: 35.16, r: 4   },
  18: { x: 12.76, y: 42.69, r: 4   },

  // Quadrant 2 - Haut droit (21→28)
  21: { x: 53.17, y: 6.14,  r: 3   },
  22: { x: 60.73, y: 8.02,  r: 3   },
  23: { x: 67.82, y: 11.92, r: 3.5 },
  24: { x: 74.67, y: 17.16, r: 3.5 },
  25: { x: 76.8,  y: 21.59, r: 3.5 },
  26: { x: 80.82, y: 27.64, r: 4   },
  27: { x: 84.12, y: 34.92, r: 4   },
  28: { x: 83.18, y: 42.04, r: 4   },

  // Quadrant 3 - Bas droit (31→38)
  31: { x: 54.35, y: 93.61, r: 3   },
  32: { x: 61.67, y: 90.38, r: 3   },
  33: { x: 69.24, y: 86.35, r: 3.5 },
  34: { x: 73.49, y: 82.46, r: 3.5 },
  35: { x: 79.87, y: 77.22, r: 3.5 },
  36: { x: 81.29, y: 71.44, r: 4   },
  37: { x: 82.94, y: 64.05, r: 4   },
  38: { x: 84.83, y: 56.39, r: 4   },

  // Quadrant 4 - Bas gauche (41→48)
  41: { x: 42.77, y: 93.34, r: 3   },
  42: { x: 35.92, y: 90.71, r: 3   },
  43: { x: 28.36, y: 87.21, r: 3.5 },
  44: { x: 21.27, y: 81.84, r: 3.5 },
  45: { x: 18.43, y: 77.14, r: 3.5 },
  46: { x: 16.07, y: 70.96, r: 4   },
  47: { x: 12.29, y: 63.43, r: 4   },
  48: { x: 11.11, y: 56.18, r: 4   },
};

// Mapping pour odontogramme pédiatrique (20 dents de lait)
export const ANATOMICAL_MAPPING_PEDIATRIC: Record<PediatricToothNumber, ToothPosition> = {
  // Quadrant 5 - Haut droit (55→51) — coordonnées calibrées sur image réelle
  55: { x: 11.81, y: 39.97, r: 3.5 },
  54: { x: 17.96, y: 30.99, r: 3.5 },
  53: { x: 24.1,  y: 22.01, r: 3.5 },
  52: { x: 32.14, y: 16.97, r: 3   },
  51: { x: 43.01, y: 13.19, r: 3   },

  // Quadrant 6 - Haut gauche (61→65)
  61: { x: 58.84, y: 13.03, r: 3   },
  62: { x: 65.93, y: 16.34, r: 3   },
  63: { x: 76.09, y: 22.32, r: 3.5 },
  64: { x: 81.52, y: 29.57, r: 3.5 },
  65: { x: 85.54, y: 39.65, r: 3.5 },

  // Quadrant 7 - Bas gauche (75→71)
  75: { x: 86.25, y: 59.03, r: 3.5 },
  74: { x: 82.23, y: 68.64, r: 3.5 },
  73: { x: 76.09, y: 75.88, r: 3.5 },
  72: { x: 66.64, y: 81.24, r: 3   },
  71: { x: 54.58, y: 84.86, r: 3   },

  // Quadrant 8 - Bas droit (81→85)
  81: { x: 41.82, y: 84.39, r: 3   },
  82: { x: 31.9,  y: 82.03, r: 3   },
  83: { x: 23.63, y: 76.2,  r: 3.5 },
  84: { x: 15.83, y: 68.64, r: 3.5 },
  85: { x: 10.87, y: 59.03, r: 3.5 },
};

// Export combiné pour utilisation générique
export const ANATOMICAL_MAPPING = {
  ADULT: ANATOMICAL_MAPPING_ADULT,
  PEDIATRIC: ANATOMICAL_MAPPING_PEDIATRIC,
};

// Chemins des images de référence
export const ODONTOGRAM_IMAGES = {
  ADULT: '/assets/odontogram/adult-anatomical.jpg',
  PEDIATRIC: '/assets/odontogram/pediatric-anatomical.jpg',
};
