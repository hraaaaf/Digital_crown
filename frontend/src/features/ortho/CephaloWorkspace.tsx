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
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRight, ChevronLeft,
  Loader2, AlertCircle,
  Save
} from 'lucide-react';
import type { 
  StepId 
} from './cephaloShared';

import type { 
  DDMState, DiagnosticTexts,
  DonneesEtape3, DonneesEtape2, PhotoUpload, PatternVertical, ProfilFacial, SeveriteDDM
} from './cephaloTypes';

import { 
  calcDDMReelle, computeLocalImpa, computeStep3Data
} from './cephaloUtils';
import { PALETTE } from './cephaloTheme';

import { Step1Cephalo } from './components/Step1Cephalo';
import { Step2Occlusal } from './components/Step2Occlusal';
import { Step3Clinical } from './components/Step3Clinical';
import { Step4Documents } from './components/Step4Documents';
import { LivePreview } from '../admin/DocumentStudio/LivePreview';
import { StepTab } from './components/StepTab';
import { SyncBadge } from './components/SyncBadge';
import { Step2BlockerModal } from './components/Step2BlockerModal';
import { useOrthoStore } from './stores/useOrthoStore';


export interface CephaloWorkspaceProps {
  patientId:   number;
  patientName: string;
}

// StepTab, SyncBadge imported from ./components/




// StepTab, SyncBadge imported from ./components/

// Step2BlockerModal imported from ./components/Step2BlockerModal

// 
// COMPOSANT PRINCIPAL
// 
export const CephaloWorkspace: React.FC<CephaloWorkspaceProps> = ({
  patientId,
  patientName,
}) => {
  //  ÉTAT LOCAL - Navigation et UI
  const store = useOrthoStore();
  const mode = store.mode;
  const P = PALETTE[mode];
  const [step, setStep] = useState<StepId>(1);
  const [completed, setCompleted] = useState<Set<number>>(new Set());
  const [isStep1Fullscreen, setIsStep1Fullscreen] = useState(false);
  const [patientData, setPatientData] = useState<{ age: number; sexe: 'M' | 'F' } | null>(null);

  // Initialisation du Store Zustand
  useEffect(() => {
    store.setPatientInfo(patientId, patientName);
  }, [patientId, patientName]);

  // Initialisation Patient
  useEffect(() => {
    const fetchPatient = async () => {
      try {
        const { data } = await import('../../services/api').then(m => m.api.get(`/patients/${patientId}`));
        if (data) {
          let age = data.age;
          if (!age && data.date_naissance) {
            const birth = new Date(data.date_naissance);
            const now = new Date();
            age = now.getFullYear() - birth.getFullYear();
            if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) age--;
          }
          setPatientData({ age: age || 20, sexe: data.sexe || 'M' });
        }
      } catch (e) {
        console.error('Erreur patient data:', e);
        setPatientData({ age: 20, sexe: 'M' });
      }
    };
    fetchPatient();
  }, [patientId]);

  // DDM & Diagnostic State (Source de vérité)
  const [ddm, setDdm] = useState<DDMState>({ maxillaire: '', mandibulaire: '' });
  const [diag, setDiag] = useState<DiagnosticTexts>({
    diagnostic_squelettique: '',
    analyse_moulages: '',
    synthese_diagnostique: '',
    strategie_therapeutique: '',
  });



  //  ÉTAPE 4 - Données Photos
  const [photos, setPhotos] = useState<PhotoUpload[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_photos_${patientId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
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

  //  ÉTAPE 3 - Données Protocole COM
  const [etape3Data, setEtape3Data] = useState<DonneesEtape3>(() => {
    const initialState: DonneesEtape3 = {
      age: '', cvm: '', date_teles: new Date().toISOString().split('T')[0],
      dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
      osseuse: { angle_tweed: '', decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: '' },
      esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
      ddm_clinique: '', ddm_cephalo: '', division: null, type_arcade: null, classe_squelettique: '',
      pattern_vertical: '', profil: '', severite_ddm: '', subdivision: false, denture_type: 'PERMANENTE', preference_technique: 'DAMON',
    };
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape3_${patientId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          return { ...initialState, ...parsed, dentaire: { ...initialState.dentaire, ...(parsed.dentaire || {}) }, osseuse: { ...initialState.osseuse, ...(parsed.osseuse || {}) }, esthetique: { ...initialState.esthetique, ...(parsed.esthetique || {}) } };
        } catch (e) { console.error('Erreur chargement étape 3:', e); }
      }
    }
    return initialState;
  });

  //  ÉTAPE 2 - Examen Occlusal
  const [etape2Data, setEtape2Data] = useState<DonneesEtape2>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`digitalcrown_etape2_${patientId}`);
      if (saved) {
        try { return JSON.parse(saved); } catch (e) {}
      }
    }
    return { occlusal: { molaire_gauche: 'I', molaire_droite: 'I', canine_gauche: 'I', canine_droite: 'I' } };
  });

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 4 (photos et métadonnées)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const photosToSave = photos.reduce((acc, p) => { acc[p.id] = p.preview; return acc; }, {} as Record<string, string | null>);
      localStorage.setItem(`digitalcrown_photos_${patientId}`, JSON.stringify(photosToSave));
      localStorage.setItem(`digitalcrown_etape4_${patientId}`, JSON.stringify({ dateConsultation, sexePatient }));
    }
  }, [photos, dateConsultation, sexePatient, patientId]);

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 2
  useEffect(() => { if (typeof window !== 'undefined') localStorage.setItem(`digitalcrown_etape2_${patientId}`, JSON.stringify(etape2Data)); }, [etape2Data, patientId]);

  //  SAUVEGARDE AUTOMATIQUE ÉTAPE 3
  useEffect(() => { if (typeof window !== 'undefined') localStorage.setItem(`digitalcrown_etape3_${patientId}`, JSON.stringify(etape3Data)); }, [etape3Data, patientId]);

  //  Modal blocage étape 2
  const [showStep2Blocker, setShowStep2Blocker] = useState<'calibration' | null>(null);

  //  Refs 
  const fileRef = useRef<HTMLInputElement>(null);
  const step1ContainerRef = useRef<HTMLDivElement>(null);

  // 
  // HOOK DE PERSISTENCE & SYNC
  // 
  const {
    analysisId, imageSrc, anglesData,
    isCalibrated, mmPerPixel,
    local, syncState, isSaving, isPrinting,
    previewPdfUrl, isPreviewLoading,
    setShowCalibration, setCalibrationClickPoints, setCalibrationDistance, setCalibrationStep,
    setImgDim,
    setPreviewPdfUrl, setIsPreviewLoading,
    handleSave, silentSave, handlePreview, handlePrint
  } = store;

  //  AUTOMATISATION ÉTAPE 3 (Diagnostic Intelligent COM)
  useEffect(() => {
    if (!patientData) return;
    
    const automated = computeStep3Data(local.landmarks, patientData.age, patientData.sexe, mmPerPixel);
    
    setEtape3Data(prev => {
      const hasOsseuseChanged = JSON.stringify(automated.osseuse) !== JSON.stringify(prev.osseuse);
      const hasEsthetiqueChanged = JSON.stringify(automated.esthetique) !== JSON.stringify(prev.esthetique);
      const hasBasicsChanged = automated.cvm !== prev.cvm || automated.denture_type !== prev.denture_type;
      
      if (!hasOsseuseChanged && !hasEsthetiqueChanged && !hasBasicsChanged && prev.age === patientData.age) {
        return prev;
      }
      
      return {
        ...prev,
        age: patientData.age,
        cvm: automated.cvm || prev.cvm,
        denture_type: automated.denture_type || prev.denture_type,
        osseuse: { ...prev.osseuse, ...automated.osseuse },
        esthetique: { ...prev.esthetique, ...automated.esthetique },
        classe_squelettique: automated.classe_squelettique || prev.classe_squelettique,
        pattern_vertical: automated.pattern_vertical || prev.pattern_vertical,
        profil: automated.profil || prev.profil,
      };
    });
  }, [local.landmarks, patientData, mmPerPixel]);

  // 
  // COMPUTED
  // 
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

  const ddmMaxReelle = useMemo(() => calcDDMReelle(ddm.maxillaire, iFrancfortActuel, 107), [ddm.maxillaire, iFrancfortActuel]);
  const ddmMandReelle = useMemo(() => calcDDMReelle(ddm.mandibulaire, impaActuel, 90), [ddm.mandibulaire, impaActuel]);
  const ddmReelleTotale = useMemo(() => {
    if (ddmMaxReelle === null || ddmMandReelle === null) return null;
    return ddmMaxReelle + ddmMandReelle;
  }, [ddmMaxReelle, ddmMandReelle]);

  const hasSubdivision = useMemo(() => {
    const { molaire_gauche, molaire_droite, canine_gauche, canine_droite } = etape2Data.occlusal;
    return molaire_gauche !== molaire_droite || canine_gauche !== canine_droite;
  }, [etape2Data.occlusal]);

  const classeSquelettique = useMemo(() => {
    const anb = etape3Data.osseuse.decalage_ab === '' ? null : Number(etape3Data.osseuse.decalage_ab);
    if (anb === null) return '';
    if (anb < 0) return 'Classe III';
    if (anb >= 0 && anb <= 4) return 'Classe I';
    if (anb > 4 && anb <= 8) return 'Classe II modérée';
    if (anb > 8) return 'Classe II sévère';
    return '';
  }, [etape3Data.osseuse.decalage_ab]);

  const patternVertical = useMemo((): PatternVertical | '' => {
    const fma = etape3Data.osseuse.angle_tweed === '' ? null : Number(etape3Data.osseuse.angle_tweed);
    if (fma === null) return '';
    if (fma < 20) return 'hypodivergent';
    if (fma >= 20 && fma <= 30) return 'normodivergent';
    if (fma > 30) return 'hyperdivergent';
    return '';
  }, [etape3Data.osseuse.angle_tweed]);

  const severiteDDM = useMemo((): SeveriteDDM | 'excès' | '' => {
    const val = ddmReelleTotale; 
    if (val === null || val === 0) return '';
    if (val > 0) return 'excès'; 
    if (val >= -3) return 'léger';      
    if (val >= -6) return 'modéré';     
    return 'sévère';                    
  }, [ddmReelleTotale]);

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
    }
    await silentSave();
    setCompleted(prev => new Set([...prev, step]));
    setStep(target);
  }, [silentSave, step, imageSrc, isCalibrated, setCompleted, setStep]);



  const handlePhotoUpload = useCallback((id: string, file: File) => {
    const url = URL.createObjectURL(file);
    setPhotos(prev => prev.map(p => p.id === id ? { ...p, file, preview: url } : p));
  }, [setPhotos]);

  
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
  }, [imageSrc, setImgDim]);

  useEffect(() => {
    if (step !== 1 && isStep1Fullscreen) setIsStep1Fullscreen(false);
  }, [step, isStep1Fullscreen]);

  // 
  // RENDU ÉTAPE 1 - CÉPHALOMÉTRIE
  // 
  const renderStep1 = () => (
    <Step1Cephalo
      P={P}
      fileRef={fileRef}
      step1ContainerRef={step1ContainerRef}
    />
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

      {/* Modal Aperçu PDF */}
      <AnimatePresence>
        {(previewPdfUrl || isPreviewLoading) && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-4 z-50 rounded-[3rem] overflow-hidden shadow-2xl ring-1 ring-black/5"
          >
            <LivePreview 
              pdfUrl={previewPdfUrl} 
              loading={isPreviewLoading} 
              onClose={() => {
                if (previewPdfUrl) URL.revokeObjectURL(previewPdfUrl);
                setPreviewPdfUrl(null);
                setIsPreviewLoading(false);
              }} 
              title="Aperçu du Bilan Orthodontique" 
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: P.border, background: P.bgPanel }}>
        <div>
          <h2 className="text-lg font-bold" style={{ color: P.text }}>Studio Céphalométrique</h2>
          <p className="text-xs" style={{ color: P.textMuted }}>{patientName}</p>
        </div>
        <div className="flex items-center gap-4">
          <SyncBadge state={syncState} P={P} />
          <button 
            onClick={handleSave} 
            disabled={!analysisId || isSaving} 
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50 shadow-sm hover:shadow-md" 
            style={{ background: P.bgCard, border: `1px solid ${P.border}`, color: P.text }}
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Sauvegarder
          </button>
        </div>
      </div>

      {/* Stepper */}
      <div data-tour="cephalo-stepper" className="flex items-center gap-2 px-6 py-4 overflow-x-auto" style={{ background: P.bg }}>
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
              diag={diag}
              onDiagChange={setDiag}
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
              onPreviewPDF={handlePreview}
              isGenerating={isPrinting} 
              P={P} 
            />
          )}
          
          {/* Navigation des étapes */}
          {(step < 4 || step > 1) && (
            <div className={`flex mt-8 pt-6 border-t ${step > 1 ? 'justify-between' : 'justify-end'}`} style={{ borderColor: P.border }}>
              {step > 1 && (
                <button
                  onClick={() => goToStep((step - 1) as StepId)}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all hover:opacity-80"
                  style={{ border: `1px solid ${P.border}`, color: P.textMuted }}
                >
                  <ChevronLeft size={18} />
                  Précédent
                </button>
              )}
              
              {step < 4 && (
                <button
                  onClick={() => goToStep((step + 1) as StepId)}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all hover:opacity-90 shadow-lg"
                  style={{ background: P.accent, color: 'white', boxShadow: `0 4px 12px ${P.accent}40` }}
                >
                  {step === 1 && 'Passer aux moulages'}
                  {step === 2 && 'Passer au diagnostic'}
                  {step === 3 && 'Exporter le bilan'}
                  <ChevronRight size={18} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CephaloWorkspace;
