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
  useState, useRef, useEffect,
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

import { 
  computeStep3Data,
  generateTreatmentPlan
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
  const store = useOrthoStore();
  const mode = store.mode;
  const P = PALETTE[mode];
  const [patientData, setPatientData] = useState<{ age: number; sexe: 'M' | 'F' } | null>(null);

  // Initialisation du Store Zustand & Sync Thème
  useEffect(() => {
    store.setPatientInfo(patientId, patientName);
    
    // Sync reactive avec le thème global
    const syncTheme = () => {
      const isDark = document.body.dataset.theme === 'dark' || document.body.dataset.theme === 'prestige';
      store.setMode(isDark ? 'dark' : 'light');
    };

    const observer = new MutationObserver(syncTheme);
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });
    
    syncTheme(); // Init immédiat
    return () => observer.disconnect();
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

  //  Modal blocage étape 2
  const [showStep2Blocker, setShowStep2Blocker] = useState<'calibration' | null>(null);

  //  Refs 
  const fileRef = useRef<HTMLInputElement>(null);
  const step1ContainerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const {
    analysisId, imageSrc,
    mmPerPixel,
    local, syncState, isSaving,
    previewPdfUrl, isPreviewLoading,
    setShowCalibration, setCalibrationClickPoints, setCalibrationDistance, setCalibrationStep,
    setImgDim,
    setPreviewPdfUrl, setIsPreviewLoading,
    handleSave,
    step, completedSteps, goToStep, uploadError,
    setEtape3Data
  } = store;

  //  AUTOMATISATION ÉTAPE 3 (Diagnostic Intelligent COM)
  useEffect(() => {
    if (!patientData) return;
    const automated = computeStep3Data(
      local.landmarks, 
      patientData.age, 
      patientData.sexe, 
      mmPerPixel, 
      store.etape2Data
    );
    
    setEtape3Data(prev => {
      const hasOsseuseChanged = JSON.stringify(automated.osseuse) !== JSON.stringify(prev.osseuse);
      const hasEsthetiqueChanged = JSON.stringify(automated.esthetique) !== JSON.stringify(prev.esthetique);
      const hasMoulageChanged = automated.analyse_moulages_auto !== prev.analyse_moulages_auto;
      
      if (!hasOsseuseChanged && !hasEsthetiqueChanged && !hasMoulageChanged && prev.age === patientData.age && prev.cvm === automated.cvm) {
        return prev;
      }

      // Sync intelligent pour le diagnostic textuel
      const currentMoulageDiag = store.diag.analyse_moulages;
      const isPlaceholder = !currentMoulageDiag || 
                           currentMoulageDiag === "Occlusion à préciser (Classe d'Angle, Subdivision, Forme d'arcade)." ||
                           currentMoulageDiag.trim() === "";

      if (isPlaceholder && automated.analyse_moulages_auto) {
        store.setDiag(d => ({ ...d, analyse_moulages: automated.analyse_moulages_auto || "" }));
      }

      // Auto-fill stratégie thérapeutique si vide
      if (!store.diag.strategie_therapeutique || store.diag.strategie_therapeutique.trim() === "") {
        const plan = generateTreatmentPlan(automated as any);
        if (plan) {
          store.setDiag(d => ({ ...d, strategie_therapeutique: plan }));
        }
      }
      
      return {
        ...prev,
        ...automated,
        osseuse: { ...prev.osseuse, ...automated.osseuse },
        esthetique: { ...prev.esthetique, ...automated.esthetique },
      };
    });
  }, [local.landmarks, patientData, mmPerPixel, store.etape2Data, store.etape3Data.selectedAnalysis, store.diag.analyse_moulages]);

  

  const [stepError, setStepError] = useState<string | null>(null);

  // Sync internal step errors with store upload error
  useEffect(() => {
    if (uploadError) {
      setStepError(uploadError);
      const timer = setTimeout(() => setStepError(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [uploadError]);

  // Reset scroll on step change
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [step]);

  //  Effects
  useEffect(() => {
    if (!store.isStep1Fullscreen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') store.setIsStep1Fullscreen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [store.isStep1Fullscreen]);

  useEffect(() => {
    if (store.isStep1Fullscreen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = originalOverflow; };
    }
  }, [store.isStep1Fullscreen]);

  useEffect(() => {
    if (!imageSrc) return;
    const img = new Image();
    img.onload = () => setImgDim({ w: img.naturalWidth, h: img.naturalHeight });
    img.src = imageSrc;
  }, [imageSrc, setImgDim]);

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
        <StepTab id={1} label="Céphalométrie" isActive={step === 1} isCompleted={completedSteps.has(1)} onClick={() => goToStep(1)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={2} label="Moulages" isActive={step === 2} isCompleted={completedSteps.has(2)} onClick={() => goToStep(2)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={3} label="Diagnostic" isActive={step === 3} isCompleted={completedSteps.has(3)} onClick={() => goToStep(3)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={4} label="Ghost Brain & Plan" isActive={step === 4} isCompleted={completedSteps.has(4)} onClick={() => goToStep(4)} P={P} />
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
      <div ref={scrollContainerRef} className="flex-1 overflow-auto p-6 scroll-smooth" style={{ background: P.bg }}>
        <div className="max-w-4xl mx-auto">
          {step === 1 && renderStep1()}
          {step === 2 && (
            <Step2Occlusal P={P} />
          )}
          {step === 3 && (
            <Step3Clinical P={P} />
          )}
          {step === 4 && (
            <Step4Documents P={P} />
          )}

          {/* Navigation des étapes */}
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
                {step === 3 && 'Discuter du plan (Ghost Brain)'}
                <ChevronRight size={18} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CephaloWorkspace;
