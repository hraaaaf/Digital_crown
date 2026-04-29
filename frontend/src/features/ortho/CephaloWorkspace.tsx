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
  Target, Save,
  Sun, Moon, ZoomIn, ZoomOut,
  Activity, RefreshCw,
  Maximize2, Minimize2, Ruler,
} from 'lucide-react';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import type { 
  Landmark, UIMode, StepId, SyncState, ImageFilters, VTOSettings 
} from './cephaloShared';

import type { 
  DDMState, DiagnosticTexts, LocalState, 
  DonneesEtape3, DonneesEtape2, PhotoUpload, PatternVertical, ProfilFacial, SeveriteDDM
} from './cephaloTypes';

import { 
  calcDDMReelle, calcDDMCephalo, estimateCVM, computeLocalImpa, 
  computeMcNamaraProjections, initializeDefaultApexes 
} from './cephaloUtils';

import { cephaloRepository } from './cephaloRepository';

import { Step2Occlusal } from './components/Step2Occlusal';
import { Step3Clinical } from './components/Step3Clinical';
import { Step4Documents } from './components/Step4Documents';


export interface CephaloWorkspaceProps {
  patientId:   number;
  patientName: string;
}

// 
// HELPERS
// 
const buildPayload = (
  lms: Landmark[], 
  max: number | null, 
  mand: number | null, 
  real: number | null, 
  diag: DiagnosticTexts, 
  projections: Record<string, any>,
  ratio: number | null = null
) => ({
  landmarks: lms,
  mm_per_pixel: ratio,
  clinical_data: {
    ddm_maxillaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: max ?? 0 },
    ddm_mandibulaire: { espace_disponible: 0, espace_necessaire: 0, calcul_ddm: mand ?? 0 },
    ddm_reelle: real ?? 0,
    plan_traitement: diag.plan_therapeutique || '',
  },
  ai_diagnostic: {
    squelettique: diag.squelettique,
    dentaire: diag.compensations_dentaires,
    traitement: diag.plan_therapeutique
  },
  mcnmara_projections: projections
});
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
  const [magnifierEnabled, setMagnifierEnabled] = useState(false);
  const [autoCalibMessage, setAutoCalibMessage] = useState<string | null>(null);
  
  // DDM & Diagnostic State (Source de vérité)
  const [ddm, setDdm] = useState<DDMState>({ maxillaire: '', mandibulaire: '' });
  const [diag, setDiag] = useState<DiagnosticTexts>({
    squelettique: '',
    compensations_dentaires: '',
    plan_therapeutique: '',
  });

  //  VTO & Simulation State
  const [vtoSettings, setVtoSettings] = useState<VTOSettings>({
    enabled: false,
    showGhostFace: true,
    showSoftTissue: true,
    u1_offset: { x: 0, y: 0 },
    l1_offset: { x: 0, y: 0 },
    mand_offset: { x: 0, y: 0 }
  });


  // Mode Performance (pour PC modestes)
  const performanceMode = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('performance_mode') === 'true';
  }, []);

  //  ÉTAPE 4 - Photos et Documents
  // PhotoUpload est importé de cephaloTypes.ts
  
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
  
  const [dateConsultation, _setDateConsultation] = useState<string>(() => {
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
  
  const [sexePatient, _setSexePatient] = useState<'M' | 'F'>(() => {
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
      esthetique: {
        ligne_e_ls: '',
        ligne_e_li: '',
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
    const esthetique = anglesData.metrics.analyse_esthetique || {};
    
    setEtape3Data(prev => ({
      ...prev,
      dentaire: {
        surplomb: dentaire.Surplomb?.valeur ?? prev.dentaire.surplomb,
        recouvrement: dentaire.Recouvrement?.valeur ?? prev.dentaire.recouvrement,
        impa: dentaire.IMPA?.valeur ?? prev.dentaire.impa,
        i_francfort: dentaire.I_Francfort?.valeur ?? prev.dentaire.i_francfort,
        inter_incisif: dentaire.Inter_Incisif?.valeur ?? prev.dentaire.inter_incisif,
      },
      osseuse: {
        angle_tweed: osseuse.Angle_de_Tweed?.valeur ?? prev.osseuse.angle_tweed,
        decalage_ab: osseuse.Decalage_A_B?.valeur ?? prev.osseuse.decalage_ab,
        situation_a: osseuse.Situation_A?.valeur ?? prev.osseuse.situation_a,
        situation_b: osseuse.Situation_B?.valeur ?? prev.osseuse.situation_b,
        profondeur_faciale: osseuse.Profondeur_Faciale?.valeur ?? prev.osseuse.profondeur_faciale,
      },
      esthetique: {
        ligne_e_ls: esthetique.Ligne_E_Ls?.valeur ?? prev.esthetique.ligne_e_ls,
        ligne_e_li: esthetique.Ligne_E_Li?.valeur ?? prev.esthetique.ligne_e_li,
      },
    }));
  }, [anglesData]);

  // Déclencher le pré-remplissage auto quand les données IA arrivent
  useEffect(() => {
    autoFillAnalyses();
  }, [autoFillAnalyses]);

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

  // Debug/Usage future pour profilFacial
  void profilFacial;

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

  // On affiche le plan de traitement (calculé pour usage dans les logs/debug si besoin)
  useEffect(() => {
    if (planTraitement) console.log("[Analyse] Plan suggéré généré");
  }, [planTraitement]);

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
  const iFrancfortActuel = etape3Data.dentaire.i_francfort === '' ? 107 : Number(etape3Data.dentaire.i_francfort);

  const ddmMaxClinique = ddm.maxillaire === '' ? null : Number(ddm.maxillaire);
  const ddmMandClinique = ddm.mandibulaire === '' ? null : Number(ddm.mandibulaire);

  const ddmMaxReelle = useMemo(() => calcDDMReelle(ddm.maxillaire, iFrancfortActuel, 107), [ddm.maxillaire, iFrancfortActuel]);
  const ddmMandReelle = useMemo(() => calcDDMReelle(ddm.mandibulaire, impaActuel, 90), [ddm.mandibulaire, impaActuel]);
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
      await cephaloRepository.saveAnalysis(aid, buildPayload(l.landmarks, max, mand, real, g, projections));
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
        await cephaloRepository.saveAnalysis(analysisId, buildPayload(newLms, max, mand, real, g, projections, mmPerPixel));
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
      const data = await cephaloRepository.uploadRadio(patientId, file);
      if (data.analysis_id) setAnalysisId(data.analysis_id);
      if (data.file_url) setImageSrc(data.file_url);
      if (data.results) setAnglesData(data.results);
      if (data.results?.vision_metadata) setVisionMetadata(data.results.vision_metadata);
      if (data.is_calibrated !== undefined) {
        setIsCalibrated(data.is_calibrated);
        setMmPerPixel(data.mm_per_pixel || null);
        if (data.is_calibrated && data.mm_per_pixel) {
          setAutoCalibMessage(`Auto-calibration réussie : ${data.mm_per_pixel.toFixed(4)} mm/px`);
          setTimeout(() => setAutoCalibMessage(null), 8000);
        }
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
      await cephaloRepository.calibrate(analysisId, p1, p2, distMm);
      setMmPerPixel(ratio);
      setIsCalibrated(true);
      setShowCalibration(false);
      setCalibrationClickPoints([]);
      setCalibrationDistance('');
      setCalibrationStep('selecting');
      const updatedData = await cephaloRepository.saveAnalysis(analysisId, {
        landmarks: local.landmarks,
        mm_per_pixel: ratio
      });
      if (updatedData.results) setAnglesData(updatedData.results);
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
      await cephaloRepository.saveAnalysis(analysisId, buildPayload(local.landmarks, ddmMaxClinique, ddmMandClinique, ddmReelleTotale, diag, projections, mmPerPixel));
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
    try {
      const data = await cephaloRepository.getAIDiagnostic(patientId);
      setDiag({
        squelettique: data.diagnostic_squelettique || data.squelettique || data.skeletal || '',
        compensations_dentaires: data.analyse_dentaire || data.dentaire || data.dental || '',
        plan_therapeutique: data.strategie_therapeutique || data.traitement || data.recommendations || '',
      });
    } catch (e) {
      console.error('[SLM] Génération échouée:', e);
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
      const data = await cephaloRepository.generatePDF(patientId, {
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
      });
      const blob = new Blob([data], { type: 'application/pdf' });
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

          <div className="w-px h-4 opacity-20" style={{ background: P.border }} />

          {/* Contrôles Esthétiques & Simulation */}
          <div className="flex items-center gap-2">
             <button 
                onClick={() => setVtoSettings(v => ({ ...v, showSoftTissue: !v.showSoftTissue }))}
                className="px-2 py-1.5 rounded-lg text-[10px] font-bold transition-all"
                style={{ 
                  background: vtoSettings.showSoftTissue ? `${P.accentSuccess}15` : 'transparent', 
                  border: `1px solid ${vtoSettings.showSoftTissue ? P.accentSuccess : P.border}`,
                  color: vtoSettings.showSoftTissue ? P.accentSuccess : P.textDim 
                }}
             >
                PROFIL
             </button>
             <button 
                onClick={() => setVtoSettings(v => ({ ...v, showGhostFace: !v.showGhostFace }))}
                className="px-2 py-1.5 rounded-lg text-[10px] font-bold transition-all"
                style={{ 
                  background: vtoSettings.showGhostFace ? `${P.accent}15` : 'transparent', 
                  border: `1px solid ${vtoSettings.showGhostFace ? P.accent : P.border}`,
                  color: vtoSettings.showGhostFace ? P.accent : P.textDim 
                }}
             >
                FACE 3D
             </button>
             <button 
                onClick={() => setVtoSettings(v => ({ ...v, enabled: !v.enabled }))}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
                style={{ 
                  background: vtoSettings.enabled ? `${P.accentWarning}20` : 'transparent', 
                  border: `1px solid ${vtoSettings.enabled ? P.accentWarning : P.border}`,
                  color: vtoSettings.enabled ? P.accentWarning : P.textDim 
                }}
             >
                <Activity size={14} />
                SIMULATION VTO
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
        
        {/* Alerte Auto-Calibration */}
        <AnimatePresence>
          {autoCalibMessage && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex flex-col gap-2 px-4 py-3 rounded-xl shadow-lg" style={{ background: `${P.accentSuccess}25`, border: `2px solid ${P.accentSuccess}` }}>
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} style={{ color: P.accentSuccess }} />
                <span className="text-sm font-bold" style={{ color: P.accentSuccess }}>{autoCalibMessage}</span>
              </div>
              <div className="text-[11px] font-mono" style={{ color: P.textMuted }}>
                Précision millimétrique certifiée par vision artificielle.
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
            performanceMode={performanceMode}
            vto={vtoSettings}
          />

          {/* Panneau Simulation VTO Elite (Flottant) */}
          <AnimatePresence>
            {vtoSettings.enabled && (
              <motion.div
                initial={{ opacity: 0, x: 30, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 30, scale: 0.95 }}
                className="absolute top-24 right-8 w-72 p-5 rounded-3xl shadow-2xl z-40 overflow-hidden"
                style={{ 
                  background: `${P.bgPanel}CC`, // Transparence vitreuse
                  border: `1px solid ${P.accent}40`,
                  backdropFilter: 'blur(20px)',
                  boxShadow: `0 20px 50px -12px rgba(0,0,0,0.5), 0 0 20px ${P.accent}20`
                }}
              >
                {/* Effet de lueur en arrière-plan du panel */}
                <div className="absolute -top-12 -right-12 w-24 h-24 rounded-full blur-[40px] opacity-20" style={{ background: P.accent }} />

                <div className="relative flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: `${P.accentWarning}20`, border: `1px solid ${P.accentWarning}40` }}>
                      <Activity size={16} style={{ color: P.accentWarning }} />
                    </div>
                    <div>
                      <span className="block text-sm font-black tracking-tight" style={{ color: P.text }}>STUDIO VTO</span>
                      <span className="block text-[10px] font-mono opacity-50" style={{ color: P.textMuted }}>PROACTIVE ENGINE v1.2</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button 
                      onClick={() => {
                        // Animation de séquence 0 -> Valeur actuelle
                        const targetU1 = vtoSettings.u1_offset?.x || 0;
                        const targetL1 = vtoSettings.l1_offset?.x || 0;
                        const targetMand = vtoSettings.mand_offset?.x || 0;
                        
                        // Reset temporaire pour l'effet visuel
                        setVtoSettings(v => ({...v, u1_offset: {x:0,y:0}, l1_offset: {x:0,y:0}, mand_offset: {x:0,y:0}}));
                        
                        // Lancement différé pour laisser le spring réagir
                        setTimeout(() => {
                           setVtoSettings(v => ({...v, u1_offset: {x:targetU1,y:0}, l1_offset: {x:targetL1,y:0}, mand_offset: {x:targetMand,y:0}}));
                        }, 100);
                      }}
                      className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                      title="Lancer la séquence de traitement"
                    >
                      <Activity size={14} className="animate-pulse" style={{ color: P.accentSuccess }} />
                    </button>
                    <button onClick={() => setVtoSettings(v => ({...v, enabled: false}))} className="p-1 rounded-lg hover:bg-white/10 transition-colors">
                      <X size={14} style={{ color: P.textDim }} />
                    </button>
                  </div>
                </div>

                <div className="space-y-6">
                   {/* Maxillaire / U1 */}
                   <div className="space-y-2">
                      <div className="flex justify-between items-end">
                        <label className="text-[10px] font-black uppercase tracking-widest opacity-60" style={{ color: P.textMuted }}>Incisive Supérieure</label>
                        <span className="text-xs font-mono font-bold" style={{ color: P.accent }}>
                          {((vtoSettings.u1_offset?.x || 0) * (mmPerPixel || 0.1)).toFixed(1)} <span className="opacity-40">mm</span>
                        </span>
                      </div>
                      <div className="relative h-6 flex items-center">
                        <div className="absolute inset-0 h-1 my-auto rounded-full opacity-10" style={{ background: P.text }} />
                        <input 
                          type="range" min={-60} max={60} step={1}
                          value={vtoSettings.u1_offset?.x || 0} 
                          onChange={(e) => setVtoSettings(v => ({ ...v, u1_offset: { x: +e.target.value, y: v.u1_offset?.y || 0 }}))}
                          className="w-full h-1 cursor-pointer appearance-none bg-transparent" 
                          style={{ accentColor: P.accent }}
                        />
                      </div>
                   </div>

                   {/* Mandibule / L1 */}
                   <div className="space-y-2">
                      <div className="flex justify-between items-end">
                        <label className="text-[10px] font-black uppercase tracking-widest opacity-60" style={{ color: P.textMuted }}>Incisive Inférieure</label>
                        <span className="text-xs font-mono font-bold" style={{ color: P.accentSuccess }}>
                          {((vtoSettings.l1_offset?.x || 0) * (mmPerPixel || 0.1)).toFixed(1)} <span className="opacity-40">mm</span>
                        </span>
                      </div>
                      <div className="relative h-6 flex items-center">
                        <div className="absolute inset-0 h-1 my-auto rounded-full opacity-10" style={{ background: P.text }} />
                        <input 
                          type="range" min={-60} max={60} step={1}
                          value={vtoSettings.l1_offset?.x || 0} 
                          onChange={(e) => setVtoSettings(v => ({ ...v, l1_offset: { x: +e.target.value, y: v.l1_offset?.y || 0 }}))}
                          className="w-full h-1 cursor-pointer appearance-none bg-transparent" 
                          style={{ accentColor: P.accentSuccess }}
                        />
                      </div>
                   </div>

                   {/* Chin / Mandibule */}
                   <div className="space-y-2">
                      <div className="flex justify-between items-end">
                        <label className="text-[10px] font-black uppercase tracking-widest opacity-60" style={{ color: P.textMuted }}>Avancement Mandibulaire</label>
                        <span className="text-xs font-mono font-bold" style={{ color: P.accentWarning }}>
                          {((vtoSettings.mand_offset?.x || 0) * (mmPerPixel || 0.1)).toFixed(1)} <span className="opacity-40">mm</span>
                        </span>
                      </div>
                      <div className="relative h-6 flex items-center">
                        <div className="absolute inset-0 h-1 my-auto rounded-full opacity-10" style={{ background: P.text }} />
                        <input 
                          type="range" min={-100} max={100} step={1}
                          value={vtoSettings.mand_offset?.x || 0} 
                          onChange={(e) => setVtoSettings(v => ({ ...v, mand_offset: { x: +e.target.value, y: v.mand_offset?.y || 0 }}))}
                          className="w-full h-1 cursor-pointer appearance-none bg-transparent" 
                          style={{ accentColor: P.accentWarning }}
                        />
                      </div>
                   </div>

                   <div className="pt-6 border-t" style={{ borderColor: `${P.border}40` }}>
                      <button 
                        onClick={() => setVtoSettings(v => ({ ...v, u1_offset: {x:0,y:0}, l1_offset: {x:0,y:0}, mand_offset: {x:0,y:0}}))}
                        className="w-full py-3 rounded-xl text-[10px] font-black tracking-widest uppercase transition-all hover:scale-[1.02] active:scale-[0.98]"
                        style={{ background: `${P.accent}15`, border: `1px solid ${P.accent}40`, color: P.accent }}
                      >
                        Réinitialiser l'objectif
                      </button>
                   </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          
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
          {step === 2 && (
            <Step2Occlusal 
              data={etape2Data} 
              ddm={ddm}
              impa={impaActuel ?? 90}
              iFrancfort={iFrancfortActuel ?? 107}
              onDdmChange={setDdm}
              onChange={(newData) => setEtape2Data({ ...etape2Data, ...newData })} 
              P={P} 
            />
          )}
          {step === 3 && (
            <Step3Clinical 
              data={etape3Data} 
              onChange={(newData) => setEtape3Data({ ...etape3Data, ...newData })} 
              P={P} 
            />
          )}
          {step === 4 && (
            <Step4Documents 
              photos={photos} 
              patientName={patientName}
              sexe={sexePatient}
              onUpload={handlePhotoUpload} 
              onGeneratePDF={handlePrint} 
              isGenerating={isPrinting} 
              P={P} 
            />
          )}
          
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
