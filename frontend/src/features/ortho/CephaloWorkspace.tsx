/**
 * CephaloWorkspace.tsx  *  v4.2  *  Digital Crown - Studio COM
 *
 * Composant central du workflow d'analyse céphalométrique en 4 étapes.
 * Les données démographiques Patient sont requises : aucune valeur clinique n'est inventée
 * pour permettre aux calculs de continuer, et aucune stratégie thérapeutique n'est auto-écrite.
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
import { CephaloHistory } from './CephaloHistory';
import { useOrthoStore } from './stores/useOrthoStore';
import { cephaloRepository } from './cephaloRepository';
import { API_BASE, api } from '../../services/api';
import toast from 'react-hot-toast';

export interface CephaloWorkspaceProps {
  patientId: number;
  patientName: string;
}

export const CephaloWorkspace: React.FC<CephaloWorkspaceProps> = ({
  patientId,
  patientName,
}) => {
  const store = useOrthoStore();
  const mode = store.mode;
  const P = PALETTE[mode];
  const [patientData, setPatientData] = useState<{ age: number; sexe: 'M' | 'F' } | null>(null);
  const [patientDataError, setPatientDataError] = useState(false);
  const [viewMode, setViewMode] = useState<'studio' | 'history'>('studio');

  const resolveImageSrc = (imagePath?: string) => {
    if (!imagePath) return undefined;
    if (/^https?:\/\//i.test(imagePath)) return imagePath;
    return `${API_BASE.replace(/\/$/, '')}/${imagePath.replace(/^\//, '')}`;
  };

  const handleSelectHistory = async (analysis: any) => {
    try {
      const loaded = await cephaloRepository.getAnalysis(analysis.id);
      const landmarks = loaded.landmarks_data || [];
      const anglesData = loaded.angles_data || {};

      store.setAnalysisId(loaded.id);
      store.setImageSrc(resolveImageSrc(loaded.image_original_path));
      store.setLocal({ landmarks, version: Date.now() });
      store.setAnglesData(anglesData);
      store.setVisionMetadata(anglesData.vision_metadata || {});
      store.setIsCalibrated(Boolean(loaded.is_calibrated));
      store.setMmPerPixel(typeof loaded.mm_per_pixel === 'number' ? loaded.mm_per_pixel : null);
      store.setCompletedSteps(new Set(landmarks.length ? [1] : []));

      const narrative = anglesData.ai_narrative || loaded.ai_diagnostic;
      if (narrative) {
        store.setDiag(prev => ({
          ...prev,
          diagnostic_squelettique: narrative.diagnostic_squelettique || prev.diagnostic_squelettique,
          analyse_moulages: narrative.analyse_moulages || prev.analyse_moulages,
          synthese_diagnostique: narrative.synthese_diagnostique || prev.synthese_diagnostique,
          strategie_therapeutique: narrative.strategie_therapeutique || prev.strategie_therapeutique,
        }));
      }

      store.setStep(1);
      setViewMode('studio');
      toast.success('Analyse céphalométrique chargée.');
    } catch (error) {
      console.error('Erreur chargement analyse céphalométrique:', error);
      toast.error("Impossible d'ouvrir cette analyse céphalométrique.");
    }
  };

  const handleDeleteHistory = (analysisId: number) => {
    if (store.analysisId === analysisId) {
      store.setAnalysisId(undefined as any);
    }
  };

  useEffect(() => {
    store.setPatientInfo(patientId, patientName);

    const syncTheme = () => {
      const isDark = document.body.dataset.theme === 'dark' || document.body.dataset.theme === 'prestige';
      store.setMode(isDark ? 'dark' : 'light');
    };

    const observer = new MutationObserver(syncTheme);
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });

    syncTheme();
    return () => observer.disconnect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId, patientName]);

  useEffect(() => {
    let cancelled = false;
    const fetchPatient = async () => {
      setPatientDataError(false);
      setPatientData(null);
      try {
        const { data } = await api.get(`/patients/${patientId}`);
        if (cancelled) return;

        let age: number | null = typeof data?.age === 'number' ? data.age : null;
        if (age === null && data?.date_naissance) {
          const birth = new Date(data.date_naissance);
          if (!Number.isNaN(birth.getTime())) {
            const now = new Date();
            age = now.getFullYear() - birth.getFullYear();
            if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) age--;
          }
        }

        const sexe = data?.sexe === 'M' || data?.sexe === 'F' ? data.sexe : null;
        if (age === null || age < 0 || age > 130 || !sexe) {
          setPatientDataError(true);
          return;
        }
        setPatientData({ age, sexe });
      } catch (error) {
        if (cancelled) return;
        console.error('Erreur patient data:', error);
        setPatientDataError(true);
      }
    };
    void fetchPatient();
    return () => { cancelled = true; };
  }, [patientId]);

  const [showStep2Blocker, setShowStep2Blocker] = useState<'calibration' | null>(null);
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

      const currentMoulageDiag = store.diag.analyse_moulages;
      const isPlaceholder = !currentMoulageDiag ||
                           currentMoulageDiag === "Occlusion à préciser (Classe d'Angle, Subdivision, Forme d'arcade)." ||
                           currentMoulageDiag.trim() === "";

      if (isPlaceholder && automated.analyse_moulages_auto) {
        store.setDiag(d => ({ ...d, analyse_moulages: automated.analyse_moulages_auto || "" }));
      }

      return {
        ...prev,
        ...automated,
        osseuse: { ...prev.osseuse, ...automated.osseuse },
        esthetique: { ...prev.esthetique, ...automated.esthetique },
      };
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [local.landmarks, patientData, mmPerPixel, store.etape2Data, store.etape3Data.selectedAnalysis, store.diag.analyse_moulages]);

  const [stepError, setStepError] = useState<string | null>(null);

  useEffect(() => {
    if (uploadError) {
      setStepError(uploadError);
      const timer = setTimeout(() => setStepError(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [uploadError]);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [step]);

  useEffect(() => {
    if (!store.isStep1Fullscreen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') store.setIsStep1Fullscreen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

    if (imageSrc.startsWith('blob:') || imageSrc.startsWith('data:')) {
      const img = new Image();
      img.onload = () => setImgDim({ w: img.naturalWidth, h: img.naturalHeight });
      img.src = imageSrc;
      return;
    }

    let cancelled = false;
    let createdBlobUrl: string | null = null;

    api.get(imageSrc, { responseType: 'blob' })
      .then(response => {
        if (cancelled) return;
        const blobUrl = URL.createObjectURL(response.data as Blob);
        createdBlobUrl = blobUrl;
        store.setImageSrc(blobUrl);
        createdBlobUrl = null;
      })
      .catch(() => {
        if (cancelled) return;
        const img = new Image();
        img.onload = () => { if (!cancelled) setImgDim({ w: img.naturalWidth, h: img.naturalHeight }); };
        img.src = imageSrc;
      });

    return () => {
      cancelled = true;
      if (createdBlobUrl) URL.revokeObjectURL(createdBlobUrl);
    };
  }, [imageSrc, setImgDim]); // eslint-disable-line react-hooks/exhaustive-deps

  const renderStep1 = () => (
    <Step1Cephalo
      P={P}
      fileRef={fileRef}
      step1ContainerRef={step1ContainerRef}
    />
  );

  if (patientDataError) {
    return (
      <div className="min-h-[420px] flex flex-col items-center justify-center gap-4 px-6 text-center" style={{ background: P.bg }}>
        <AlertCircle size={40} style={{ color: P.accentError }} />
        <div>
          <h3 className="text-lg font-black" style={{ color: P.text }}>Données Patient requises</h3>
          <p className="mt-2 max-w-lg text-sm" style={{ color: P.textMuted }}>
            La céphalométrie ne peut pas calculer avec un âge ou un sexe inventé. Vérifiez la date de naissance et le sexe du dossier Patient, puis rechargez cet espace.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" style={{ background: P.bg }}>
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

      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: P.border, background: P.bgPanel }}>
        <div>
          <h2 className="text-lg font-bold" style={{ color: P.text }}>Studio Céphalométrique</h2>
          <p className="text-xs" style={{ color: P.textMuted }}>{patientName}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex bg-black/5 rounded-lg p-1">
             <button onClick={() => setViewMode('studio')} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${viewMode === 'studio' ? 'bg-white shadow-sm' : 'opacity-50'}`} style={{ color: P.text }}>Actuel</button>
             <button onClick={() => setViewMode('history')} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${viewMode === 'history' ? 'bg-white shadow-sm' : 'opacity-50'}`} style={{ color: P.text }}>Historique</button>
          </div>
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

      <div data-tour="cephalo-stepper" className="flex items-center gap-2 px-6 py-4 overflow-x-auto" style={{ background: P.bg }}>
        <StepTab id={1} label="Céphalométrie" isActive={step === 1} isCompleted={completedSteps.has(1)} onClick={() => goToStep(1)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={2} label="Moulages" isActive={step === 2} isCompleted={completedSteps.has(2)} onClick={() => goToStep(2)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={3} label="Synthèse clinique" isActive={step === 3} isCompleted={completedSteps.has(3)} onClick={() => goToStep(3)} P={P} />
        <ChevronRight size={16} style={{ color: P.textDim, opacity: 0.5 }} />
        <StepTab id={4} label="Documents & stratégie" isActive={step === 4} isCompleted={completedSteps.has(4)} onClick={() => goToStep(4)} P={P} />
      </div>

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

      <div ref={scrollContainerRef} className="flex-1 overflow-auto p-6 scroll-smooth" style={{ background: P.bg }}>
        <div className="max-w-4xl mx-auto">
          {viewMode === 'studio' ? (
            <>
              {step === 1 && renderStep1()}
              {step === 2 && <Step2Occlusal P={P} />}
              {step === 3 && <Step3Clinical P={P} />}
              {step === 4 && <Step4Documents P={P} />}

              <div className={`flex mt-8 pt-6 border-t ${step > 1 ? 'justify-between' : 'justify-end'}`} style={{ borderColor: P.border }}>
                {step > 1 && (
                  <button onClick={() => goToStep((step - 1) as StepId)} className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all hover:opacity-80" style={{ border: `1px solid ${P.border}`, color: P.textMuted }}>
                    <ChevronLeft size={18} /> Précédent
                  </button>
                )}
                {step < 4 && (
                  <button onClick={() => goToStep((step + 1) as StepId)} className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all hover:opacity-90 shadow-lg" style={{ background: P.accent, color: 'white', boxShadow: `0 4px 12px ${P.accent}40` }}>
                    {step === 1 && 'Passer aux moulages'}
                    {step === 2 && 'Passer à la synthèse'}
                    {step === 3 && 'Préparer les documents et la stratégie'}
                    <ChevronRight size={18} />
                  </button>
                )}
              </div>
            </>
          ) : (
             <CephaloHistory patientId={patientId} onSelect={handleSelectHistory} onDelete={handleDeleteHistory} />
          )}
        </div>
      </div>
    </div>
  );
};

export default CephaloWorkspace;
