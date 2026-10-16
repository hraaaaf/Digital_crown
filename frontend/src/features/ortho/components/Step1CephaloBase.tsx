import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { CEPHALO_ACCEPTED_IMAGE_TYPES, isSupportedCephaloImageFile } from '../cephaloImageUploadPolicy';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Loader2, AlertCircle, Sun, Target, RefreshCw, Maximize2, Minimize2, ZoomIn, ZoomOut, ArrowLeft, ArrowRight, ArrowUp, ArrowDown, X, Activity, CheckCircle2, Info, Aperture, MousePointer2, Settings2, SlidersHorizontal, Wand2
} from 'lucide-react';
import { CephaloTracingLayer } from '../CephaloTracingLayer';
import type { 
  UIMode, VTOSettings, ImageFilters 
} from '../cephaloShared';
import { useOrthoStore } from '../stores/useOrthoStore';
import { cephaloRepository } from '../cephaloRepository';
import { calibrationUiLabel, calibrationUiTone, deriveCalibrationUiState } from '../cephaloCalibration';
import { STEINER_EXPLICIT_ID_SET, STEINER_EXPLICIT_IDENTITIES } from '../cephaloSteinerProtocol';
import { hasCertifiedTweedPoAnatomic } from '../cephaloTweedMerrifieldProtocol';
import { scienceArticles } from '../../../data/science_articles';
import { ClinicalTipBubble } from '../../clinical_tips/components/ClinicalTipBubble';

interface ThemePalette {
  bg: string;
  bgPanel: string;
  bgCard: string;
  bgInput: string;
  border: string;
  borderFocus: string;
  text: string;
  textMuted: string;
  textDim: string;
  accent: string;
  accentSuccess: string;
  accentWarning: string;
  accentError: string;
  shadow: string;
  shadowLg: string;
}

interface Step1CephaloProps {
  P: ThemePalette; // Theme palette
  embedded?: boolean; // Shared desktop workbench hosts controls outside the image.
  fileRef: React.RefObject<HTMLInputElement | null>;
  step1ContainerRef: React.RefObject<HTMLDivElement | null>;
}

export const Step1Cephalo: React.FC<Step1CephaloProps> = ({ P, fileRef, step1ContainerRef, embedded = false }) => {
  const store = useOrthoStore();

  const [showTip, setShowTip] = React.useState(false);
  const [currentTip, setCurrentTip] = React.useState('');
  const [activeMenu, setActiveMenu] = useState<'none' | 'visual' | 'vto'>('none');
  const [showCalibrationAssistant, setShowCalibrationAssistant] = useState(false);
  const [calibrationBusy, setCalibrationBusy] = useState(false);
  const [calibrationActionError, setCalibrationActionError] = useState<string | null>(null);
  const [zoomPercent, setZoomPercent] = useState(100);
  const [viewPan, setViewPan] = useState({ x: 0, y: 0 });
  const [desktopZoomAvailable, setDesktopZoomAvailable] = useState(false);

  React.useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const desktop = window.matchMedia('(min-width: 1280px)');
    const sync = () => {
      setDesktopZoomAvailable(desktop.matches);
      if (!desktop.matches) { setZoomPercent(100); setViewPan({ x: 0, y: 0 }); }
    };
    sync();
    desktop.addEventListener('change', sync);
    return () => desktop.removeEventListener('change', sync);
  }, []);
  React.useEffect(() => {
    setZoomPercent(100);
    setViewPan({ x: 0, y: 0 });
  }, [store.imageSrc]);
  const activeViewZoom = embedded && desktopZoomAvailable ? zoomPercent / 100 : 1;

  React.useEffect(() => {
    if (!store.imageSrc) {
      if (scienceArticles.length > 0) {
        const randomArticle = scienceArticles[Math.floor(Math.random() * scienceArticles.length)];
        setCurrentTip(randomArticle.summary);
        
        const timer = setTimeout(() => {
          setShowTip(true);
        }, 1500);
        
        return () => {
          clearTimeout(timer);
          setShowTip(false);
        };
      }
    } else {
      setShowTip(false);
    }
  }, [store.imageSrc]);

  const handleCalibrationClick = (p: { x: number; y: number }) => {
    if (store.calibrationClickPoints.length < 2) {
      store.setCalibrationClickPoints([...store.calibrationClickPoints, p]);
    }
  };

  const cancelCalibration = () => {
    store.setShowCalibration(false);
    store.setCalibrationClickPoints([]);
    store.setCalibrationDistance('');
    store.setCalibrationStep('selecting');
  };

  const handleFileDrop = (files: FileList | null) => {
    if (!files?.length) return;
    if (!isSupportedCephaloImageFile(files[0])) {
      store.setUploadError('Format non supporté. Utilisez JPEG ou PNG.');
      return;
    }
    store.runAnalysis(files[0]);
  };

  const {
    imageSrc, mode, setMode, imgFilters, setImgFilters, isCalibrated, mmPerPixel, setShowCalibration,
    setCalibrationClickPoints, setCalibrationDistance, setCalibrationStep, magnifierEnabled, setMagnifierEnabled,
    vtoSettings, setVtoSettings, setImageSrc, setLocal, setAnglesData, isStep1Fullscreen, setIsStep1Fullscreen,
    visionMetadata, autoCalibMessage, showCalibration, calibrationClickPoints,
    calibrationStep, calibrationDistance, applyCalibration, local, imgDim,
    updateLandmarksOptimistic, nudgeLandmarkFromKeyboard, activePointId, setActivePointId, anglesData,
    performanceMode, isUploading, uploadError,
    activeMorphing, setActiveMorphing, layerVisibility, layerOpacity, setLayerVisible, setLandmarkEditBaseline
  } = store;

  const calibrationData = anglesData?.__calibrationData ?? null;
  const calibrationState = deriveCalibrationUiState({ isCalibrated, anglesData, calibrationData });
  const calibrationTone = calibrationUiTone(calibrationState);
  const calibrationLabel = calibrationUiLabel(calibrationState);

  const refreshCalibrationFromServer = async () => {
    if (!store.analysisId) return;
    const loaded = await cephaloRepository.getAnalysis(store.analysisId);
    const refreshedAngles = loaded.angles_data || {};
    setAnglesData({ ...refreshedAngles, __calibrationData: loaded.calibration_data || null });
    store.setVisionMetadata(refreshedAngles.vision_metadata || {});
    store.setIsCalibrated(Boolean(loaded.is_calibrated));
    store.setMmPerPixel(typeof loaded.mm_per_pixel === 'number' ? loaded.mm_per_pixel : null);
  };

  const startManualCalibration = () => {
    setCalibrationActionError(null);
    setShowCalibrationAssistant(false);
    setShowCalibration(true);
    setCalibrationClickPoints([]);
    setCalibrationDistance('');
    setCalibrationStep('selecting');
  };

  const handleAutoCalibration = async () => {
    if (!store.analysisId || calibrationBusy) return;
    setCalibrationBusy(true);
    setCalibrationActionError(null);
    try {
      await cephaloRepository.autoCalibrate(store.analysisId);
      await refreshCalibrationFromServer();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setCalibrationActionError(typeof detail === 'string' ? detail : "La réglette détectée ne peut pas être vérifiée automatiquement.");
    } finally {
      setCalibrationBusy(false);
    }
  };

  const handleConfirmAutoCalibration = async () => {
    if (!store.analysisId || calibrationBusy) return;
    setCalibrationBusy(true);
    setCalibrationActionError(null);
    try {
      await cephaloRepository.confirmAutoCalibration(store.analysisId);
      await refreshCalibrationFromServer();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setCalibrationActionError(typeof detail === 'string' ? detail : "La confirmation de calibration a échoué.");
    } finally {
      setCalibrationBusy(false);
    }
  };

  const handleApplyManualCalibration = async () => {
    await applyCalibration();
    try {
      await refreshCalibrationFromServer();
    } catch (error) {
      console.warn('Calibration appliquée mais rechargement de provenance impossible:', error);
    }
  };

  // Historical T1/T2 projections stay visualization-only. LOT07 allows
  // independent layer visibility without defining a new longitudinal registration.
  const computedGhosts = React.useMemo(() => {
    const requested = new Set<'T1' | 'T2'>();
    if (layerVisibility.t1) requested.add('T1');
    if (layerVisibility.t2) requested.add('T2');
    if (activeMorphing === 'T1' || activeMorphing === 'T2') requested.add(activeMorphing);

    return Array.from(requested).flatMap(layer => {
      const projection = layer === 'T1' ? anglesData?.t1_projection : anglesData?.t2_projection;
      if (!projection || Object.keys(projection).length === 0) return [];

      const ghostLandmarks = Object.entries(projection).map(([id, coords]) => ({
        id,
        x: (coords as [number, number])[0],
        y: (coords as [number, number])[1]
      }));

      const layerId: 't1' | 't2' = layer === 'T1' ? 't1' : 't2';
      return [{
        layerId,
        landmarks: ghostLandmarks,
        opacity: 1,
        color: layer === 'T1' ? P.accent : P.accentSuccess
      }];
    });
  }, [activeMorphing, anglesData, layerVisibility.t1, layerVisibility.t2, P]);

  if (!imageSrc) {
    return (
      <div className="flex-1 w-full flex flex-col items-center justify-center min-h-[400px] relative">
        {localStorage.getItem('clinical_tips_enabled') !== 'false' && (
          <ClinicalTipBubble 
            show={showTip} 
            tip={currentTip} 
            onClose={() => setShowTip(false)}
            autoHideMs={2000}
          />
        )}

        <input ref={fileRef} type="file" accept={CEPHALO_ACCEPTED_IMAGE_TYPES} aria-label="Sélectionner une radiographie JPEG ou PNG" className="hidden" onChange={e => handleFileDrop(e.target.files)} />
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-6 max-w-md w-full px-6"
        >
          <div
            className="w-full flex flex-col items-center justify-center gap-6 rounded-2xl px-4 py-12 sm:py-16 cursor-pointer transition-all duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4"
            role="button" tabIndex={isUploading ? -1 : 0} aria-disabled={isUploading} aria-busy={isUploading}
            aria-label="Importer une radiographie JPEG ou PNG"
            onKeyDown={e => { if (!isUploading && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); fileRef.current?.click(); } }}
            onClick={() => !isUploading && fileRef.current?.click()}
            style={{ border: `2px dashed ${P.border}`, background: P.bgCard }}
            onDragOver={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.accent; }}
            onDragLeave={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.border; }}
            onDrop={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.borderColor = P.border; if (!isUploading) handleFileDrop(e.dataTransfer.files); }}
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
                  <div className="text-xs" style={{ color: P.textMuted }}>JPEG ou PNG · Glissez-déposez, cliquez ou appuyez sur Entrée</div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-start gap-3 p-4 rounded-xl mt-2" style={{ background: `${P.accent}05`, border: `1px solid ${P.border}` }}>
            <Info size={16} className="shrink-0 mt-0.5" style={{ color: P.accent }} />
            <p className="text-[11px] leading-relaxed" style={{ color: P.textMuted }}>
              <strong style={{ color: P.text }}>Exigence de Qualité :</strong> Veuillez importer une image numérique haute résolution. Les radiographies floues, pixélisées ou de faible contraste compromettent la précision de l'analyse IA et seront rejetées par le système.
            </p>
          </div>

          {uploadError && (
            <div role="alert" className="flex items-center gap-2 text-sm" style={{ color: P.accentError }}>
              <AlertCircle size={16} />
              {uploadError}
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  const isCinematic = true;
  const cbg = P.bgCard;
  const themeVars = {
    '--ceph-ui-panel': P.bgPanel,
    '--ceph-ui-card': P.bgCard,
    '--ceph-ui-input': P.bgInput,
    '--ceph-ui-border': P.border,
    '--ceph-ui-border-focus': P.borderFocus,
    '--ceph-ui-text': P.text,
    '--ceph-ui-muted': P.textMuted,
    '--ceph-ui-dim': P.textDim,
    '--ceph-ui-accent': P.accent,
    '--ceph-ui-accent-soft': `${P.accent}18`,
    '--ceph-ui-success': P.accentSuccess,
    '--ceph-ui-success-soft': `${P.accentSuccess}18`,
    '--ceph-ui-warning': P.accentWarning,
    '--ceph-ui-warning-soft': `${P.accentWarning}18`,
  } as React.CSSProperties;
  const toneClasses = calibrationTone === 'emerald'
    ? 'bg-[var(--ceph-ui-success-soft)] border-[var(--ceph-ui-success)] text-[var(--ceph-ui-success)] hover:bg-[var(--ceph-ui-success-soft)]'
    : calibrationTone === 'indigo'
      ? 'bg-[var(--ceph-ui-accent-soft)] border-[var(--ceph-ui-accent)] text-[var(--ceph-ui-accent)] hover:bg-[var(--ceph-ui-accent-soft)]'
      : 'bg-[var(--ceph-ui-warning-soft)] border-[var(--ceph-ui-warning)] text-[var(--ceph-ui-warning)] hover:bg-[var(--ceph-ui-warning-soft)]';
  const activeSteinerPlacement = activePointId && STEINER_EXPLICIT_ID_SET.has(activePointId)
    ? STEINER_EXPLICIT_IDENTITIES.find(item => item.id === activePointId) ?? null
    : null;
  const tweedPoAnatomicCertified = React.useMemo(
    () => hasCertifiedTweedPoAnatomic(anglesData),
    [anglesData],
  );

  const handleSteinerExplicitPointPlacement = (p: { x: number; y: number }) => {
    if (!activeSteinerPlacement) return;
    const next = local.landmarks.filter(point => point.id !== activeSteinerPlacement.id);
    updateLandmarksOptimistic([...next, { id: activeSteinerPlacement.id, x: p.x, y: p.y, isAdjusted: true }]);
    setActivePointId(null);
  };

  // Transformed/grid ancestors can clip a position:fixed descendant.
  // React's portal preserves store, editor callbacks and anatomical points.
  const stageContent = (
    <div ref={step1ContainerRef} className={`relative flex min-w-0 flex-col rounded-3xl overflow-hidden ${isStep1Fullscreen ? 'fixed inset-0 z-[9999]' : 'h-[82vh] w-full'}`} style={{ ...themeVars, background: cbg, boxShadow: P.shadowLg, border: `1px solid ${P.border}` }}>
      <div className="absolute inset-2 z-0 overflow-hidden rounded-[1.15rem] border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-panel)] shadow-lg sm:inset-2">
        <CephaloTracingLayer
          imageSrc={imageSrc}
          imgFilters={imgFilters}
          landmarks={local.landmarks}
          baseOpacity={1}
          ghosts={computedGhosts}
          imageWidth={imgDim.w}
          imageHeight={imgDim.h}
          viewZoom={activeViewZoom}
          viewPan={activeViewZoom > 1 ? viewPan : { x: 0, y: 0 }}
          compactLabels={embedded && desktopZoomAvailable}
          onUpdateLandmarks={updateLandmarksOptimistic}
          onKeyboardNudgeLandmark={nudgeLandmarkFromKeyboard}
          activePointId={activePointId}
          focusedPointId={null}
          tweedPoAnatomicCertified={tweedPoAnatomicCertified}
          onPointMouseDown={setActivePointId}
          onEmptyAreaClick={activeSteinerPlacement ? handleSteinerExplicitPointPlacement : undefined}
          visualDebug={anglesData?.visual_debug ?? null}
          isCalibrating={showCalibration}
          calibrationPoints={calibrationClickPoints}
          onAddCalibrationPoint={handleCalibrationClick}
          uiMode={'pro'}
          hoveredMetric={null}
          magnifierEnabled={magnifierEnabled}
          performanceMode={performanceMode}
          vto={vtoSettings}
          layerPresentation={{ visibility: layerVisibility, opacity: layerOpacity }}
        />
      </div>


      <div className="absolute top-3 left-3 right-3 flex flex-wrap items-start justify-between gap-2 z-20 sm:top-6 sm:left-6 sm:right-6">
        <div className="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] backdrop-blur-md">
            <Activity size={12} className="text-[var(--ceph-ui-success)]" />
            <span className="text-[11px] font-bold text-[var(--ceph-ui-success)] tracking-wide uppercase">Édition Active</span>
          </div>
          <button
            type="button"
            onClick={() => { setCalibrationActionError(null); setShowCalibrationAssistant(true); }}
            className={`flex max-w-[230px] items-center gap-2 rounded-full border px-3 py-1.5 backdrop-blur-md transition-colors sm:max-w-none ${toneClasses}`}
            title="État de calibration et provenance" aria-label={`Calibration : ${calibrationLabel}. Consulter les détails`}
            style={{ background: P.bgPanel, color: P.text, borderColor: calibrationTone === 'emerald' ? P.accentSuccess : calibrationTone === 'indigo' ? P.accent : P.accentWarning }}
          >
            {calibrationTone === 'emerald' ? <CheckCircle2 size={12} /> : <Target size={12} />}
            <span className="truncate text-[11px] font-bold tracking-wide uppercase">
              {calibrationLabel}{mmPerPixel ? ` · ${mmPerPixel.toFixed(3)} mm/px` : ''}
            </span>
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button onClick={() => { setImageSrc(undefined); setLocal({ landmarks: [], version: 0 }); setLandmarkEditBaseline([]); setAnglesData({}); }} className="p-2 rounded-full bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] text-[var(--ceph-ui-text)] hover:text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] transition-all backdrop-blur-md" title="Changer d'image">
            <RefreshCw size={14} />
          </button>
          <button onClick={() => setIsStep1Fullscreen((v: boolean) => !v)} className="p-2 rounded-full bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] text-[var(--ceph-ui-text)] hover:text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] transition-all backdrop-blur-md" title={isStep1Fullscreen ? 'Quitter plein écran' : 'Plein écran'}>
            {isStep1Fullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>


      {embedded && desktopZoomAvailable && (
        <div
          data-cephalo-zoom-controls
          aria-label="Grossissement de la radiographie"
          role="group"
          className="absolute bottom-3 left-3 z-40 flex items-center gap-1 rounded-xl border px-1.5 py-1 shadow-lg backdrop-blur-md sm:bottom-6 sm:left-6"
          style={{ borderColor: P.border, background: P.bgPanel, color: P.text }}
        >
          <button type="button" aria-label="Réduire la radiographie"
            disabled={zoomPercent <= 100}
            onClick={() => { setZoomPercent(percent => Math.max(100, percent - 25)); if (zoomPercent <= 125) setViewPan({ x: 0, y: 0 }); }}
            className="flex h-9 w-9 items-center justify-center rounded-lg disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2">
            <ZoomOut size={16} aria-hidden="true" />
          </button>
          <span data-cephalo-zoom-level aria-live="polite" className="w-14 text-center font-mono text-xs font-bold tabular-nums">{zoomPercent} %</span>
          <button type="button" aria-label="Agrandir la radiographie"
            disabled={zoomPercent >= 200}
            onClick={() => setZoomPercent(percent => Math.min(200, percent + 25))}
            className="flex h-9 w-9 items-center justify-center rounded-lg disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2">
            <ZoomIn size={16} aria-hidden="true" />
          </button>
          {zoomPercent > 100 && (
            <div data-cephalo-pan-controls role="group" aria-label="Déplacement de la radiographie"
              className="flex items-center gap-0.5 border-l pl-1" style={{ borderColor: P.border }}>
              {([
                ['left', ArrowLeft, -0.5, 0, 'Déplacer la radiographie à gauche'],
                ['right', ArrowRight, 0.5, 0, 'Déplacer la radiographie à droite'],
                ['up', ArrowUp, 0, -0.5, 'Déplacer la radiographie vers le haut'],
                ['down', ArrowDown, 0, 0.5, 'Déplacer la radiographie vers le bas'],
              ] as const).map(([direction, Icon, dx, dy, label]) => (
                <button key={direction} type="button" aria-label={label}
                  onClick={() => setViewPan(pan => ({
                    x: Math.max(-1, Math.min(1, pan.x + dx)),
                    y: Math.max(-1, Math.min(1, pan.y + dy)),
                  }))}
                  className="flex h-9 w-8 items-center justify-center rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2">
                  <Icon size={15} aria-hidden="true" />
                </button>
              ))}
            </div>
          )}
          <button type="button" aria-label="Afficher toute la radiographie"
            disabled={zoomPercent === 100}
            onClick={() => { setZoomPercent(100); setViewPan({ x: 0, y: 0 }); }}
            className="min-h-9 rounded-lg px-2 text-xs font-semibold disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2">
            Ajuster
          </button>
        </div>
      )}

      <AnimatePresence>
        {showCalibrationAssistant && !showCalibration && (
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12, scale: 0.97 }}
            data-cephalo-calibration-assistant className="fixed left-1/2 top-[min(24vh,16rem)] z-[100] flex max-h-[68vh] w-[calc(100%-1.5rem)] max-w-md -translate-x-1/2 flex-col gap-4 overflow-y-auto rounded-2xl border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-panel)] p-4 shadow-2xl backdrop-blur-2xl sm:p-5"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[10px] font-black uppercase tracking-[0.18em] text-[var(--ceph-ui-muted)]">Calibration R1</div>
                <h3 className="mt-1 text-sm font-black text-[var(--ceph-ui-text)]">{calibrationLabel}</h3>
              </div>
              <button onClick={() => setShowCalibrationAssistant(false)} className="shrink-0 rounded-lg p-1.5 text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]" aria-label="Fermer"><X size={16} /></button>
            </div>

            {calibrationState === 'CANDIDATE_UNVERIFIED' && (
              <>
                <p className="text-xs leading-relaxed text-[var(--ceph-ui-text)]">Une réglette a été détectée. L'échelle reste non vérifiée tant que le serveur n'a pas validé une source physique déjà liée au candidat.</p>
                <button onClick={handleAutoCalibration} disabled={calibrationBusy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--ceph-ui-accent-soft)] px-4 py-3 text-xs font-black uppercase tracking-widest text-[var(--ceph-ui-text)] transition-colors hover:bg-[var(--ceph-ui-accent-soft)] disabled:opacity-50">
                  {calibrationBusy ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                  Vérifier automatiquement
                </button>
                <button onClick={startManualCalibration} disabled={calibrationBusy} className="w-full rounded-xl border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-input)] px-4 py-3 text-xs font-bold text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] disabled:opacity-50">Calibrer manuellement</button>
              </>
            )}

            {calibrationState === 'AUTO_VERIFIED' && (
              <>
                <div className="rounded-xl border border-[var(--ceph-ui-success)] bg-[var(--ceph-ui-success-soft)] p-3 text-xs leading-relaxed text-[var(--ceph-ui-success)]">Échelle utilisable : {mmPerPixel?.toFixed(4)} mm/px. La confirmation du praticien est recommandée mais non obligatoire.</div>
                <button onClick={handleConfirmAutoCalibration} disabled={calibrationBusy} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--ceph-ui-success-soft)] px-4 py-3 text-xs font-black uppercase tracking-widest text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-success-soft)] disabled:opacity-50">
                  {calibrationBusy ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                  Confirmer comme praticien
                </button>
                <button onClick={startManualCalibration} disabled={calibrationBusy} className="w-full rounded-xl border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-input)] px-4 py-3 text-xs font-bold text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] disabled:opacity-50">Modifier manuellement</button>
              </>
            )}

            {calibrationState === 'CLINICIAN_CONFIRMED' && (
              <>
                <div className="rounded-xl border border-[var(--ceph-ui-success)] bg-[var(--ceph-ui-success-soft)] p-3 text-xs leading-relaxed text-[var(--ceph-ui-success)]">Auto-calibration confirmée par le praticien. Le ratio reste {mmPerPixel?.toFixed(4)} mm/px.</div>
                <button onClick={startManualCalibration} disabled={calibrationBusy} className="w-full rounded-xl border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-input)] px-4 py-3 text-xs font-bold text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] disabled:opacity-50">Recalibrer manuellement</button>
              </>
            )}

            {(calibrationState === 'MANUAL_TWO_POINT' || calibrationState === 'LEGACY_VERIFIED') && (
              <>
                <div className="rounded-xl border border-[var(--ceph-ui-accent)] bg-[var(--ceph-ui-accent-soft)] p-3 text-xs leading-relaxed text-[var(--ceph-ui-accent)]">Échelle active : {mmPerPixel?.toFixed(4)} mm/px. La provenance automatique n'est pas revendiquée.</div>
                <button onClick={startManualCalibration} disabled={calibrationBusy} className="w-full rounded-xl border border-[var(--ceph-ui-border)] bg-[var(--ceph-ui-input)] px-4 py-3 text-xs font-bold text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] disabled:opacity-50">Recalibrer manuellement</button>
              </>
            )}

            {calibrationState === 'UNCALIBRATED' && (
              <>
                <p className="text-xs leading-relaxed text-[var(--ceph-ui-text)]">Aucune échelle physique vérifiée n'est disponible. Les mesures linéaires en millimètres restent indisponibles.</p>
                <button onClick={startManualCalibration} className="w-full rounded-xl bg-[var(--ceph-ui-accent-soft)] px-4 py-3 text-xs font-black uppercase tracking-widest text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-accent-soft)]">Calibrer manuellement</button>
              </>
            )}

            {calibrationActionError && (
              <div className="flex items-start gap-2 rounded-xl border border-[var(--ceph-ui-warning)] bg-[var(--ceph-ui-warning-soft)] p-3 text-xs leading-relaxed text-[var(--ceph-ui-warning)]">
                <AlertCircle size={15} className="mt-0.5 shrink-0" />
                <span>{calibrationActionError}</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!embedded && (
        <>
      <div className="absolute left-3 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-30 sm:left-6" onMouseLeave={() => setActiveMenu('none')}>
        <div className="flex flex-col gap-2 p-2 rounded-2xl bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] backdrop-blur-xl shadow-2xl">
          <button 
            onClick={() => { setCalibrationActionError(null); setShowCalibrationAssistant(true); }}
            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${showCalibration || showCalibrationAssistant ? 'bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-accent)] border border-[var(--ceph-ui-accent)]' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Calibration et provenance"
          >
            <Target size={18} />
          </button>

          <button 
            onClick={() => setMagnifierEnabled((v: boolean) => !v)}
            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${magnifierEnabled ? 'bg-[var(--ceph-ui-success-soft)] text-[var(--ceph-ui-success)] border border-[var(--ceph-ui-success)]' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Loupe"
          >
            <MousePointer2 size={18} />
          </button>

          <div className="w-6 h-px bg-[var(--ceph-ui-card)] mx-auto my-1" />

          <div className="relative group">
            <button 
              onMouseEnter={() => setActiveMenu('visual')}
              className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${activeMenu === 'visual' || imgFilters.brightness !== 100 || imgFilters.contrast !== 110 ? 'bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-accent)] border border-[var(--ceph-ui-accent)]' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            >
              <Sun size={18} />
            </button>
            <AnimatePresence>
              {activeMenu === 'visual' && (
                <motion.div 
                  initial={{ opacity: 0, x: -10, scale: 0.9 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: -10, scale: 0.9 }}
                  className="absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 w-48 p-4 rounded-2xl bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] backdrop-blur-2xl shadow-2xl flex flex-col gap-4"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)]">
                      <span>Luminosité</span>
                      <span>{imgFilters.brightness}%</span>
                    </div>
                    <input type="range" min={50} max={200} value={imgFilters.brightness} onChange={e => setImgFilters((f: ImageFilters) => ({ ...f, brightness: +e.target.value }))} className="w-full h-1.5 bg-[var(--ceph-ui-input)] rounded-full appearance-none cursor-pointer" style={{ accentColor: P.accent }} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)]">
                      <span>Contraste</span>
                      <span>{imgFilters.contrast}%</span>
                    </div>
                    <input type="range" min={50} max={300} value={imgFilters.contrast} onChange={e => setImgFilters((f: ImageFilters) => ({ ...f, contrast: +e.target.value }))} className="w-full h-1.5 bg-[var(--ceph-ui-input)] rounded-full appearance-none cursor-pointer" style={{ accentColor: P.accentWarning }} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <button 
            onClick={() => setImgFilters((f: ImageFilters) => ({ ...f, invert: !f.invert }))}
            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${imgFilters.invert ? 'bg-[var(--ceph-ui-card)] text-[var(--ceph-ui-text)] border border-[var(--ceph-ui-border-focus)] shadow-sm' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Inverser les couleurs"
          >
            <Aperture size={18} />
          </button>
        </div>
      </div>

      <div className="absolute right-3 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-30 sm:right-6">
        <div className="flex flex-col gap-2 p-2 rounded-2xl bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] backdrop-blur-xl shadow-2xl">
          <button 
            onClick={() => { setActiveMorphing('none'); setLayerVisible('t1', !layerVisibility.t1); }}
            className={`w-10 h-10 flex items-center justify-center rounded-xl text-[10px] font-black transition-all ${layerVisibility.t1 ? 'bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-text)] shadow-sm' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Morphing à 1 an"
          >
            T1
          </button>
          
          <button 
            onClick={() => { setActiveMorphing('none'); setLayerVisible('t2', !layerVisibility.t2); }}
            className={`w-10 h-10 flex items-center justify-center rounded-xl text-[10px] font-black transition-all ${layerVisibility.t2 ? 'bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-text)] shadow-sm' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Morphing à 5 ans"
          >
            T2
          </button>

          <div className="w-6 h-px bg-[var(--ceph-ui-card)] mx-auto my-1" />

          <button 
            onClick={() => { const next = !layerVisibility.soft_tissue; setLayerVisible('soft_tissue', next); setVtoSettings((v: VTOSettings) => ({ ...v, showSoftTissue: next })); }}
            className={`w-10 h-10 flex items-center justify-center rounded-xl text-[9px] font-black transition-all leading-tight text-center ${layerVisibility.soft_tissue ? 'bg-[var(--ceph-ui-success-soft)] text-[var(--ceph-ui-success)] border border-[var(--ceph-ui-success)]' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
          >
            SKIN
          </button>
          
          <button 
            onClick={() => setVtoSettings((v: VTOSettings) => ({ ...v, showGhostFace: !v.showGhostFace }))}
            className={`w-10 h-10 flex items-center justify-center rounded-xl text-[9px] font-black transition-all leading-tight text-center ${vtoSettings.showGhostFace ? 'bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-accent)] border border-[var(--ceph-ui-accent)]' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
          >
            3D
          </button>

          <div className="w-6 h-px bg-[var(--ceph-ui-card)] mx-auto my-1" />

          <button 
            onClick={() => setVtoSettings((v: VTOSettings) => ({ ...v, enabled: !v.enabled }))}
            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${vtoSettings.enabled ? 'bg-[var(--ceph-ui-warning-soft)] text-[var(--ceph-ui-text)] shadow-sm' : 'text-[var(--ceph-ui-muted)] hover:bg-[var(--ceph-ui-input)] hover:text-[var(--ceph-ui-text)]'}`}
            title="Simulation VTO Interactive"
          >
            <Wand2 size={18} />
          </button>
        </div>
      </div>

        </>
      )}
      <AnimatePresence>
        {vtoSettings.enabled && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[calc(100%-1.5rem)] max-w-[600px] p-4 sm:p-6 rounded-[2rem] z-40 overflow-hidden"
            style={{ 
              background: P.bgPanel,
              border: `1px solid ${P.border}`,
              backdropFilter: 'blur(24px)',
              boxShadow: P.shadowLg
            }}
          >
            <div className="absolute inset-0    pointer-events-none" />
            
            <div className="relative flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center    shadow-lg shadow-sm text-[var(--ceph-ui-text)]">
                  <Wand2 size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-[var(--ceph-ui-text)] tracking-widest uppercase">Studio VTO expérimental</h3>
                  <p className="text-[10px] font-mono text-[var(--ceph-ui-warning)]">APERÇU NON VALIDÉ CLINIQUEMENT</p>
                </div>
              </div>
              <button 
                onClick={() => {
                  const targetU1 = vtoSettings.u1_offset?.x || 0;
                  const targetL1 = vtoSettings.l1_offset?.x || 0;
                  const targetMand = vtoSettings.mand_offset?.x || 0;
                  setVtoSettings(v => ({...v, u1_offset: {x:0,y:0}, l1_offset: {x:0,y:0}, mand_offset: {x:0,y:0}}));
                  setTimeout(() => {
                     setVtoSettings(v => ({...v, u1_offset: {x:targetU1,y:0}, l1_offset: {x:targetL1,y:0}, mand_offset: {x:targetMand,y:0}}));
                  }, 100);
                }}
                className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-text)] hover:text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] transition-colors border border-[var(--ceph-ui-border)]"
              >
                Rejouer
              </button>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between items-end px-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)]">Incisive Supérieure (U1)</label>
                  <span className="text-sm font-mono font-bold text-[var(--ceph-ui-accent)]">
                    {mmPerPixel ? ((vtoSettings.u1_offset?.x || 0) * mmPerPixel).toFixed(1) : 'NC'} <span className="text-[10px] opacity-50">{mmPerPixel ? 'mm' : ''}</span>
                  </span>
                </div>
                <input
                  type="range" min={-60} max={60} step={1}
                  value={vtoSettings.u1_offset?.x || 0}
                  onChange={(e) => setVtoSettings(v => ({ ...v, u1_offset: { x: +e.target.value, y: v.u1_offset?.y || 0 }}))}
                  className="w-full h-2 bg-[var(--ceph-ui-input)] rounded-full appearance-none cursor-pointer"
                  style={{ accentColor: P.accent }}
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-end px-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)]">Incisive Inférieure (L1)</label>
                  <span className="text-sm font-mono font-bold text-[var(--ceph-ui-success)]">
                    {mmPerPixel ? ((vtoSettings.l1_offset?.x || 0) * mmPerPixel).toFixed(1) : 'NC'} <span className="text-[10px] opacity-50">{mmPerPixel ? 'mm' : ''}</span>
                  </span>
                </div>
                <input
                  type="range" min={-60} max={60} step={1}
                  value={vtoSettings.l1_offset?.x || 0}
                  onChange={(e) => setVtoSettings(v => ({ ...v, l1_offset: { x: +e.target.value, y: v.l1_offset?.y || 0 }}))}
                  className="w-full h-2 bg-[var(--ceph-ui-input)] rounded-full appearance-none cursor-pointer"
                  style={{ accentColor: P.accentSuccess }}
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-end px-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)]">Avancement Mandibulaire</label>
                  <span className="text-sm font-mono font-bold text-[var(--ceph-ui-warning)]">
                    {mmPerPixel ? ((vtoSettings.mand_offset?.x || 0) * mmPerPixel).toFixed(1) : 'NC'} <span className="text-[10px] opacity-50">{mmPerPixel ? 'mm' : ''}</span>
                  </span>
                </div>
                <input 
                  type="range" min={-100} max={100} step={1}
                  value={vtoSettings.mand_offset?.x || 0} 
                  onChange={(e) => setVtoSettings(v => ({ ...v, mand_offset: { x: +e.target.value, y: v.mand_offset?.y || 0 }}))}
                  className="w-full h-2 bg-[var(--ceph-ui-input)] rounded-full appearance-none cursor-pointer" 
                  style={{ accentColor: P.accentWarning }}
                />
              </div>
            </div>
            
            <div className="mt-8 flex justify-center">
              <button 
                onClick={() => setVtoSettings(v => ({ ...v, u1_offset: {x:0,y:0}, l1_offset: {x:0,y:0}, mand_offset: {x:0,y:0}}))}
                className="px-6 py-2 rounded-full text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-muted)] hover:text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)] transition-colors"
              >
                Réinitialiser la simulation
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showCalibration && (
          <motion.div initial={{ opacity: 0, y: -20, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -20, scale: 0.95 }} className="absolute top-20 left-1/2 -translate-x-1/2 flex flex-col gap-4 p-4 sm:top-8 sm:p-6 rounded-2xl z-50 w-[calc(100%-1.5rem)] max-w-96" style={{ background: P.bgPanel, backdropFilter: 'blur(16px)', border: `1px solid ${P.borderFocus}`, boxShadow: P.shadowLg }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-accent)] flex items-center justify-center border border-[var(--ceph-ui-accent)]">
                  <Target size={16} />
                </div>
                <span className="text-sm font-black tracking-widest uppercase text-[var(--ceph-ui-text)]">
                  Calibration manuelle
                </span>
              </div>
              <button onClick={cancelCalibration} className="p-1 rounded text-[var(--ceph-ui-muted)] hover:text-[var(--ceph-ui-text)] hover:bg-[var(--ceph-ui-input)]"><X size={16} /></button>
            </div>
            
            {calibrationStep === 'selecting' ? (
              <div className="space-y-4">
                <div className="text-xs text-[var(--ceph-ui-text)] leading-relaxed">
                  {calibrationClickPoints.length === 0 && "1. Cliquez sur le premier point de référence sur la radio."}
                  {calibrationClickPoints.length === 1 && "2. Cliquez sur le deuxième point de référence."}
                  {calibrationClickPoints.length === 2 && "3. Entrez la distance réelle ci-dessous."}
                </div>
                
                {calibrationClickPoints.length === 2 && (
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3 bg-[var(--ceph-ui-panel)] rounded-xl p-2 border border-[var(--ceph-ui-border)]">
                      <span className="text-xs font-black uppercase text-[var(--ceph-ui-muted)] ml-2 flex-1">Distance (mm)</span>
                      <input type="number" value={calibrationDistance} onChange={(e) => setCalibrationDistance(e.target.value)} placeholder="Ex: 10" className="w-20 px-3 py-1.5 rounded-lg text-sm font-mono font-bold bg-[var(--ceph-ui-input)] text-[var(--ceph-ui-text)] outline-none border border-[var(--ceph-ui-border)] focus:border-[var(--ceph-ui-accent)] text-center" />
                    </div>
                    <button onClick={() => setCalibrationStep('entering')} disabled={!calibrationDistance || parseFloat(calibrationDistance) <= 0} className="w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all bg-[var(--ceph-ui-accent-soft)] hover:bg-[var(--ceph-ui-accent-soft)] text-[var(--ceph-ui-text)] disabled:opacity-50 disabled:hover:bg-[var(--ceph-ui-accent-soft)]">
                      Valider la distance
                    </button>
                  </div>
                )}
                
                {calibrationClickPoints.length > 0 && (
                  <button onClick={() => setCalibrationClickPoints([])} className="w-full py-2 text-[10px] font-bold uppercase tracking-widest text-[var(--ceph-ui-muted)] hover:text-[var(--ceph-ui-text)]">
                    Recommencer la sélection
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[var(--ceph-ui-success-soft)] border border-[var(--ceph-ui-success)] flex flex-col items-center justify-center gap-1">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-success)]">Distance Calculée</span>
                  <strong className="text-xl font-mono text-[var(--ceph-ui-text)]">{calibrationDistance} mm</strong>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setCalibrationStep('selecting')} className="flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-[var(--ceph-ui-text)] hover:text-[var(--ceph-ui-text)] bg-[var(--ceph-ui-input)] hover:bg-[var(--ceph-ui-card)] transition-colors">Modifier</button>
                  <button onClick={handleApplyManualCalibration} className="flex-[2] py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all bg-[var(--ceph-ui-success-soft)] hover:bg-[var(--ceph-ui-success-soft)] text-[var(--ceph-ui-text)] shadow-lg shadow-sm">Appliquer</button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute bottom-3 right-3 flex items-center gap-4 text-[11px] font-mono z-20 pointer-events-none sm:bottom-4 sm:right-4">
        <div className="px-3 py-1.5 rounded-full bg-[var(--ceph-ui-panel)] border border-[var(--ceph-ui-border)] backdrop-blur-md text-[var(--ceph-ui-text)]">
          Repères : <span className="text-[var(--ceph-ui-text)] font-bold">{local.landmarks.length}</span>
        </div>
      </div>
    </div>
  );
  return isStep1Fullscreen && typeof document !== 'undefined'
    ? createPortal(stageContent, document.body)
    : stageContent;
};
