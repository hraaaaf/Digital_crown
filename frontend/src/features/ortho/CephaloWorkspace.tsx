/**
 * CephaloWorkspace.tsx  *  v4.2  *  Digital Crown - Studio COM
 * 
 * Composant central du workflow d'analyse céphalométrique en 4 étapes.
 *
 * Architecture :
 *   * Optimistic Update Pattern  - state local source de vérité, sync backend 600ms debounce
 *   * Payload Consolidé          - schemas.py AnalysisUpdate strict (landmarks + clinical_data + ai_diagnostic)
 *   * Sauvegarde silencieuse     - déclenchée automatiquement lors du changement d'étape
 *   * Mathématiques cliniques    - IMPA L1/Plan Mandibulaire (Go*Me), 180-rawAngle
 *                                   DDM Cephalo = (90 - IMPA) * 0.8, DDM Réelle = Mand + Cephalo
 *   * SLM Integration            - /patients/{id}/ai-diagnostic (ai_advisor.py)
 *                                   Fallback heuristique transparent côté backend
 *   * PDF Gate                   - bouton bloqué si REQUIRED_LANDMARKS incomplets
 *   * Dual theme                 - light / dark via PALETTE
 *   * CALIBRATION V2             - clic sur image pour 2 points + saisie distance mm
 * 
 */

import React, {
  useState, useCallback, useMemo, useRef, useEffect,
} from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRight, X,
  Upload, Loader2, AlertCircle, CheckCircle2,
  Target, Save, Printer,
  Sun, Moon, ZoomIn, ZoomOut,
  Activity, RefreshCw,
  Maximize2, Minimize2, Ruler,
} from 'lucide-react';
import { api } from '../../services/api';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import type { Landmark } from './CephaloTracingLayer';

// 
// TYPES
// 
type UIMode   = 'light' | 'dark';

type StepId   = 1 | 2 | 3 | 4;

type SyncState = 'idle' | 'syncing' | 'success' | 'error';

interface DDMState {
  maxillaire:   number | '';
  mandibulaire: number | '';
}

interface DiagnosticTexts {
  squelettique:           string;
  compensations_dentaires: string;
  plan_therapeutique:     string;
}

interface ImageFilters {
  brightness: number;
  contrast:   number;
  invert:     boolean;
}

interface LocalState {
  landmarks: Landmark[];
  version:   number;
}

export interface CephaloWorkspaceProps {
  patientId:   number;
  patientName: string;
}

// 
// TYPES ÉTAPE 3 - PROTOCOLE COM
// 
type CVMStage = 'CS1' | 'CS2' | 'CS3' | 'CS4' | 'CS5' | 'CS6';
type ClasseAngle = 'I' | 'II' | 'III';
type DivisionClasseII = '1' | '2' | null;
type TypeArcade = 'I' | 'II' | null;
type PatternVertical = 'hypodivergent' | 'normodivergent' | 'hyperdivergent';
type ProfilFacial = 'convexe' | 'droit' | 'concave';
type SeveriteDDM = 'léger' | 'modéré' | 'sévère' | 'excès';

interface AnalyseDentaire {
  surplomb: number | '';
  recouvrement: number | '';
  impa: number | '';
  i_francfort: number | '';
  inter_incisif: number | '';
}

interface AnalyseOsseuse {
  angle_tweed: number | '';
  decalage_ab: number | '';
  situation_a: number | '';
  situation_b: number | '';
  profondeur_faciale: number | '';
}

interface ExamenOcclusal {
  molaire_gauche: ClasseAngle;
  molaire_droite: ClasseAngle;
  canine_gauche: ClasseAngle;
  canine_droite: ClasseAngle;
}

interface DonneesEtape3 {
  // Identification
  age: number | '';
  cvm: CVMStage | '';
  date_teles: string;
  
  // Analyses (auto-remplies depuis backend)
  dentaire: AnalyseDentaire;
  osseuse: AnalyseOsseuse;
  
  // DDM (affichage lecture seule depuis étape 2)
  ddm_clinique: number | '';
  ddm_cephalo: number | '';
  
  // Classification Classe II
  division: DivisionClasseII;
  type_arcade: TypeArcade;
  
  // Résumé diagnostic (calculé auto)
  classe_squelettique: string;
  pattern_vertical: PatternVertical | '';
  profil: ProfilFacial | '';
  severite_ddm: SeveriteDDM | '';
  subdivision: boolean;
}

//  Étape 2 - Examen Occlusal (moulages)
interface DonneesEtape2 {
  occlusal: ExamenOcclusal;
}

// 
// DESIGN TOKENS
// 
const PALETTE = {
  dark: {
    bg:           '#0f1419',
    bgPanel:      '#131921',
    bgCard:       '#1a2332',
    bgInput:      '#131921',
    border:       '#2a3f5f',
    borderFocus:  '#4a9eff',
    text:         '#f0f4f8',
    textMuted:    '#8a9aaa',
    textDim:      '#5a6a7a',
    accent:       '#4a9eff',
    accentSuccess:'#10b981',
    accentWarning:'#f59e0b',
    accentError:  '#ef4444',
    shadow:       '0 8px 32px rgba(0,0,0,0.3)',
    shadowLg:     '0 20px 60px rgba(0,0,0,0.4)',
  },
  light: {
    bg:           '#f8fafb',
    bgPanel:      '#ffffff',
    bgCard:       '#f3f7fb',
    bgInput:      '#ffffff',
    border:       '#dde5f0',
    borderFocus:  '#2563eb',
    text:         '#0f172a',
    textMuted:    '#64748b',
    textDim:      '#94a3b8',
    accent:       '#2563eb',
    accentSuccess:'#059669',
    accentWarning:'#d97706',
    accentError:  '#dc2626',
    shadow:       '0 4px 16px rgba(0,0,0,0.06)',
    shadowLg:     '0 12px 40px rgba(0,0,0,0.08)',
  },
} as const;

type Palette = typeof PALETTE[keyof typeof PALETTE];

// 
// LANDMARKS REQUIS
// 
const REQUIRED_LANDMARKS = [
  'Po', 'Or', 'N', 'S', 'A', 'B', 'Go', 'Me',
  'U1_incisal', 'U1_apex', 'L1_incisal', 'L1_apex',
] as const;

// 
// PURE HELPERS
// 
function calcDDMReelle(ddmClinique: number | '', impa: number | null): number | null {
  if (ddmClinique === '' || impa === null) return null;
  const ddmCephalo = (impa - 90) / 2.5;
  return Number(ddmClinique) + ddmCephalo;
}

function calcDDMCephalo(impa: number | null): number | null {
  if (impa === null) return null;
  return (impa - 90) / 2.5;
}

/**
 * Calcule le stade CVM estimé selon Baccetti basé sur l'âge et le sexe
 * Source: Magalhães et al., 2022 (méta-analyse)
 */
function estimateCVM(age: number | '', sexe: 'M' | 'F'): CVMStage | '' {
  if (age === '') return '';
  
  // Données approximatives basées sur la méta-analyse
  // Filles atteignent CS3-CS4 environ 1-1.5 an avant les garçons
  if (sexe === 'F') {
    if (age < 9.5) return 'CS1';
    if (age < 10.5) return 'CS2';
    if (age >= 10.5 && age < 12) return 'CS3';  // Pic ~11.5
    if (age >= 12 && age < 13.5) return 'CS4';  // Fin pic ~12.5
    if (age >= 13.5 && age < 15) return 'CS5';
    return 'CS6';
  } else {
    if (age < 10.5) return 'CS1';
    if (age < 11.5) return 'CS2';
    if (age >= 11.5 && age < 13.5) return 'CS3';  // Pic ~12.8
    if (age >= 13.5 && age < 15) return 'CS4';    // Fin pic ~14.1
    if (age >= 15 && age < 17) return 'CS5';
    return 'CS6';
  }
}

function computeLocalImpa(lms: Landmark[]): number | null {
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
 * Calcule la projection orthogonale d'un point sur une ligne définie par deux points.
 */
function projectPointOnLine(
  px: number, py: number,
  ax: number, ay: number,
  bx: number, by: number
): [number, number] | null {
  const dx = bx - ax;
  const dy = by - ay;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return null;
  const t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
  return [ax + t * dx, ay + t * dy];
}

/**
 * Calcule les projections McNamara (N', A', B') sur le plan de Francfort.
 * Retourne un objet avec les coordonnées des projections.
 */
function computeMcNamaraProjections(lms: Landmark[]): { N_prime?: [number, number]; A_prime?: [number, number]; B_prime?: [number, number] } {
  const g = (id: string) => lms.find(l => l.id === id);
  const po = g('Po');
  const or_ = g('Or');
  const n = g('N');
  const a = g('A');
  const b = g('B');
  
  if (!po || !or_) return {};
  
  const projections: { N_prime?: [number, number]; A_prime?: [number, number]; B_prime?: [number, number] } = {};
  
  if (n) {
    const np = projectPointOnLine(n.x, n.y, po.x, po.y, or_.x, or_.y);
    if (np) projections.N_prime = np;
  }
  if (a) {
    const ap = projectPointOnLine(a.x, a.y, po.x, po.y, or_.x, or_.y);
    if (ap) projections.A_prime = ap;
  }
  if (b) {
    const bp = projectPointOnLine(b.x, b.y, po.x, po.y, or_.x, or_.y);
    if (bp) projections.B_prime = bp;
  }
  
  return projections;
}

function fmtNum(v: number | null, dec = 1): string {
  if (v === null) return '-';
  return (v >= 0 ? '+' : '') + v.toFixed(dec);
}

/**
 * Initialise les apex dentaires aux normes COM par défaut si manquants ou sur demande.
 * - L1_apex : IMPA = 90° (perpendiculaire au plan mandibulaire Go-Me)
 * - U1_apex : I/Francfort = 107° (angle avec le plan de Francfort Po-Or)
 */
function initializeDefaultApexes(landmarks: Landmark[]): Landmark[] {
  const g = (id: string) => landmarks.find(l => l.id === id);
  
  const u1i = g('U1_incisal');
  const l1i = g('L1_incisal');
  const go = g('Go');
  const me = g('Me');
  const po = g('Po');
  const or_ = g('Or');
  
  const newLandmarks = [...landmarks];
  const TOOTH_LENGTH = 85; // pixels, même valeur que le backend
  
  // Positionner L1_apex à IMPA = 90° (perpendiculaire au plan mandibulaire)
  if (l1i && go && me) {
    const mandAngle = Math.atan2(me.y - go.y, me.x - go.x);
    // Pour IMPA = 90°, l'axe est perpendiculaire au plan mandibulaire
    // L'apex est vers le bas (sens mandibulaire)
    const toothAngle = mandAngle - Math.PI / 2;
    
    const l1a: Landmark = {
      id: 'L1_apex',
      x: Math.round((l1i.x + TOOTH_LENGTH * Math.cos(toothAngle)) * 100) / 100,
      y: Math.round((l1i.y + TOOTH_LENGTH * Math.sin(toothAngle)) * 100) / 100,
    };
    
    const existingIdx = newLandmarks.findIndex(l => l.id === 'L1_apex');
    if (existingIdx >= 0) {
      newLandmarks[existingIdx] = l1a;
    } else {
      newLandmarks.push(l1a);
    }
  }
  
  // Positionner U1_apex à I/F = 107° (angle avec le plan de Francfort)
  if (u1i && po && or_) {
    const fhAngle = Math.atan2(or_.y - po.y, or_.x - po.x);
    // Pour I/F = 107°, l'axe fait 107° avec le plan de Francfort
    const toothAngle = fhAngle - (107 * Math.PI / 180);
    
    const u1a: Landmark = {
      id: 'U1_apex',
      x: Math.round((u1i.x + TOOTH_LENGTH * Math.cos(toothAngle)) * 100) / 100,
      y: Math.round((u1i.y + TOOTH_LENGTH * Math.sin(toothAngle)) * 100) / 100,
    };
    
    const existingIdx = newLandmarks.findIndex(l => l.id === 'U1_apex');
    if (existingIdx >= 0) {
      newLandmarks[existingIdx] = u1a;
    } else {
      newLandmarks.push(u1a);
    }
  }
  
  return newLandmarks;
}

function buildPayload(
  landmarks: Landmark[],
  _ddm: DDMState,
  ddmMax: number | null,
  ddmMand: number | null,
  ddmReelle: number | null,
  diag: DiagnosticTexts,
  mcnamaraProjections?: { N_prime?: [number, number]; A_prime?: [number, number]; B_prime?: [number, number] }
) {
  const payload: any = {
    landmarks: landmarks.map(l => ({ id: l.id, x: l.x, y: l.y })),
    clinical_data: {
      ddm_maxillaire: {
        espace_disponible: 0,
        espace_necessaire: 0,
        calcul_ddm: ddmMax ?? 0,
      },
      ddm_mandibulaire: {
        espace_disponible: 0,
        espace_necessaire: 0,
        calcul_ddm: ddmMand ?? 0,
      },
      ddm_reelle: ddmReelle ?? 0,
      plan_traitement: diag.plan_therapeutique || '',
    },
    ai_diagnostic: {
      squelettique: diag.squelettique || '',
      dentaire: diag.compensations_dentaires || '',
      traitement: diag.plan_therapeutique || '',
    },
  };
  
  // Ajout des projections McNamara si disponibles
  if (mcnamaraProjections && (mcnamaraProjections.A_prime || mcnamaraProjections.B_prime)) {
    payload.mcnmara_projections = mcnamaraProjections;
  }
  
  return payload;
}



const StepTab: React.FC<{
  id: StepId; label: string; isActive: boolean; isCompleted: boolean;
  hasError?: boolean; onClick: () => void; P: Palette;
}> = ({ id, label, isActive, isCompleted, hasError, onClick, P }) => (
  <motion.button
    whileHover={{ y: -1 }} whileTap={{ scale: 0.98 }}
    onClick={onClick}
    className="relative px-4 py-3 rounded-lg transition-all"
    style={{
      background: isActive ? `${P.accent}15` : 'transparent',
      border: `1px solid ${isActive ? P.accent : P.border}`,
      color: isActive ? P.accent : P.textMuted,
    }}
  >
    <div className="flex items-center gap-2 text-xs font-mono font-semibold tracking-wide">
      {isCompleted && !isActive && !hasError && <CheckCircle2 size={12} style={{ color: P.accentSuccess }} />}
      {hasError && !isActive && <AlertCircle size={12} style={{ color: P.accentError }} />}
      <span className="opacity-40">{id}.</span>
      <span>{label}</span>
    </div>
    {isActive && (
      <motion.div
        layoutId="step-active"
        className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
        style={{ background: `linear-gradient(90deg, ${P.accent}, ${P.accentSuccess})` }}
      />
    )}
  </motion.button>
);

const SyncBadge: React.FC<{ state: SyncState; P: Palette }> = ({ state, P }) => {
  if (state === 'idle') return null;
  const cfg = {
    syncing: { color: P.accent, icon: <Loader2 size={12} className="animate-spin" />, label: 'Synchronisation…' },
    success: { color: P.accentSuccess, icon: <CheckCircle2 size={12} />, label: 'Synchronisé' },
    error: { color: P.accentError, icon: <AlertCircle size={12} />, label: 'Erreur sync' },
  }[state];
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
      className="absolute bottom-4 right-4 z-30 px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-2 pointer-events-none"
      style={{ background: `${cfg.color}15`, border: `1px solid ${cfg.color}40`, color: cfg.color }}
    >
      {cfg.icon}{cfg.label}
    </motion.div>
  );
};

// 
// MODAL BLOCAGE ÉTAPE 2
// 
const Step2BlockerModal: React.FC<{
  type: 'calibration' | 'apex' | null;
  onClose: () => void;
  onStartCalibration: () => void;
  P: Palette;
}> = ({ type, onClose, onStartCalibration, P }) => {
  if (!type) return null;
  const isCalibration = type === 'calibration';
  
  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className="max-w-md w-full rounded-2xl p-6"
        style={{ 
          background: P.bgPanel,
          border: `1px solid ${P.border}`,
          boxShadow: P.shadowLg
        }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ background: isCalibration ? `${P.accentWarning}15` : `${P.accent}15` }}
          >
            {isCalibration ? (
              <Ruler size={24} style={{ color: P.accentWarning }} />
            ) : (
              <Activity size={24} style={{ color: P.accent }} />
            )}
          </div>
          <div>
            <h3 className="text-lg font-bold" style={{ color: P.text }}>
              {isCalibration ? 'Calibration requise' : 'Repositionnement nécessaire'}
            </h3>
            <p className="text-xs" style={{ color: P.textMuted }}>
              Étape préliminaire obligatoire
            </p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <p className="text-sm leading-relaxed" style={{ color: P.textMuted }}>
            {isCalibration 
              ? "Avant de procéder à l'analyse des moulages, vous devez calibrer l'échelle de la radiographie en sélectionnant deux points de référence dont vous connaissez la distance réelle."
              : "Les apex des incisives ont été placés automatiquement par l'IA. Pour une analyse précise, vous devez les repositionner manuellement à la racine des dents."}
          </p>
          
          <div 
            className="rounded-xl p-4 text-xs space-y-3"
            style={{ background: P.bgCard, border: `1px solid ${P.border}` }}
          >
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: P.accent, color: 'white' }}>1</span>
              <span style={{ color: P.textMuted }}>
                {isCalibration 
                  ? 'Cliquez sur "Calibrer maintenant" puis sélectionnez deux points distincts sur l\'image (ex: bords d\'une dent connue)'
                  : 'Sélectionnez et déplacez U1_apex (apex incisive supérieure) à la racine de la dent'}
              </span>
            </div>
            <div className="flex items-start gap-3">
              <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: P.accent, color: 'white' }}>2</span>
              <span style={{ color: P.textMuted }}>
                {isCalibration 
                  ? 'Entrez la distance réelle entre ces deux points en millimètres'
                  : 'Sélectionnez et déplacez L1_apex (apex incisive inférieure) à la racine de la dent'}
              </span>
            </div>
            {!isCalibration && (
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: P.accent, color: 'white' }}>3</span>
                <span style={{ color: P.textMuted }}>
                  Validez la position des apex pour débloquer l'accès aux moulages
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all hover:opacity-80"
            style={{ 
              background: 'transparent',
              border: `1px solid ${P.border}`,
              color: P.textMuted
            }}
          >
            Plus tard
          </button>
          {isCalibration ? (
            <button
              onClick={() => {
                onClose();
                onStartCalibration();
              }}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold transition-all hover:opacity-90"
              style={{ 
                background: P.accentWarning,
                color: 'white'
              }}
            >
              Calibrer maintenant
            </button>
          ) : (
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold transition-all hover:opacity-90"
              style={{ 
                background: P.accent,
                color: 'white'
              }}
            >
              J'ai compris
            </button>
          )}
        </div>
      </motion.div>
    </div>,
    document.body
  );
};

// 
// COMPOSANT PRINCIPAL
// 
export const CephaloWorkspace: React.FC<CephaloWorkspaceProps> = ({
  patientId,
  patientName,
}) => {
  //  Thème 
  const [mode, setMode] = useState<UIMode>('light');
  const P = PALETTE[mode];

  //  Navigation 
  const [step, setStep] = useState<StepId>(1);
  const [completed, setCompleted] = useState<Set<number>>(new Set());

  //  Mode Plein Écran 
  const [isStep1Fullscreen, setIsStep1Fullscreen] = useState(false);

  //  State Analyse 
  const [analysisId, setAnalysisId] = useState<number | undefined>();
  const [imageSrc, setImageSrc] = useState<string | undefined>();
  const [anglesData, setAnglesData] = useState<Record<string, any>>({});
  const [visionMetadata, setVisionMetadata] = useState<{
    mode_inference?: string;
    warning?: string;
    processing_time_ms?: number;
  }>({});

  //  Calibration State V2
  const [isCalibrated, setIsCalibrated] = useState(false);
  const [mmPerPixel, setMmPerPixel] = useState<number | null>(null);
  const [showCalibration, setShowCalibration] = useState(false);
  // NOUVEAU: Points cliqués directement sur l'image (pas des landmarks)
  const [calibrationClickPoints, setCalibrationClickPoints] = useState<{x: number, y: number}[]>([]);
  const [calibrationDistance, setCalibrationDistance] = useState<string>('');
  const [calibrationStep, setCalibrationStep] = useState<'selecting' | 'entering'>('selecting');

  //  State Local
  const [local, setLocal] = useState<LocalState>({ landmarks: [], version: 0 });
  const [activePointId, setActivePointId] = useState<string | null>(null);
  const [imgFilters, setImgFilters] = useState<ImageFilters>({ brightness: 100, contrast: 110, invert: false });
  const [imgDim, setImgDim] = useState({ w: 800, h: 1000 });
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>('idle');
  const [isSaving, setIsSaving] = useState(false);
  const [isPrinting, setIsPrinting] = useState(false);
  const [, setIsGeneratingSLM] = useState(false);
  const [magnifierEnabled, setMagnifierEnabled] = useState(false);

  //  DDM & Textes Diagnostics 
  const [ddm, setDdm] = useState<DDMState>({ maxillaire: '', mandibulaire: '' });
  const [diag, setDiag] = useState<DiagnosticTexts>({
    squelettique: '',
    compensations_dentaires: '',
    plan_therapeutique: '',
  });

  //  ÉTAPE 4 - Photos et Documents
  interface PhotoUpload {
    id: string;
    type: 'radio' | 'moulage_max' | 'moulage_mand' | 'intra_face' | 'intra_profile' | 'extra_face' | 'extra_profile' | 'extra_sourire';
    file: File | null;
    preview: string | null;
    label: string;
  }
  
  //  ÉTAPE 4 - Données Photos (chargement localStorage)
  const [photos, setPhotos] = useState<PhotoUpload[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_photos_${patientId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          // Reconstruction des photos avec previews
          return [
            { id: 'radio', type: 'radio', file: null, preview: parsed.radio || null, label: 'Radiographie Céphalométrique' },
            { id: 'moulage_max', type: 'moulage_max', file: null, preview: parsed.moulage_max || null, label: 'Moulage Maxillaire' },
            { id: 'moulage_mand', type: 'moulage_mand', file: null, preview: parsed.moulage_mand || null, label: 'Moulage Mandibulaire' },
            { id: 'extra_face', type: 'extra_face', file: null, preview: parsed.extra_face || null, label: 'Photo Extra-orale Face' },
            { id: 'extra_profile', type: 'extra_profile', file: null, preview: parsed.extra_profile || null, label: 'Photo Extra-orale Profil' },
            { id: 'extra_sourire', type: 'extra_sourire', file: null, preview: parsed.extra_sourire || null, label: 'Photo Extra-orale Sourire' },
            { id: 'intra_face', type: 'intra_face', file: null, preview: parsed.intra_face || null, label: 'Photo Intra-orale Face' },
            { id: 'intra_profile', type: 'intra_profile', file: null, preview: parsed.intra_profile || null, label: 'Photo Intra-orale Profil' },
          ];
        } catch (e) {
          console.error('Erreur chargement photos:', e);
        }
      }
    }
    return [
      { id: 'radio', type: 'radio', file: null, preview: null, label: 'Radiographie Céphalométrique' },
      { id: 'moulage_max', type: 'moulage_max', file: null, preview: null, label: 'Moulage Maxillaire' },
      { id: 'moulage_mand', type: 'moulage_mand', file: null, preview: null, label: 'Moulage Mandibulaire' },
      { id: 'extra_face', type: 'extra_face', file: null, preview: null, label: 'Photo Extra-orale Face' },
      { id: 'extra_profile', type: 'extra_profile', file: null, preview: null, label: 'Photo Extra-orale Profil' },
      { id: 'extra_sourire', type: 'extra_sourire', file: null, preview: null, label: 'Photo Extra-orale Sourire' },
      { id: 'intra_face', type: 'intra_face', file: null, preview: null, label: 'Photo Intra-orale Face' },
      { id: 'intra_profile', type: 'intra_profile', file: null, preview: null, label: 'Photo Intra-orale Profil' },
    ];
  });
  
  const [dateConsultation, setDateConsultation] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape4_${patientId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          return parsed.dateConsultation || new Date().toISOString().split('T')[0];
        } catch (e) {}
      }
    }
    return new Date().toISOString().split('T')[0];
  });
  
  const [sexePatient, setSexePatient] = useState<'M' | 'F'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape4_${patientId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          return parsed.sexePatient || 'M';
        } catch (e) {}
      }
    }
    return 'M';
  });

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 4 (photos et métadonnées)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const photosToSave = photos.reduce((acc, p) => {
        acc[p.id] = p.preview;
        return acc;
      }, {} as Record<string, string | null>);
      localStorage.setItem(`digitalcrown_photos_${patientId}`, JSON.stringify(photosToSave));
      localStorage.setItem(`digitalcrown_etape4_${patientId}`, JSON.stringify({ dateConsultation, sexePatient }));
    }
  }, [photos, dateConsultation, sexePatient, patientId]);
  
  //  FONCTION UPLOAD PHOTO
  const handlePhotoUpload = (id: string, file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setPhotos(prev => prev.map(p => p.id === id ? { ...p, file, preview: e.target?.result as string } : p));
    };
    reader.readAsDataURL(file);
  };
  
  //  ÉTAPE 3 - Données Protocole COM
  const [etape3Data, setEtape3Data] = useState<DonneesEtape3>(() => {
    // Chargement depuis localStorage au montage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape3_${patientId}`);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {
          console.error('Erreur chargement étape 3:', e);
        }
      }
    }
    return {
      age: '',
      cvm: '',
      date_teles: new Date().toISOString().split('T')[0],
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
      },
      ddm_clinique: '',
      ddm_cephalo: '',
      division: null,
      type_arcade: null,
      classe_squelettique: '',
      pattern_vertical: '',
      profil: '',
      severite_ddm: '',
      subdivision: false,
    };
  });

  //  ÉTAPE 2 - Examen Occlusal (déplacé depuis étape 3)
  const [etape2Data, setEtape2Data] = useState<DonneesEtape2>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape2_${patientId}`);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {}
      }
    }
    return {
      occlusal: {
        molaire_gauche: 'I',
        molaire_droite: 'I',
        canine_gauche: 'I',
        canine_droite: 'I',
      },
    };
  });

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 2
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(`digitalcrown_etape2_${patientId}`, JSON.stringify(etape2Data));
    }
  }, [etape2Data, patientId]);

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 3
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(`digitalcrown_etape3_${patientId}`, JSON.stringify(etape3Data));
    }
  }, [etape3Data, patientId]);

  //  AUTOMATISATION CVM (Âge + Sexe)
  useEffect(() => {
    const cvmEstime = estimateCVM(etape3Data.age, sexePatient);
    if (cvmEstime && cvmEstime !== etape3Data.cvm) {
      setEtape3Data(prev => ({ ...prev, cvm: cvmEstime }));
    }
  }, [etape3Data.age, sexePatient]);

  //  PRÉ-REMPLISSAGE AUTO DES ANALYSES (depuis anglesData backend)
  const autoFillAnalyses = useCallback(() => {
    if (!anglesData?.metrics) return;
    
    const dentaire = anglesData.metrics.analyse_dentaire || {};
    const osseuse = anglesData.metrics.analyse_osseuse || {};
    
    setEtape3Data(prev => ({
      ...prev,
      dentaire: {
        surplomb: dentaire.Surplomb?.value ?? prev.dentaire.surplomb,
        recouvrement: dentaire.Recouvrement?.value ?? prev.dentaire.recouvrement,
        impa: dentaire.IMPA?.value ?? prev.dentaire.impa,
        i_francfort: dentaire.I_Francfort?.value ?? prev.dentaire.i_francfort,
        inter_incisif: dentaire.Inter_Incisif?.value ?? prev.dentaire.inter_incisif,
      },
      osseuse: {
        angle_tweed: osseuse.Angle_de_Tweed?.value ?? prev.osseuse.angle_tweed,
        decalage_ab: osseuse.Decalage_A_B?.value ?? prev.osseuse.decalage_ab,
        situation_a: osseuse.Situation_A?.value ?? prev.osseuse.situation_a,
        situation_b: osseuse.Situation_B?.value ?? prev.osseuse.situation_b,
        profondeur_faciale: osseuse.Profondeur_Faciale?.value ?? prev.osseuse.profondeur_faciale,
      },
    }));
  }, [anglesData]);

  //  SYNCHRONISATION DDM Étape 2 → Étape 3
  // Méthode de Nance: DDM = Espace Disponible - Espace Nécessaire
  // Valeurs saisies positives = déficit → converties en négatives
  useEffect(() => {
    // DDM Clinique = somme des déficits Maxillaire + Mandibulaire (négatif = déficit)
    const ddmMax = ddm.maxillaire === '' ? 0 : -Number(ddm.maxillaire);  // Inversé: saisie positive → négatif
    const ddmMand = ddm.mandibulaire === '' ? 0 : -Number(ddm.mandibulaire);  // Inversé
    const ddmClinique = ddmMax + ddmMand;
    
    // DDM Céphalo = compensation dentaire (formule COM)
    // Compensation mandibulaire = (IMPA - 90) / 2.5 → positive si IMPA > 90 (proclinaison)
    // Cette compensation réduit le déficit apparent → on l'ajoute (moins négatif)
    const impa = etape3Data.dentaire.impa === '' ? 90 : Number(etape3Data.dentaire.impa);
    const iFrancfort = etape3Data.dentaire.i_francfort === '' ? 107 : Number(etape3Data.dentaire.i_francfort);
    const compensationMand = (impa - 90) / 2.5;  // Compensation mandibulaire
    const compensationMax = (iFrancfort - 107) / 2.5;  // Compensation maxillaire
    const ddmCephalo = compensationMand + compensationMax;
    
    setEtape3Data(prev => ({
      ...prev,
      ddm_clinique: parseFloat(ddmClinique.toFixed(1)),
      ddm_cephalo: parseFloat(ddmCephalo.toFixed(1)),
    }));
  }, [ddm.maxillaire, ddm.mandibulaire, etape3Data.dentaire.impa, etape3Data.dentaire.i_francfort]);

  //  Modal blocage étape 2
  const [showStep2Blocker, setShowStep2Blocker] = useState<'calibration' | 'apex' | null>(null);

  //  Refs 
  const fileRef = useRef<HTMLInputElement>(null);
  const syncTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const latestLocal = useRef(local);
  const latestDdm = useRef(ddm);
  const latestDiag = useRef(diag);
  const step1ContainerRef = useRef<HTMLDivElement>(null);

  // Synchroniser les refs
  latestLocal.current = local;
  latestDdm.current = ddm;
  latestDiag.current = diag;

  //  Vérifications pour passage étape 2
  const hasApexAdjusted = useMemo(() => {
    const u1a = local.landmarks.find(l => l.id === 'U1_apex');
    const l1a = local.landmarks.find(l => l.id === 'L1_apex');
    const u1i = local.landmarks.find(l => l.id === 'U1_incisal');
    const l1i = local.landmarks.find(l => l.id === 'L1_incisal');
    
    if (!u1a || !l1a || !u1i || !l1i) return false;
    
    const u1ExpectedY = u1i.y - 80;
    const l1ExpectedY = l1i.y + 80;
    
    const u1Adjusted = Math.abs(u1a.y - u1ExpectedY) > 2;
    const l1Adjusted = Math.abs(l1a.y - l1ExpectedY) > 2;
    
    return u1Adjusted || l1Adjusted;
  }, [local.landmarks]);

  //  CALCULS ÉTAPE 3 - Protocole COM
  
  // Calcul DDM Réelle
  const ddmReelleCalc = useMemo(() => {
    const clinique = etape3Data.ddm_clinique === '' ? 0 : Number(etape3Data.ddm_clinique);
    const cephalo = etape3Data.ddm_cephalo === '' ? 0 : Number(etape3Data.ddm_cephalo);
    return clinique + cephalo;
  }, [etape3Data.ddm_clinique, etape3Data.ddm_cephalo]);
  
  // Interprétation sévérité DDM (Méthode de Nance)
  // DDM = Espace Disponible - Espace Nécessaire
  // DDM négative = déficit (encombrement) | DDM positive = excès (espacements)
  // Convention clinique: valeurs saisies positives = déficit (encombrement)
  const severiteDDM = useMemo((): SeveriteDDM | 'excès' | '' => {
    const val = ddmReelleCalc; 
    if (val === 0) return '';
    if (val > 0) return 'excès'; // Excès d'espace (diastèmes)
    // valeurs négatives = déficit d'espace (encombrement)
    if (val >= -3) return 'léger';      // -3mm à 0 = léger
    if (val >= -6) return 'modéré';     // -6mm à -3mm = modéré  
    return 'sévère';                    // < -6mm = sévère
  }, [ddmReelleCalc]);
  
  // Détection subdivision (depuis étape 2)
  const hasSubdivision = useMemo(() => {
    const { molaire_gauche, molaire_droite, canine_gauche, canine_droite } = etape2Data.occlusal;
    return molaire_gauche !== molaire_droite || canine_gauche !== canine_droite;
  }, [etape2Data.occlusal]);
  
  // Détermination Classe Squelettique
  const classeSquelettique = useMemo(() => {
    const anb = etape3Data.osseuse.decalage_ab === '' ? null : Number(etape3Data.osseuse.decalage_ab);
    if (anb === null) return '';
    if (anb < 0) return 'Classe III';
    if (anb >= 0 && anb <= 4) return 'Classe I';
    if (anb > 4 && anb <= 8) return 'Classe II modérée';
    if (anb > 8) return 'Classe II sévère';
    return '';
  }, [etape3Data.osseuse.decalage_ab]);
  
  // Pattern Vertical
  const patternVertical = useMemo((): PatternVertical | '' => {
    const fma = etape3Data.osseuse.angle_tweed === '' ? null : Number(etape3Data.osseuse.angle_tweed);
    if (fma === null) return '';
    if (fma < 20) return 'hypodivergent';
    if (fma >= 20 && fma <= 30) return 'normodivergent';
    if (fma > 30) return 'hyperdivergent';
    return '';
  }, [etape3Data.osseuse.angle_tweed]);
  
  // Profil Facial
  const profilFacial = useMemo((): ProfilFacial | '' => {
    const pf = etape3Data.osseuse.profondeur_faciale === '' ? null : Number(etape3Data.osseuse.profondeur_faciale);
    if (pf === null) return '';
    if (pf < 82) return 'convexe';
    if (pf >= 82 && pf <= 92) return 'droit';
    if (pf > 92) return 'concave';
    return '';
  }, [etape3Data.osseuse.profondeur_faciale]);
  
  // Génération Plan de Traitement
  const planTraitement = useMemo(() => {
    const cvm = etape3Data.cvm;
    const classe = classeSquelettique;
    const pattern = patternVertical;
    const ddmSev = severiteDDM;
    const anb = etape3Data.osseuse.decalage_ab === '' ? 0 : Number(etape3Data.osseuse.decalage_ab);
    const impa = etape3Data.dentaire.impa === '' ? 90 : Number(etape3Data.dentaire.impa);
    const ifranc = etape3Data.dentaire.i_francfort === '' ? 107 : Number(etape3Data.dentaire.i_francfort);
    
    let plan = '';
    
    // Vérification extraction obligatoire
    if (ddmSev === 'sévère' || impa > 100 || ifranc > 120) {
      plan += '• INDICATION EXTRACTION : ';
      if (ddmSev === 'sévère') plan += 'DDM sévère (<-6mm). ';
      if (impa > 100) plan += 'IMPA > 100° (risque parodontal). ';
      if (ifranc > 120) plan += 'I/F > 120° (biproalvéolie). ';
      plan += '\n\n';
    }
    
    // Contre-indication extraction mandibulaire
    if (pattern === 'hyperdivergent') {
      plan += '⚠ CONTRE-INDICATION : Extraction mandibulaire interdite (Tweed >30° risque béance).\n\n';
    }
    
    // Arbre décisionnel principal
    if (cvm === 'CS1' || cvm === 'CS2' || cvm === 'CS3' || cvm === 'CS4') {
      // Patient en croissance
      plan += '**PATIENT EN CROISSANCE** (CVM ' + cvm + ')\n\n';
      
      if (classe.includes('Classe I')) {
        if (ddmSev === 'léger' || ddmSev === '') {
          plan += '• Protocole : Sans extraction\n';
          plan += '• Expansion transversale (ERM) si arcade en V\n';
          plan += '• Appareil fixe multi-attache\n';
        } else if (ddmSev === 'modéré') {
          plan += '• Protocole : Borderline - évaluer profil\n';
          plan += '• Si profil convexe → Extraction PM4 sup.\n';
          plan += '• Si profil droit → Essai sans extraction\n';
        }
      } else if (classe.includes('Classe II')) {
        if (etape3Data.division === '1') {
          plan += '• Division 1 : Appareil fonctionnel de choix (Herbst ou Twin Block)\n';
          plan += '• Timing optimal : CS3-CS4 (pic de croissance)\n';
          if (etape3Data.type_arcade === 'I') {
            plan += '• Arcade en V : ERM simultanée pour expansion\n';
          }
          plan += '• Préserver arcades (pas d\'extraction avant fin du pic)\n';
          if (impa > 100) plan += '• Surveiller IMPA, ne pas corriger incisives avant fonctionnel\n';
        } else if (etape3Data.division === '2') {
          plan += '• Division 2 :\n';
          plan += '  - Phase 1 : Dérétroclinaison incisives sup. (arcs acier)\n';
          plan += '  - Phase 2 : Appareil fonctionnel ou fixe selon DDM\n';
          if (pattern === 'hypodivergent') {
            plan += '• FMA bas : Surveiller DV (ne pas ouvrir)\n';
          }
        }
      } else if (classe.includes('Classe III')) {
        if (cvm === 'CS1' || cvm === 'CS2' || cvm === 'CS3') {
          plan += '• Masque facial (Delaire) + ERM\n';
          plan += '• Protocole : 350-500g/côté, 14-16h/jour\n';
          plan += '• Efficacité maximale avant CS4\n';
        } else {
          plan += '• CS4+ : Efficacité diminuée, camouflage si ANB >-4°\n';
        }
      }
    } else {
      // Adulte
      plan += '**PATIENT ADULTE** (CVM ' + cvm + ')\n\n';
      
      if (classe.includes('Classe II')) {
        if (anb > 9) {
          plan += '• ANB > 9° : CHIRURGIE ORTHOGNATHIQUE INDiquée\n';
          plan += '• Advancement mandibulaire (BSSO) ± LeFort I\n';
          plan += '• Ortho pré-chirurgicale : décompensation (pas de camouflage)\n';
        } else if (anb >= 4 && anb <= 7) {
          plan += '• Camouflage orthodontique possible\n';
          if (ddmSev === 'sévère') {
            plan += '• Extraction PM4 supérieures + rétraction\n';
          } else {
            plan += '• Distalisation assistée par TADs (sans extraction si profil acceptable)\n';
          }
        }
      } else if (classe.includes('Classe III')) {
        if (anb < -4) {
          plan += '• ANB <-4° : Chirurgie bi-maxillaire\n';
        } else {
          plan += '• Camouflage : Extractions inférieures + proclinaison sup.\n';
        }
      } else if (classe.includes('Classe I') && ddmSev === 'sévère') {
        plan += '• Classe I avec DDM sévère : Extraction 4 prémolaires\n';
        plan += '• Mécanique de fermeture avec TADs ancrage\n';
      }
    }
    
    // Mention subdivision si présente
    if (hasSubdivision) {
      plan += '\n• Attention : Classe II/III Subdivision unilatérale détectée\n';
      plan += '• Vérifier asymétrie squelettique (analyse transversale)\n';
    }
    
    return plan;
  }, [etape3Data, classeSquelettique, patternVertical, severiteDDM, hasSubdivision]);

  //  Effects
  useEffect(() => {
    if (!isStep1Fullscreen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsStep1Fullscreen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isStep1Fullscreen]);

  useEffect(() => {
    if (isStep1Fullscreen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = originalOverflow; };
    }
  }, [isStep1Fullscreen]);

  useEffect(() => {
    if (!imageSrc) return;
    const img = new Image();
    img.onload = () => setImgDim({ w: img.naturalWidth, h: img.naturalHeight });
    img.src = imageSrc;
  }, [imageSrc]);

  useEffect(() => {
    return () => { if (syncTimer.current) clearTimeout(syncTimer.current); };
  }, []);

  useEffect(() => {
    if (step !== 1 && isStep1Fullscreen) setIsStep1Fullscreen(false);
  }, [step, isStep1Fullscreen]);

  // 
  // COMPUTED
  // 
  const tracingPct = useMemo(() => {
    const n = REQUIRED_LANDMARKS.filter(id => local.landmarks.some(l => l.id === id)).length;
    return n / REQUIRED_LANDMARKS.length;
  }, [local.landmarks]);

  const allLandmarksPlaced = tracingPct === 1;



  const localImpa = useMemo(() => computeLocalImpa(local.landmarks), [local.landmarks]);

  const serverImpa = useMemo(() => {
    const v1 = anglesData?.metrics?.analyse_dentaire?.IMPA?.value;
    if (v1 !== undefined && v1 !== null) return v1 as number;
    const v2 = anglesData?.IMPA?.valeur;
    if (v2 !== undefined && v2 !== null) return v2 as number;
    return null;
  }, [anglesData]);

  const impaActuel = serverImpa ?? localImpa;

  const ddmMaxClinique = ddm.maxillaire === '' ? null : Number(ddm.maxillaire);
  const ddmMandClinique = ddm.mandibulaire === '' ? null : Number(ddm.mandibulaire);

  const ddmMaxReelle = useMemo(() => calcDDMReelle(ddm.maxillaire, impaActuel), [ddm.maxillaire, impaActuel]);
  const ddmMandReelle = useMemo(() => calcDDMReelle(ddm.mandibulaire, impaActuel), [ddm.mandibulaire, impaActuel]);
  const ddmReelleTotale = useMemo(() => {
    if (ddmMaxReelle === null || ddmMandReelle === null) return null;
    return ddmMaxReelle + ddmMandReelle;
  }, [ddmMaxReelle, ddmMandReelle]);

  // 
  // SAUVEGARDE SILENCIEUSE
  // 
  const silentSave = useCallback(async (id?: number) => {
    const aid = id ?? analysisId;
    if (!aid) return;
    const l = latestLocal.current;
    const d = latestDdm.current;
    const g = latestDiag.current;
    const max = d.maxillaire === '' ? null : Number(d.maxillaire);
    const mand = d.mandibulaire === '' ? null : Number(d.mandibulaire);
    const ceph = calcDDMCephalo(serverImpa ?? computeLocalImpa(l.landmarks));
    const real = (mand !== null && ceph !== null) ? mand + ceph : null;
    try {
      const projections = computeMcNamaraProjections(l.landmarks);
      await api.put(`/analyses/${aid}`, buildPayload(l.landmarks, d, max, mand, real, g, projections));
    } catch {}
  }, [analysisId, serverImpa]);

  // 
  // OPTIMISTIC UPDATE
  // 
  const updateLandmarksOptimistic = useCallback((newLms: Landmark[]) => {
    setLocal(prev => ({ landmarks: newLms, version: prev.version + 1 }));
    if (!analysisId) return;
    if (syncTimer.current) clearTimeout(syncTimer.current);
    setSyncState('syncing');
    syncTimer.current = setTimeout(async () => {
      const d = latestDdm.current;
      const g = latestDiag.current;
      const impa = serverImpa ?? computeLocalImpa(newLms);
      const max = calcDDMReelle(d.maxillaire, impa);
      const mand = calcDDMReelle(d.mandibulaire, impa);
      const real = (max !== null && mand !== null) ? (max + mand) : null;
      try {
        const projections = computeMcNamaraProjections(newLms);
        await api.put(`/analyses/${analysisId}`, buildPayload(newLms, d, max, mand, real, g, projections));
        setSyncState('success');
        setTimeout(() => setSyncState('idle'), 1500);
      } catch {
        setSyncState('error');
        setTimeout(() => setSyncState('idle'), 2500);
      }
    }, 600);
  }, [analysisId, serverImpa]);

  // 
  // NAVIGATION STEPPER
  // 
  const [stepError, setStepError] = useState<string | null>(null);

  const goToStep = useCallback(async (target: StepId) => {
    if (target >= 2) {
      if (!imageSrc) {
        setStepError('Veuillez d\'abord uploader une radiographie avant d\'accéder aux moulages.');
        setTimeout(() => setStepError(null), 4000);
        return;
      }
      if (!isCalibrated) {
        setShowStep2Blocker('calibration');
        return;
      }
      if (!hasApexAdjusted) {
        setShowStep2Blocker('apex');
        return;
      }
    }
    await silentSave();
    setCompleted(prev => new Set([...prev, step]));
    setStep(target);
  }, [silentSave, step, imageSrc, local.landmarks, isCalibrated, hasApexAdjusted]);

  // 
  // UPLOAD & ANALYSE IA
  // 
  const runAnalysis = useCallback(async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await api.post(`/patients/${patientId}/upload-radio`, form);
      const data = res.data;
      if (data.analysis_id) setAnalysisId(data.analysis_id);
      if (data.file_url) setImageSrc(data.file_url);
      if (data.results) setAnglesData(data.results);
      if (data.results?.vision_metadata) setVisionMetadata(data.results.vision_metadata);
      if (data.is_calibrated !== undefined) {
        setIsCalibrated(data.is_calibrated);
        setMmPerPixel(data.mm_per_pixel || null);
      }
      if (data.landmarks) {
        // Initialisation des apex aux normes COM si nécessaire
        const landmarksWithApex = initializeDefaultApexes(data.landmarks);
        
        setLocal(prev => {
          const isSame =
            Array.isArray(prev.landmarks) &&
            prev.landmarks.length === landmarksWithApex.length &&
            prev.landmarks.every((l: Landmark, i: number) => {
              const d2 = landmarksWithApex[i];
              return l.id === d2.id && Math.abs(l.x - d2.x) < 0.01 && Math.abs(l.y - d2.y) < 0.01;
            });
          return isSame ? prev : { landmarks: landmarksWithApex, version: prev.version + 1 };
        });
      }
      // DEBUG: Log visual_debug data
      console.log('[DEBUG] visual_debug:', data.results?.visual_debug);
      console.log('[DEBUG] A_prime:', data.results?.visual_debug?.A_prime);
      console.log('[DEBUG] B_prime:', data.results?.visual_debug?.B_prime);
      console.log('[DEBUG] landmarks:', data.landmarks?.map((l: any) => l.id));
      
      if (data.results?.ai_narrative) {
        const n = data.results.ai_narrative;
        setDiag(prev => ({
          squelettique: prev.squelettique || n.diagnostic_squelettique || '',
          compensations_dentaires: prev.compensations_dentaires || n.analyse_dentaire || '',
          plan_therapeutique: prev.plan_therapeutique || n.strategie_therapeutique || '',
        }));
      }
      setCompleted(prev => new Set([...prev, 1]));
    } catch (e: any) {
      const raw = e?.response?.data?.detail;
      setUploadError(typeof raw === 'string' ? raw : 'Échec de l\'analyse. Vérifiez l\'image.');
    } finally {
      setIsUploading(false);
    }
  }, [patientId]);

  const handleFileDrop = useCallback((files: FileList | null) => {
    if (!files?.length) return;
    if (!files[0].type.startsWith('image/')) {
      setUploadError('Format non supporté. Utilisez JPEG ou PNG.');
      return;
    }
    runAnalysis(files[0]);
  }, [runAnalysis]);

  // 
  // CALIBRATION V2 - Clic sur image
  // 
  const handleCalibrationClick = useCallback((x: number, y: number) => {
    if (!showCalibration) return;
    if (calibrationClickPoints.length < 2) {
      setCalibrationClickPoints(prev => [...prev, { x, y }]);
    }
  }, [showCalibration, calibrationClickPoints.length]);

  const applyCalibration = useCallback(async () => {
    if (!analysisId || calibrationClickPoints.length !== 2 || !calibrationDistance) return;
    const p1 = calibrationClickPoints[0];
    const p2 = calibrationClickPoints[1];
    const distPixels = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
    const distMm = parseFloat(calibrationDistance);
    if (distMm <= 0 || distPixels <= 0) return;
    const ratio = distMm / distPixels;
    try {
      await api.post(`/analyses/${analysisId}/calibrate`, {
        p1, p2, distance_mm: distMm
      });
      setMmPerPixel(ratio);
      setIsCalibrated(true);
      setShowCalibration(false);
      setCalibrationClickPoints([]);
      setCalibrationDistance('');
      setCalibrationStep('selecting');
      const updatedRes = await api.put(`/analyses/${analysisId}`, {
        landmarks: local.landmarks,
        mm_per_pixel: ratio
      });
      if (updatedRes.data.results) setAnglesData(updatedRes.data.results);
    } catch (e) {
      console.error('Erreur calibration:', e);
    }
  }, [analysisId, calibrationClickPoints, calibrationDistance, local.landmarks]);

  const cancelCalibration = useCallback(() => {
    setShowCalibration(false);
    setCalibrationClickPoints([]);
    setCalibrationDistance('');
    setCalibrationStep('selecting');
  }, []);

  // 
  // SAUVEGARDE MANUELLE
  // 
  const handleSave = useCallback(async () => {
    if (!analysisId) return;
    setIsSaving(true);
    try {
      const projections = computeMcNamaraProjections(local.landmarks);
      await api.put(`/analyses/${analysisId}`, buildPayload(local.landmarks, ddm, ddmMaxClinique, ddmMandClinique, ddmReelleTotale, diag, projections));
      setSyncState('success');
      setTimeout(() => setSyncState('idle'), 1500);
    } catch {
      setSyncState('error');
      setTimeout(() => setSyncState('idle'), 2000);
    } finally {
      setIsSaving(false);
    }
  }, [analysisId, local.landmarks, ddm, ddmMaxClinique, ddmMandClinique, ddmReelleTotale, diag]);

  // 
  // GÉNÉRATION SLM
  // 
  const handleGenerateSLM = useCallback(async () => {
    // NOTE: Cette fonction est disponible pour usage futur
    void handleGenerateSLM;
    setIsGeneratingSLM(true);
    try {
      const res = await api.get(`/patients/${patientId}/ai-diagnostic`);
      const data = res.data?.report ?? res.data ?? {};
      setDiag({
        squelettique: data.diagnostic_squelettique || data.squelettique || data.skeletal || '',
        compensations_dentaires: data.analyse_dentaire || data.dentaire || data.dental || '',
        plan_therapeutique: data.strategie_therapeutique || data.traitement || data.recommendations || '',
      });
    } catch (e) {
      console.error('[SLM] Génération échouée:', e);
    } finally {
      setIsGeneratingSLM(false);
    }
  }, [patientId]);

  // 
  // IMPRESSION PDF
  // 
  const handlePrint = useCallback(async () => {
    if (!analysisId || !allLandmarksPlaced) return;
    setIsPrinting(true);
    await silentSave();
    try {
      const res = await api.post(`/patients/${patientId}/pdf`, {
        ai_diagnostic: {
          squelettique: diag.squelettique || '',
          dentaire: diag.compensations_dentaires || '',
          traitement: diag.plan_therapeutique || '',
        },
        clinical_data: {
          ddm_maxillaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: ddmMaxClinique ?? 0 },
          ddm_mandibulaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: ddmMandClinique ?? 0 },
          ddm_reelle: ddmReelleTotale,
          plan_traitement: diag.plan_therapeutique || '',
        },
        archive: false,
      }, { responseType: 'blob' as any });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      // Demander confirmation avant d'ouvrir (l'impression peut échouer)
      const userChoice = window.confirm(
        'Le PDF a été généré avec succès.\n\n' +
        '• OK = Ouvrir dans un nouvel onglet (pour imprimer)\n' +
        '• Annuler = Télécharger le fichier\n\n' +
        'Note: Si l\'impression échoue, vous pourrez ré-ouvrir le PDF depuis le dossier patient.'
      );
      
      if (userChoice) {
        // Ouvrir dans un nouvel onglet pour l'impression
        const printWindow = window.open(url, '_blank');
        if (printWindow) {
          // Attendre que le PDF soit chargé avant de révoquer l'URL
          setTimeout(() => URL.revokeObjectURL(url), 60000);
        } else {
          // Popup bloqué, fallback sur téléchargement
          const link = document.createElement('a');
          link.href = url;
          link.download = `Bilan_COM_${patientName.replace(/\s+/g, '_')}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          setTimeout(() => URL.revokeObjectURL(url), 60000);
          alert('Le popup a été bloqué. Le PDF a été téléchargé à la place.');
        }
      } else {
        // Téléchargement direct
        const link = document.createElement('a');
        link.href = url;
        link.download = `Bilan_COM_${patientName.replace(/\s+/g, '_')}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      }
    } catch (e) {
      console.error('[PDF] Erreur génération:', e);
    } finally {
      setIsPrinting(false);
    }
  }, [analysisId, allLandmarksPlaced, patientId, patientName, diag, ddm, ddmMaxClinique, ddmMandClinique, ddmReelleTotale, silentSave]);


  // 
  // RENDU ÉTAPE 1 - CÉPHALOMÉTRIE
  // 
  const renderStep1 = () => {
    if (!imageSrc) {
      return (
        <div className="flex-1 w-full flex flex-col items-center justify-center min-h-[400px]">
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={e => handleFileDrop(e.target.files)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center gap-6 max-w-md w-full px-6"
          >
            <div
              className="w-full flex flex-col items-center justify-center gap-6 rounded-2xl py-16 cursor-pointer transition-all duration-200"
              onClick={() => !isUploading && fileRef.current?.click()}
              style={{ border: `2px dashed ${P.border}`, background: P.bgCard }}
              onDragOver={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.accent; }}
              onDragLeave={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.border; }}
              onDrop={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.border; handleFileDrop(e.dataTransfer.files); }}
            >
              {isUploading ? (
                <div className="flex flex-col items-center gap-3">
                  <Loader2 size={40} className="animate-spin" style={{ color: P.accent }} />
                  <span className="text-sm font-mono" style={{ color: P.textMuted }}>Analyse IA en cours...</span>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: `${P.accent}15` }}>
                    <Upload size={32} style={{ color: P.accent }} />
                  </div>
                  <div className="text-center space-y-1">
                    <div className="font-semibold" style={{ color: P.text }}>Uploader une radiographie</div>
                    <div className="text-xs" style={{ color: P.textMuted }}>Glissez-déposez ou cliquez pour parcourir</div>
                  </div>
                </>
              )}
            </div>
            {uploadError && (
              <div className="flex items-center gap-2 text-sm" style={{ color: P.accentError }}>
                <AlertCircle size={16} />
                {uploadError}
              </div>
            )}
          </motion.div>
        </div>
      );
    }

    return (
      <div ref={step1ContainerRef} className={`flex flex-col gap-4 ${isStep1Fullscreen ? 'fixed inset-0 z-[9999] p-4' : ''}`} style={{ background: isStep1Fullscreen ? P.bg : 'transparent' }}>
        {/* Barre d'outils */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMode(m => m === 'light' ? 'dark' : 'light')}
              className="p-1.5 rounded-lg transition-all"
              style={{ border: `1px solid ${P.border}`, color: P.textDim }}
              title={mode === 'light' ? 'Mode sombre' : 'Mode clair'}
            >
              {mode === 'light' ? <Moon size={14} /> : <Sun size={14} />}
            </button>
          </div>
          <div className="w-px h-4 opacity-20" style={{ background: P.border }} />
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-mono" style={{ color: P.textDim }}>L</span>
            <input type="range" min={50} max={200} value={imgFilters.brightness} onChange={e => setImgFilters(f => ({ ...f, brightness: +e.target.value }))} className="w-20 h-1 cursor-pointer" style={{ accentColor: P.accent }} title="Luminosité" />
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-mono" style={{ color: P.textDim }}>C</span>
            <input type="range" min={50} max={300} value={imgFilters.contrast} onChange={e => setImgFilters(f => ({ ...f, contrast: +e.target.value }))} className="w-20 h-1 cursor-pointer" style={{ accentColor: P.accentWarning }} title="Contraste" />
          </div>
          <button onClick={() => setImgFilters(f => ({ ...f, invert: !f.invert }))} className="px-2 py-1 rounded text-[10px] font-mono transition-all" style={{ background: imgFilters.invert ? `${P.accent}20` : 'transparent', border: `1px solid ${imgFilters.invert ? P.accent : P.border}`, color: imgFilters.invert ? P.accent : P.textDim }}>INV</button>
          
          {/* Bouton Calibration */}
          <button
            onClick={() => { setShowCalibration(true); setCalibrationClickPoints([]); setCalibrationDistance(''); setCalibrationStep('selecting'); }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all ml-2"
            style={{
              background: isCalibrated ? `${P.accentSuccess}15` : `${P.accentWarning}15`,
              border: `1px solid ${isCalibrated ? P.accentSuccess : P.accentWarning}`,
              color: isCalibrated ? P.accentSuccess : P.accentWarning,
            }}
            title={isCalibrated ? `Calibré: ${mmPerPixel?.toFixed(4)} mm/pixel` : 'Calibrer l\'échelle mm/pixel'}
          >
            <Target size={13} />
            {isCalibrated ? 'Calibré' : 'Calibrer'}
          </button>

          {/* Loupe */}
          <div className="ml-auto">
            <button onClick={() => setMagnifierEnabled(v => !v)} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all" style={{ background: magnifierEnabled ? `${P.accent}15` : 'transparent', border: `1px solid ${magnifierEnabled ? P.accent : P.border}`, color: magnifierEnabled ? P.accent : P.textMuted }}>
              {magnifierEnabled ? <ZoomOut size={13} /> : <ZoomIn size={13} />}
            </button>
          </div>
          <button onClick={() => { setImageSrc(undefined); setLocal({ landmarks: [], version: 0 }); setAnglesData({}); }} className="p-1.5 rounded-lg transition-all" style={{ border: `1px solid ${P.border}`, color: P.textDim }} title="Changer d'image"><RefreshCw size={12} /></button>
          
          {/* Réinitialiser apex aux normes COM */}
          <button 
            onClick={() => {
              const newLms = initializeDefaultApexes(local.landmarks);
              setLocal(prev => ({ landmarks: newLms, version: prev.version + 1 }));
            }} 
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all" 
            style={{ background: `${P.accentSuccess}15`, border: `1px solid ${P.accentSuccess}40`, color: P.accentSuccess }}
            title="Réinitialiser les apex aux normes COM (IMPA 90°, I/F 107°)"
          >
            <Target size={12} />
            Apex COM
          </button>
          <button onClick={() => setIsStep1Fullscreen(v => !v)} className="p-1.5 rounded-lg transition-all" style={{ border: `1px solid ${isStep1Fullscreen ? P.accent : P.border}`, color: isStep1Fullscreen ? P.accent : P.textDim, background: isStep1Fullscreen ? `${P.accent}15` : 'transparent' }} title={isStep1Fullscreen ? 'Quitter plein écran' : 'Plein écran'}>
            {isStep1Fullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
          </button>
        </div>

        {/* Bouton Quitter Plein écran */}
        <AnimatePresence>
          {isStep1Fullscreen && (
            <motion.button initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} onClick={() => setIsStep1Fullscreen(false)} className="fixed top-6 right-6 flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-lg z-[10000]" style={{ background: `${P.accentError}25`, border: `2px solid ${P.accentError}`, color: P.accentError, backdropFilter: 'blur(12px)' }}>
              <X size={14} /> Quitter (ESC)
            </motion.button>
          )}
        </AnimatePresence>

        {/* Alerte Mode MOCK */}
        <AnimatePresence>
          {visionMetadata.mode_inference === "MOCK" && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex flex-col gap-2 px-4 py-3 rounded-xl" style={{ background: `${P.accentError}15`, border: `2px solid ${P.accentError}60` }}>
              <div className="flex items-center gap-2">
                <AlertCircle size={16} style={{ color: P.accentError }} />
                <span className="text-sm font-bold" style={{ color: P.accentError }}>Mode Démonstration - IA Non Disponible</span>
              </div>
              <div className="text-[11px] font-mono" style={{ color: P.textMuted }}>
                {visionMetadata.warning || "Les points sont placés aléatoirement. Ne pas utiliser pour un diagnostic réel."}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Interface de Calibration V2 */}
        <AnimatePresence>
          {showCalibration && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex flex-col gap-3 px-4 py-4 rounded-xl" style={{ background: `${P.accent}10`, border: `2px solid ${P.accent}60` }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target size={16} style={{ color: P.accent }} />
                  <span className="text-sm font-bold" style={{ color: P.accent }}>
                    Calibration de l'échelle (mm/pixel)
                  </span>
                </div>
                <button onClick={cancelCalibration} className="p-1 rounded hover:bg-white/10"><X size={14} style={{ color: P.textDim }} /></button>
              </div>
              
              {calibrationStep === 'selecting' ? (
                <>
                  <div className="text-[11px]" style={{ color: P.textMuted }}>
                    {calibrationClickPoints.length === 0 && "Cliquez sur le premier point de référence sur l'image (début de la distance connue)."}
                    {calibrationClickPoints.length === 1 && "Cliquez sur le deuxième point de référence sur l'image (fin de la distance connue)."}
                    {calibrationClickPoints.length === 2 && "Parfait ! Maintenant entrez la distance réelle entre ces deux points."}
                  </div>
                  
                  {calibrationClickPoints.length === 2 && (
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs" style={{ color: P.textMuted }}>Distance réelle (mm):</span>
                        <input type="number" value={calibrationDistance} onChange={(e) => setCalibrationDistance(e.target.value)} placeholder="10" className="w-24 px-2 py-1 rounded text-xs" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }} />
                      </div>
                      <button onClick={() => setCalibrationStep('entering')} disabled={!calibrationDistance || parseFloat(calibrationDistance) <= 0} className="px-3 py-2 rounded-lg text-xs font-semibold transition-all disabled:opacity-50" style={{ background: P.accent, color: 'white' }}>Valider</button>
                    </div>
                  )}
                  
                  {calibrationClickPoints.length > 0 && (
                    <button onClick={() => setCalibrationClickPoints([])} className="text-[10px] underline" style={{ color: P.textMuted }}>Recommencer</button>
                  )}
                </>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="text-xs" style={{ color: P.textMuted }}>
                    Distance: <strong>{calibrationDistance} mm</strong> entre {calibrationClickPoints.length} points
                  </div>
                  <button onClick={applyCalibration} className="px-3 py-2 rounded-lg text-xs font-semibold transition-all" style={{ background: P.accentSuccess, color: 'white' }}>Appliquer</button>
                  <button onClick={() => setCalibrationStep('selecting')} className="text-[10px] underline" style={{ color: P.textMuted }}>Modifier</button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Indicateur Apex à repositionner */}
        {!hasApexAdjusted && !showCalibration && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ background: `${P.accentWarning}15`, border: `1px solid ${P.accentWarning}60` }}>
            <Activity size={16} style={{ color: P.accentWarning }} />
            <div className="flex-1">
              <div className="text-xs font-semibold" style={{ color: P.accentWarning }}>Repositionnement des apex requis</div>
              <div className="text-[10px]" style={{ color: P.textMuted }}>Déplacez U1_apex et L1_apex à la racine des incisives avant de passer aux moulages</div>
            </div>
          </motion.div>
        )}

        {/* Canvas Radiographique */}
        <div className={`relative flex-1 rounded-2xl overflow-hidden ${isStep1Fullscreen ? 'h-[calc(100vh-180px)]' : 'min-h-[500px]'}`} style={{ background: '#000' }}>
          <CephaloTracingLayer
            imageSrc={imageSrc}
            imgFilters={imgFilters}
            landmarks={local.landmarks}
            baseOpacity={1}
            imageWidth={imgDim.w}
            imageHeight={imgDim.h}
            onUpdateLandmarks={updateLandmarksOptimistic}
            activePointId={activePointId}
            focusedPointId={null}
            onPointMouseDown={setActivePointId}
            visualDebug={anglesData?.visual_debug ?? null}
            isCalibrating={showCalibration}
            calibrationPoints={calibrationClickPoints}
            onAddCalibrationPoint={handleCalibrationClick}
            uiMode={mode === 'dark' ? 'pro' : 'standard'}
            hoveredMetric={null}
            magnifierEnabled={magnifierEnabled}
          />
          
          {/* Overlay Calibration */}
          {showCalibration && calibrationClickPoints.length < 2 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="px-4 py-2 rounded-lg text-sm font-medium" style={{ background: 'rgba(0,0,0,0.7)', color: '#fff', backdropFilter: 'blur(4px)' }}>
                {calibrationClickPoints.length === 0 ? "Cliquez pour placer le premier point" : "Cliquez pour placer le deuxième point"}
              </div>
            </div>
          )}
        </div>

        {/* Status bar */}
        <div className="flex items-center justify-between text-[10px] font-mono px-2" style={{ color: P.textDim }}>
          <div className="flex items-center gap-3">
            <span>Points: {local.landmarks.length}</span>
            {isCalibrated && <span>Échelle: {mmPerPixel?.toFixed(4)} mm/px</span>}
          </div>
          <div className="flex items-center gap-2">
            {!isCalibrated && <span style={{ color: P.accentWarning }}>⚠ Non calibré</span>}
            {!hasApexAdjusted && <span style={{ color: P.accentWarning }}>⚠ Apex à repositionner</span>}
          </div>
        </div>

        <AnimatePresence>
          {syncState !== 'idle' && <SyncBadge state={syncState} P={P} />}
        </AnimatePresence>
      </div>
    );
  };


  // 
  // RENDU ÉTAPE 2 - MOULAGES
  // 
  const renderStep2 = () => (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-semibold" style={{ color: P.text }}>Analyse des Moulages</h3>
        <p className="text-sm" style={{ color: P.textMuted }}>
          Saisissez les valeurs mesurées sur les moulages en plâtre pour calculer la DDM Réelle.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* DDM Maxillaire */}
        <div className="flex flex-col gap-3 p-4 rounded-xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${P.accent}15` }}>
              <span className="text-sm font-bold" style={{ color: P.accent }}>M</span>
            </div>
            <span className="font-medium" style={{ color: P.text }}>DDM Maxillaire</span>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs" style={{ color: P.textMuted }}>Valeur mesurée sur moulage (mm)</label>
            <input
              type="number"
              step="0.1"
              value={ddm.maxillaire}
              onChange={(e) => setDdm(prev => ({ ...prev, maxillaire: e.target.value === '' ? '' : parseFloat(e.target.value) }))}
              className="px-3 py-2 rounded-lg text-sm"
              style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
              placeholder="0.0"
            />
          </div>
          {ddmMaxReelle !== null && (
            <div className="flex items-center justify-between text-xs px-2 py-1 rounded" style={{ background: P.bgPanel }}>
              <span style={{ color: P.textMuted }}>DDM Réelle:</span>
              <span className="font-mono font-bold" style={{ color: P.accent }}>{fmtNum(ddmMaxReelle)} mm</span>
            </div>
          )}
        </div>

        {/* DDM Mandibulaire */}
        <div className="flex flex-col gap-3 p-4 rounded-xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${P.accentSuccess}15` }}>
              <span className="text-sm font-bold" style={{ color: P.accentSuccess }}>m</span>
            </div>
            <span className="font-medium" style={{ color: P.text }}>DDM Mandibulaire</span>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs" style={{ color: P.textMuted }}>Valeur mesurée sur moulage (mm)</label>
            <input
              type="number"
              step="0.1"
              value={ddm.mandibulaire}
              onChange={(e) => setDdm(prev => ({ ...prev, mandibulaire: e.target.value === '' ? '' : parseFloat(e.target.value) }))}
              className="px-3 py-2 rounded-lg text-sm"
              style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
              placeholder="0.0"
            />
          </div>
          {ddmMandReelle !== null && (
            <div className="flex items-center justify-between text-xs px-2 py-1 rounded" style={{ background: P.bgPanel }}>
              <span style={{ color: P.textMuted }}>DDM Réelle:</span>
              <span className="font-mono font-bold" style={{ color: P.accentSuccess }}>{fmtNum(ddmMandReelle)} mm</span>
            </div>
          )}
        </div>
      </div>

      {ddmReelleTotale !== null && (
        <div className="flex items-center justify-between p-4 rounded-xl" style={{ background: `${P.accent}10`, border: `2px solid ${P.accent}40` }}>
          <span className="font-medium" style={{ color: P.text }}>DDM Réelle Totale</span>
          <span className="text-2xl font-mono font-bold" style={{ color: P.accent }}>{fmtNum(ddmReelleTotale)} mm</span>
        </div>
      )}

      <div className="text-xs p-3 rounded-lg" style={{ background: P.bgCard, border: `1px solid ${P.border}`, color: P.textMuted }}>
        <strong style={{ color: P.text }}>Formule:</strong> DDM Réelle = DDM Clinique + ((IMPA - 90°) / 2.5)
        <br />
        <span className="opacity-70">La DDM Céphalo dépend de l'inclinaison incisive (IMPA actuel: {impaActuel ?? '-'}°)</span>
      </div>

      {/* EXAMEN OCCLUSAL - Classe d'Angle */}
      <div className="p-6 rounded-xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <h4 className="text-lg font-semibold mb-4" style={{ color: P.text }}>Examen Occlusal (Classe d'Angle)</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Molaire Gauche', key: 'molaire_gauche' },
            { label: 'Molaire Droite', key: 'molaire_droite' },
            { label: 'Canine Gauche', key: 'canine_gauche' },
            { label: 'Canine Droite', key: 'canine_droite' },
          ].map((item) => (
            <div key={item.key} className="flex flex-col gap-2">
              <label className="text-xs" style={{ color: P.textMuted }}>{item.label}</label>
              <select 
                value={etape2Data.occlusal[item.key as keyof ExamenOcclusal]} 
                onChange={(e) => setEtape2Data(prev => ({ 
                  ...prev, 
                  occlusal: { ...prev.occlusal, [item.key]: e.target.value as ClasseAngle }
                }))}
                className="px-3 py-2 rounded-lg text-sm"
                style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
              >
                <option value="I">Classe I</option>
                <option value="II">Classe II</option>
                <option value="III">Classe III</option>
              </select>
            </div>
          ))}
        </div>
        {hasSubdivision && (
          <div className="mt-4 p-3 rounded-lg text-sm" style={{ background: `${P.accentWarning}15`, border: `1px solid ${P.accentWarning}40`, color: P.accentWarning }}>
            ⚠ Subdivision détectée (asymétrie droite/gauche)
          </div>
        )}
      </div>
    </div>
  );

  // 
  // RENDU ÉTAPE 3 - PROTOCOLE COM COMPLET
  // 
  const renderStep3 = () => (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto pb-20">
      
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold" style={{ color: P.text }}>DOSSIER CLINIQUE ORTHODONTIQUE</h3>
          <p className="text-sm" style={{ color: P.textMuted }}>Protocole COM - Analyse Céphalométrique et Arbre Décisionnel</p>
        </div>
        <button
          onClick={() => {
            // Copier le plan dans le diagnostic
            setDiag(prev => ({ ...prev, plan_therapeutique: planTraitement }));
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
          style={{ background: P.accent, color: 'white' }}
        >
          <Activity size={16} />
          Intégrer au PDF
        </button>
      </div>

      {/* 1. IDENTIFICATION */}
      <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
          <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: P.accent, color: 'white' }}>1</span>
          Identification du Patient
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium" style={{ color: P.textMuted }}>Nom du patient</label>
            <input type="text" value={patientName} readOnly className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, color: P.text }} />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium" style={{ color: P.textMuted }}>Âge chronologique (ans)</label>
            <input type="number" value={etape3Data.age} onChange={(e) => setEtape3Data(prev => ({ ...prev, age: e.target.value === '' ? '' : parseFloat(e.target.value) }))} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }} placeholder="12" />
            <span className="text-xs" style={{ color: P.textDim }}>Le CVM se calcule auto.</span>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium" style={{ color: P.textMuted }}>Stade CVM <span style={{ color: P.accent }}>(Auto)</span></label>
            <div className="flex items-center gap-2">
              <select value={etape3Data.cvm} onChange={(e) => setEtape3Data(prev => ({ ...prev, cvm: e.target.value as CVMStage }))} className="flex-1 px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}>
                <option value="">Sélectionner...</option>
                <option value="CS1">CS1 (Pré-pic)</option>
                <option value="CS2">CS2 (Pré-pic)</option>
                <option value="CS3">CS3 (★ PIC)</option>
                <option value="CS4">CS4 (★ PIC)</option>
                <option value="CS5">CS5 (Post-pic)</option>
                <option value="CS6">CS6 (Terminé)</option>
              </select>
            </div>
            {etape3Data.cvm && (
              <span className="text-xs" style={{ color: P.textDim }}>Basé sur {sexePatient === 'F' ? 'fille' : 'garçon'} de {etape3Data.age || '?'} ans</span>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium" style={{ color: P.textMuted }}>Date des télés</label>
            <input type="date" value={etape3Data.date_teles} onChange={(e) => setEtape3Data(prev => ({ ...prev, date_teles: e.target.value }))} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }} />
          </div>
        </div>
        {etape3Data.cvm === 'CS3' || etape3Data.cvm === 'CS4' ? (
          <div className="mt-4 p-3 rounded-lg text-sm" style={{ background: `${P.accentSuccess}15`, border: `1px solid ${P.accentSuccess}40`, color: P.accentSuccess }}>
            ✓ Fenêtre d'efficacité maximale pour les appareils fonctionnels (pic de croissance mandibulaire)
          </div>
        ) : null}
      </section>

      {/* 2. ANALYSE CÉPHALOMÉTRIQUE */}
      <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-bold flex items-center gap-2" style={{ color: P.text }}>
            <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: P.accent, color: 'white' }}>2</span>
            Analyse Céphalométrique (Normes COM)
          </h4>
          {anglesData?.metrics && (
            <button
              onClick={autoFillAnalyses}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{ background: P.accent, color: 'white' }}
            >
              <RefreshCw size={14} />
              Remplir avec valeurs calculées
            </button>
          )}
        </div>
        
        {/* 2.1 Analyse Dentaire -->
        <div className="mb-6">
          <h5 className="text-sm font-semibold mb-3" style={{ color: P.textMuted }}>2.1 Analyse Dentaire</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: P.bgPanel }}>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Mesure</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Norme</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Compensation</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Valeur Patient</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Interprétation</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'Surplomb (mm)', norme: '1,5 à 3 mm', comp: '0 à 5 mm', key: 'surplomb', unit: 'mm', interp: (v: number) => v > 5 ? 'Protrusion' : v < 0 ? 'Rétro' : 'Normal' },
                  { label: 'Recouvrement (mm)', norme: '1,5 à 3 mm', comp: '0 à 5 mm', key: 'recouvrement', unit: 'mm', interp: (v: number) => v > 5 ? 'Supraclusion' : v < 0 ? 'Béance' : 'Normal' },
                  { label: 'I / Mandibulaire (°)', norme: '90° ± 5', comp: '80-100°', key: 'impa', unit: '°', interp: (v: number) => v > 100 ? 'Proclinaison' : v < 80 ? 'Rétroclinaison' : 'Normal' },
                  { label: 'I / Francfort (°)', norme: '107° ± 5', comp: '97-120°', key: 'i_francfort', unit: '°', interp: (v: number) => v > 120 ? 'Proclinaison' : v < 97 ? 'Rétroclinaison' : 'Normal' },
                  { label: 'Inter-Incisif (°)', norme: '131° ± 13', comp: '120-142°', key: 'inter_incisif', unit: '°', interp: (v: number) => v < 120 ? 'Fermeture' : v > 142 ? 'Ouverture' : 'Normal' },
                ].map((row, idx) => (
                  <tr key={row.key} style={{ borderBottom: `1px solid ${P.border}` }}>
                    <td className="p-3" style={{ color: P.text }}>{row.label}</td>
                    <td className="p-3" style={{ color: P.textMuted }}>{row.norme}</td>
                    <td className="p-3" style={{ color: P.textMuted }}>{row.comp}</td>
                    <td className="p-3">
                      <input 
                        type="number" 
                        step="0.1"
                        value={etape3Data.dentaire[row.key as keyof AnalyseDentaire]} 
                        onChange={(e) => setEtape3Data(prev => ({ 
                          ...prev, 
                          dentaire: { ...prev.dentaire, [row.key]: e.target.value === '' ? '' : parseFloat(e.target.value) }
                        }))}
                        className="w-24 px-2 py-1 rounded text-center"
                        style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
                      />
                    </td>
                    <td className="p-3">
                      {etape3Data.dentaire[row.key as keyof AnalyseDentaire] !== '' && (
                        <span className={`text-xs px-2 py-1 rounded ${row.interp(Number(etape3Data.dentaire[row.key as keyof AnalyseDentaire])) !== 'Normal' ? 'font-bold' : ''}`}
                          style={{ 
                            background: row.interp(Number(etape3Data.dentaire[row.key as keyof AnalyseDentaire])) !== 'Normal' ? `${P.accentWarning}30` : `${P.accentSuccess}20`,
                            color: row.interp(Number(etape3Data.dentaire[row.key as keyof AnalyseDentaire])) !== 'Normal' ? P.accentWarning : P.accentSuccess
                          }}
                        >
                          {row.interp(Number(etape3Data.dentaire[row.key as keyof AnalyseDentaire]))}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 2.2 Analyse Osseuse */}
        <div>
          <h5 className="text-sm font-semibold mb-3" style={{ color: P.textMuted }}>2.2 Analyse Osseuse</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: P.bgPanel }}>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Mesure</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Norme (9 ans)</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Norme (Adulte)</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Valeur Patient</th>
                  <th className="p-3 text-left font-medium" style={{ color: P.textMuted }}>Interprétation</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'Angle de Tweed (°)', norme9: '26° ± 4°', normeAd: '26° ± 4°', key: 'angle_tweed', interp: (v: number) => v < 20 ? 'Hypodivergent' : v > 30 ? 'Hyperdivergent' : 'Normodivergent' },
                  { label: 'Décalage A\'B\' (mm)', norme9: '+4,2 ± 3,2', normeAd: '+2,3 ± 3,1', key: 'decalage_ab', interp: (v: number) => v < 0 ? 'Classe III' : v > 4 ? 'Classe II' : 'Classe I' },
                  { label: 'Situation A (mm)', norme9: '+2,8 ± 3,3', normeAd: '+2,3 ± 3', key: 'situation_a', interp: (v: number) => v > 6 ? 'Prognathie' : v < 0 ? 'Rétro' : 'Normal' },
                  { label: 'Situation B (mm)', norme9: '-1,5 ± 4,5', normeAd: '0,0 ± 4,9', key: 'situation_b', interp: (v: number) => v < -6 ? 'Rétrognathie' : v > 3 ? 'Prognathie' : 'Normal' },
                  { label: 'Profondeur Faciale (°)', norme9: '61,3 ± 5', normeAd: '70,3 ± 5', key: 'profondeur_faciale', interp: (v: number) => v < 56 ? 'Convexe' : v > 75 ? 'Concave' : 'Droit' },
                ].map((row) => (
                  <tr key={row.key} style={{ borderBottom: `1px solid ${P.border}` }}>
                    <td className="p-3" style={{ color: P.text }}>{row.label}</td>
                    <td className="p-3" style={{ color: P.textMuted }}>{row.norme9}</td>
                    <td className="p-3" style={{ color: P.textMuted }}>{row.normeAd}</td>
                    <td className="p-3">
                      <input 
                        type="number" 
                        step="0.1"
                        value={etape3Data.osseuse[row.key as keyof AnalyseOsseuse]} 
                        onChange={(e) => setEtape3Data(prev => ({ 
                          ...prev, 
                          osseuse: { ...prev.osseuse, [row.key]: e.target.value === '' ? '' : parseFloat(e.target.value) }
                        }))}
                        className="w-24 px-2 py-1 rounded text-center"
                        style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
                      />
                    </td>
                    <td className="p-3">
                      {etape3Data.osseuse[row.key as keyof AnalyseOsseuse] !== '' && (
                        <span className="text-xs px-2 py-1 rounded" style={{ 
                          background: row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Normal' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Normodivergent' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Droit' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Classe I' ? `${P.accentSuccess}20` : `${P.accentWarning}30`,
                          color: row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Normal' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Normodivergent' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Droit' || row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse])) === 'Classe I' ? P.accentSuccess : P.accentWarning
                        }}>
                          {row.interp(Number(etape3Data.osseuse[row.key as keyof AnalyseOsseuse]))}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* 3. MOULAGES & DDM */}
      <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
          <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: P.accent, color: 'white' }}>3</span>
          Analyse des Moulages et DDM
        </h4>
        
        {/* Calcul DDM - Auto-calculé depuis Étape 2 et angles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <label className="text-xs font-medium block mb-2" style={{ color: P.textMuted }}>DDM Clinique (moulages)</label>
            <div className="text-2xl font-mono font-bold px-3 py-2" style={{ color: P.text }}>
              {Number(etape3Data.ddm_clinique).toFixed(1)} mm
            </div>
            <span className="text-xs" style={{ color: P.textDim }}>Auto: -(Max {ddm.maxillaire || 0} + Mand {ddm.mandibulaire || 0}) = {etape3Data.ddm_clinique}mm</span>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <label className="text-xs font-medium block mb-2" style={{ color: P.textMuted }}>DDM Céphalo (compensation)</label>
            <div className="text-2xl font-mono font-bold px-3 py-2" style={{ color: P.text }}>
              {Number(etape3Data.ddm_cephalo).toFixed(1)} mm
            </div>
            <span className="text-xs" style={{ color: P.textDim }}>Formule: ((IMPA-90)+(I/F-107))/2.5</span>
          </div>
          <div className="p-4 rounded-xl" style={{ background: `${P.accent}15`, border: `2px solid ${P.accent}40` }}>
            <label className="text-xs font-medium block mb-2" style={{ color: P.accent }}>DDM Réelle Totale</label>
            <div className="text-3xl font-mono font-bold" style={{ color: P.accent }}>{ddmReelleCalc.toFixed(1)} mm</div>
            <span className="text-xs" style={{ color: P.textMuted }}>Clinique + Céphalo</span>
          </div>
        </div>

        {/* Sévérité DDM */}
        {severiteDDM && (
          <div className={`p-4 rounded-xl mb-6 ${severiteDDM === 'sévère' ? 'border-2' : ''}`} style={{ 
            background: severiteDDM === 'sévère' ? `${P.accentError}15` : severiteDDM === 'modéré' ? `${P.accentWarning}15` : severiteDDM === 'excès' ? `${P.accentSuccess}15` : `${P.accentSuccess}15`,
            borderColor: severiteDDM === 'sévère' ? P.accentError : severiteDDM === 'modéré' ? P.accentWarning : P.accentSuccess
          }}>
            <div className="flex items-center justify-between">
              <span className="font-medium" style={{ color: P.text }}>Classification DDM:</span>
              <span className="text-xl font-bold" style={{ 
                color: severiteDDM === 'sévère' ? P.accentError : severiteDDM === 'modéré' ? P.accentWarning : P.accentSuccess 
              }}>
                {severiteDDM === 'sévère' ? '⚠ SÉVÈRE' : severiteDDM === 'modéré' ? 'MODÉRÉE' : severiteDDM === 'excès' ? 'EXCÈS D\'ESPACE' : 'LÉGÈRE'}
              </span>
            </div>
            <p className="text-sm mt-2" style={{ color: P.textMuted }}>
              {severiteDDM === 'sévère' ? 'Extraction probable (déficit > 6mm)' : severiteDDM === 'modéré' ? 'Borderline (déficit 3-6mm)' : severiteDDM === 'excès' ? 'Excès d\'espace (espacements)' : 'Léger déficit (0-3mm) - sans extraction'}
            </p>
          </div>
        )}

        {/* DDM par Arcade (depuis Étape 2) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <label className="text-xs font-medium block mb-2" style={{ color: P.textMuted }}>DDM Maxillaire (Étape 2)</label>
            <div className="text-2xl font-mono font-bold" style={{ color: P.accent }}>
              {ddm.maxillaire === '' ? '-' : ddm.maxillaire} mm
            </div>
            <span className="text-xs" style={{ color: P.textDim }}>Clinique mesurée</span>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <label className="text-xs font-medium block mb-2" style={{ color: P.textMuted }}>DDM Mandibulaire (Étape 2)</label>
            <div className="text-2xl font-mono font-bold" style={{ color: P.accentSuccess }}>
              {ddm.mandibulaire === '' ? '-' : ddm.mandibulaire} mm
            </div>
            <span className="text-xs" style={{ color: P.textDim }}>Clinique mesurée</span>
          </div>
        </div>

        {/* Classification Classe II */}
        {(etape2Data.occlusal.molaire_gauche === 'II' || etape2Data.occlusal.molaire_droite === 'II') && (
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <h5 className="text-sm font-semibold mb-3" style={{ color: P.textMuted }}>Classification Classe II</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Division</label>
                <select value={etape3Data.division || ''} onChange={(e) => setEtape3Data(prev => ({ ...prev, division: e.target.value as DivisionClasseII }))} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}>
                  <option value="">Sélectionner...</option>
                  <option value="1">Division 1 (Proclinées)</option>
                  <option value="2">Division 2 (Rétroclinées)</option>
                </select>
                {etape3Data.division === '1' && <span className="text-xs" style={{ color: P.textDim }}>Overjet important, arcade en V</span>}
                {etape3Data.division === '2' && <span className="text-xs" style={{ color: P.textDim }}>Overbite profond, arcade en U</span>}
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Type d'Arcade</label>
                <select value={etape3Data.type_arcade || ''} onChange={(e) => setEtape3Data(prev => ({ ...prev, type_arcade: e.target.value as TypeArcade }))} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}>
                  <option value="">Sélectionner...</option>
                  <option value="I">Type I (V, étroite)</option>
                  <option value="II">Type II (U, carrée)</option>
                </select>
                {etape3Data.type_arcade === 'I' && <span className="text-xs" style={{ color: P.textDim }}>Expansion indiquée</span>}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 4. RÉSUMÉ DIAGNOSTIQUE 3D */}
      <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
          <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: P.accent, color: 'white' }}>4</span>
          Résumé Diagnostic Global 3D
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Sagittal</div>
            <div className="font-bold text-lg" style={{ color: classeSquelettique.includes('III') ? P.accentError : classeSquelettique.includes('II') ? P.accentWarning : P.accentSuccess }}>
              {classeSquelettique || 'Non déterminé'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>Basé sur Décalage A'B'</div>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Vertical</div>
            <div className="font-bold text-lg" style={{ color: P.text }}>
              {patternVertical === 'hypodivergent' ? 'Hypodivergent' : patternVertical === 'hyperdivergent' ? 'Hyperdivergent' : patternVertical === 'normodivergent' ? 'Normodivergent' : 'Non déterminé'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>Basé sur Angle de Tweed</div>
            {patternVertical === 'hyperdivergent' && <div className="text-xs mt-2" style={{ color: P.accentWarning }}>⚠ Éviter extractions mand.</div>}
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Transversal</div>
            <div className="font-bold text-lg" style={{ color: P.text }}>
              {hasSubdivision ? 'Asymétrique' : etape3Data.type_arcade === 'I' ? 'Constriction' : 'Symétrique'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>Basé sur moulages/type arcade</div>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Espace (DDM)</div>
            <div className="font-bold text-lg" style={{ color: severiteDDM === 'sévère' ? P.accentError : severiteDDM === 'modéré' ? P.accentWarning : P.accentSuccess }}>
              {severiteDDM ? severiteDDM.charAt(0).toUpperCase() + severiteDDM.slice(1) : 'Non calculé'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>{ddmReelleCalc.toFixed(1)} mm</div>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Profil Cutané</div>
            <div className="font-bold text-lg" style={{ color: profilFacial === 'convexe' ? P.accentWarning : profilFacial === 'concave' ? P.accentError : P.accentSuccess }}>
              {profilFacial ? profilFacial.charAt(0).toUpperCase() + profilFacial.slice(1) : 'Non déterminé'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>Basé sur Profondeur Faciale</div>
          </div>
          <div className="p-4 rounded-xl" style={{ background: P.bgPanel }}>
            <div className="text-xs uppercase tracking-wide mb-2" style={{ color: P.textMuted }}>Croissance</div>
            <div className="font-bold text-lg" style={{ color: etape3Data.cvm === 'CS3' || etape3Data.cvm === 'CS4' ? P.accentSuccess : P.text }}>
              {etape3Data.cvm ? etape3Data.cvm : 'Non évalué'}
            </div>
            <div className="text-xs mt-1" style={{ color: P.textDim }}>
              {etape3Data.cvm === 'CS3' || etape3Data.cvm === 'CS4' ? 'Pic de croissance' : etape3Data.cvm === 'CS1' || etape3Data.cvm === 'CS2' ? 'Pré-pic' : etape3Data.cvm === 'CS5' || etape3Data.cvm === 'CS6' ? 'Fin de croissance' : ''}
            </div>
          </div>
        </div>
      </section>

      {/* 5. PLAN DE TRAITEMENT */}
      <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
        <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
          <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm" style={{ background: P.accent, color: 'white' }}>5</span>
          Plan de Traitement (Arbre Décisionnel)
        </h4>
        
        {planTraitement ? (
          <div className="p-4 rounded-xl whitespace-pre-wrap font-mono text-sm leading-relaxed" style={{ background: P.bgPanel, color: P.text, border: `1px solid ${P.border}` }}>
            {planTraitement}
          </div>
        ) : (
          <div className="p-8 text-center rounded-xl" style={{ background: P.bgPanel, color: P.textMuted }}>
            Remplissez les données d'identification et d'analyse pour générer le plan de traitement automatique.
          </div>
        )}

        {/* Alertes spécifiques */}
        {(etape3Data.dentaire.impa !== '' && Number(etape3Data.dentaire.impa) > 100) && (
          <div className="mt-4 p-4 rounded-xl" style={{ background: `${P.accentError}15`, border: `1px solid ${P.accentError}40` }}>
            <div className="font-bold text-sm" style={{ color: P.accentError }}>⚠ Alerte Extraction</div>
            <div className="text-sm mt-1" style={{ color: P.text }}>IMPA {'>'} 100° : Risque parodontal. L'extraction est indiquée pour la rétraction.</div>
          </div>
        )}
        
        {(etape3Data.dentaire.i_francfort !== '' && Number(etape3Data.dentaire.i_francfort) > 120) && (
          <div className="mt-4 p-4 rounded-xl" style={{ background: `${P.accentError}15`, border: `1px solid ${P.accentError}40` }}>
            <div className="font-bold text-sm" style={{ color: P.accentError }}>⚠ Biproalvéolie</div>
            <div className="text-sm mt-1" style={{ color: P.text }}>I/F {'>'} 120° : Biproalvéolie marquée. Extraction 4 prémolaires probable.</div>
          </div>
        )}
      </section>

      {/* Bouton Sauvegarde */}
      <div className="flex justify-end">
        <button
          onClick={() => {
            setDiag(prev => ({ 
              ...prev, 
              plan_therapeutique: planTraitement,
              squelettique: `${classeSquelettique} - ${patternVertical} - Profil ${profilFacial}`,
              compensations_dentaires: `DDM ${severiteDDM} (${ddmReelleCalc.toFixed(1)}mm)`
            }));
            setSyncState('success');
            setTimeout(() => setSyncState('idle'), 1500);
          }}
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all"
          style={{ background: P.accentSuccess, color: 'white' }}
        >
          <Save size={18} />
          Sauvegarder le Bilan COM
        </button>
      </div>
    </div>
  );

  // 
  // RENDU ÉTAPE 4 - GÉNÉRATION PDF COMPLET
  // 
  const renderStep4 = () => (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto pb-20">
      
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold" style={{ color: P.text }}>Génération du Bilan PDF</h3>
          <p className="text-sm" style={{ color: P.textMuted }}>Export complet avec tracé, analyses et photos</p>
        </div>
        <button
          onClick={handlePrint}
          disabled={!allLandmarksPlaced || isPrinting}
          className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: P.accent, color: 'white' }}
        >
          {isPrinting ? <Loader2 size={18} className="animate-spin" /> : <Printer size={18} />}
          {isPrinting ? 'Génération...' : 'Générer le PDF Complet'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* COLONNE GAUCHE - TRACÉ ET RADIO */}
        <div className="flex flex-col gap-6">
          
          {/* Aperçu du tracé avec radio */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
              <Target size={20} style={{ color: P.accent }} />
              Tracé Céphalométrique
            </h4>
            <div className="relative rounded-xl overflow-hidden" style={{ background: '#000', aspectRatio: '4/5' }}>
              {imageSrc ? (
                <CephaloTracingLayer
                  imageSrc={imageSrc}
                  imgFilters={{ brightness: 100, contrast: 110, invert: false }}
                  landmarks={local.landmarks}
                  baseOpacity={1}
                  imageWidth={imgDim.w}
                  imageHeight={imgDim.h}
                  onUpdateLandmarks={() => {}}
                  activePointId={null}
                  focusedPointId={null}
                  onPointMouseDown={() => {}}
                  visualDebug={anglesData?.visual_debug ?? null}
                  isCalibrating={false}
                  calibrationPoints={[]}
                  onAddCalibrationPoint={() => {}}
                  uiMode={mode === 'dark' ? 'pro' : 'standard'}
                  hoveredMetric={null}
                  magnifierEnabled={false}
                />
              ) : (
                <div className="flex items-center justify-center h-full" style={{ color: P.textMuted }}>
                  Aucune radiographie chargée
                </div>
              )}
            </div>
            <div className="mt-4 flex items-center justify-between text-sm">
              <span style={{ color: P.textMuted }}>Points placés: <strong style={{ color: P.text }}>{local.landmarks.length}</strong></span>
              <span style={{ color: P.textMuted }}>Calibré: <strong style={{ color: isCalibrated ? P.accentSuccess : P.accentError }}>{isCalibrated ? 'Oui' : 'Non'}</strong></span>
            </div>
          </section>

          {/* Informations Patient */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
              <Activity size={20} style={{ color: P.accent }} />
              Informations Patient
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Nom</label>
                <input type="text" value={patientName} readOnly className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, color: P.text }} />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Date de consultation</label>
                <input type="date" value={dateConsultation} onChange={(e) => setDateConsultation(e.target.value)} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }} />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Âge</label>
                <input type="number" value={etape3Data.age} onChange={(e) => setEtape3Data(prev => ({ ...prev, age: e.target.value === '' ? '' : parseFloat(e.target.value) }))} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }} placeholder="ans" />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs" style={{ color: P.textMuted }}>Sexe</label>
                <select value={sexePatient} onChange={(e) => setSexePatient(e.target.value as 'M' | 'F')} className="px-3 py-2 rounded-lg text-sm" style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}>
                  <option value="M">Masculin</option>
                  <option value="F">Féminin</option>
                </select>
              </div>
            </div>
          </section>

          {/* Résumé Analyse */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4" style={{ color: P.text }}>Résumé de l'Analyse</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 rounded-lg" style={{ background: P.bgPanel }}>
                <span style={{ color: P.textMuted }}>Classe Squelettique</span>
                <span className="font-bold" style={{ color: P.text }}>{classeSquelettique || 'Non déterminée'}</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg" style={{ background: P.bgPanel }}>
                <span style={{ color: P.textMuted }}>Pattern Vertical</span>
                <span className="font-bold" style={{ color: P.text }}>{patternVertical || 'Non déterminé'}</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg" style={{ background: P.bgPanel }}>
                <span style={{ color: P.textMuted }}>DDM Réelle</span>
                <span className="font-bold" style={{ color: severiteDDM === 'sévère' ? P.accentError : severiteDDM === 'modéré' ? P.accentWarning : P.accentSuccess }}>
                  {ddmReelleCalc.toFixed(1)} mm {severiteDDM && `(${severiteDDM})`}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg" style={{ background: P.bgPanel }}>
                <span style={{ color: P.textMuted }}>Profil</span>
                <span className="font-bold" style={{ color: P.text }}>{profilFacial || 'Non déterminé'}</span>
              </div>
            </div>
          </section>
        </div>

        {/* COLONNE DROITE - UPLOADS */}
        <div className="flex flex-col gap-6">
          
          {/* Upload Photos */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: P.text }}>
              <Upload size={20} style={{ color: P.accent }} />
              Photos et Documents
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {photos.map((photo) => (
                <div key={photo.id} className="flex flex-col gap-2">
                  <label className="text-xs font-medium" style={{ color: P.textMuted }}>{photo.label}</label>
                  <div 
                    className="relative rounded-xl overflow-hidden cursor-pointer transition-all hover:opacity-80"
                    style={{ 
                      background: photo.preview ? 'transparent' : P.bgPanel,
                      border: `2px dashed ${photo.preview ? P.accentSuccess : P.border}`,
                      aspectRatio: '4/3'
                    }}
                    onClick={() => document.getElementById(`file-${photo.id}`)?.click()}
                  >
                    {photo.preview ? (
                      <img src={photo.preview} alt={photo.label} className="w-full h-full object-cover" />
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full p-4">
                        <Upload size={24} style={{ color: P.textDim }} />
                        <span className="text-xs mt-2 text-center" style={{ color: P.textDim }}>Cliquer pour ajouter</span>
                      </div>
                    )}
                    <input 
                      id={`file-${photo.id}`}
                      type="file" 
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          handlePhotoUpload(photo.id, e.target.files[0]);
                        }
                      }}
                    />
                    {photo.preview && (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setPhotos(prev => prev.map(p => p.id === photo.id ? { ...p, file: null, preview: null } : p));
                        }}
                        className="absolute top-2 right-2 p-1 rounded-full"
                        style={{ background: P.accentError, color: 'white' }}
                      >
                        <X size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Plan de Traitement */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4" style={{ color: P.text }}>Plan de Traitement Proposé</h4>
            <div className="p-4 rounded-xl whitespace-pre-wrap font-mono text-sm leading-relaxed max-h-80 overflow-y-auto" style={{ background: P.bgPanel, color: P.text }}>
              {planTraitement || 'Complétez l\'étape 3 pour générer le plan de traitement.'}
            </div>
          </section>

          {/* Checklist avant export */}
          <section className="p-6 rounded-2xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <h4 className="text-lg font-bold mb-4" style={{ color: P.text }}>Vérification avant export</h4>
            <div className="space-y-2">
              {/* Éléments obligatoires */}
              {[
                { label: 'Radiographie avec tracé', ok: local.landmarks.length >= 10 },
                { label: 'Analyse céphalométrique complète', ok: etape3Data.osseuse.decalage_ab !== '' },
                { label: 'DDM calculée', ok: ddmReelleCalc !== 0 },
                { label: 'Plan de traitement', ok: planTraitement !== '' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-lg" style={{ background: P.bgPanel }}>
                  <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: item.ok ? P.accentSuccess : P.accentError }}>
                    {item.ok ? <CheckCircle2 size={12} color="white" /> : <AlertCircle size={12} color="white" />}
                  </div>
                  <span className="text-sm" style={{ color: P.text }}>{item.label}</span>
                </div>
              ))}
              {/* Éléments optionnels */}
              <div className="mt-4 pt-4" style={{ borderTop: `1px solid ${P.border}` }}>
                <span className="text-xs uppercase tracking-wide" style={{ color: P.textMuted }}>Optionnel</span>
              </div>
              {[
                { label: 'Photos uploadées (intra/extra/moulages)', ok: photos.some(p => p.preview !== null) },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-lg" style={{ background: P.bgPanel }}>
                  <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: item.ok ? P.accentSuccess : P.textDim }}>
                    {item.ok ? <CheckCircle2 size={12} color="white" /> : <span style={{ color: 'white', fontSize: '10px' }}>?</span>}
                  </div>
                  <span className="text-sm opacity-70" style={{ color: P.text }}>{item.label}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );

  // 
  // RENDU PRINCIPAL
  // 
  return (
    <div className="flex flex-col h-full" style={{ background: P.bg }}>
      {/* Modal Blocage Étape 2 */}
      <AnimatePresence>
        {showStep2Blocker && (
          <Step2BlockerModal
            type={showStep2Blocker}
            onClose={() => setShowStep2Blocker(null)}
            onStartCalibration={() => { setShowCalibration(true); setCalibrationClickPoints([]); setCalibrationDistance(''); setCalibrationStep('selecting'); }}
            P={P}
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: P.border, background: P.bgPanel }}>
        <div>
          <h2 className="text-lg font-bold" style={{ color: P.text }}>Studio Céphalométrique</h2>
          <p className="text-xs" style={{ color: P.textMuted }}>{patientName}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleSave} disabled={!analysisId || isSaving} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all disabled:opacity-50" style={{ background: P.bgCard, border: `1px solid ${P.border}`, color: P.text }}>
            {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Sauvegarder
          </button>
        </div>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2 px-6 py-4 overflow-x-auto" style={{ background: P.bg }}>
        <StepTab id={1} label="Céphalométrie" isActive={step === 1} isCompleted={completed.has(1)} onClick={() => goToStep(1)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={2} label="Moulages" isActive={step === 2} isCompleted={completed.has(2)} onClick={() => goToStep(2)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={3} label="Diagnostic" isActive={step === 3} isCompleted={completed.has(3)} onClick={() => goToStep(3)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={4} label="Export" isActive={step === 4} isCompleted={completed.has(4)} onClick={() => goToStep(4)} P={P} />
      </div>

      {/* Message d'erreur navigation */}
      <AnimatePresence>
        {stepError && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="px-6">
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg text-sm" style={{ background: `${P.accentError}15`, border: `1px solid ${P.accentError}40`, color: P.accentError }}>
              <AlertCircle size={16} />
              {stepError}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6" style={{ background: P.bg }}>
        <div className="max-w-4xl mx-auto">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
          
          {/* Bouton Suivant */}
          {step < 4 && (
            <div className="flex justify-end mt-8 pt-6 border-t" style={{ borderColor: P.border }}>
              <button
                onClick={() => goToStep((step + 1) as StepId)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all hover:opacity-90"
                style={{ background: P.accent, color: 'white' }}
              >
                {step === 1 && 'Passer aux moulages'}
                {step === 2 && 'Passer au diagnostic'}
                {step === 3 && 'Exporter le bilan'}
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CephaloWorkspace;
