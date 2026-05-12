import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Loader2, AlertCircle, Moon, Sun, ZoomIn, ZoomOut, Target, RefreshCw, Maximize2, Minimize2, X, Activity, CheckCircle2, Info
} from 'lucide-react';
import { CephaloTracingLayer } from '../CephaloTracingLayer';
import type { 
  UIMode, VTOSettings, ImageFilters 
} from '../cephaloShared';
import { useOrthoStore } from '../stores/useOrthoStore';
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
  fileRef: React.RefObject<HTMLInputElement | null>;
  step1ContainerRef: React.RefObject<HTMLDivElement | null>;
}

export const Step1Cephalo: React.FC<Step1CephaloProps> = ({ P, fileRef, step1ContainerRef }) => {
  const store = useOrthoStore();

  const [showTip, setShowTip] = React.useState(false);
  const [currentTip, setCurrentTip] = React.useState('');

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
    if (!files[0].type.startsWith('image/')) {
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
    updateLandmarksOptimistic, activePointId, setActivePointId, anglesData,
    performanceMode, isUploading, uploadError
  } = store;

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

          <div className="flex items-start gap-3 p-4 rounded-xl mt-2" style={{ background: `${P.accent}05`, border: `1px solid ${P.border}` }}>
            <Info size={16} className="shrink-0 mt-0.5" style={{ color: P.accent }} />
            <p className="text-[11px] leading-relaxed" style={{ color: P.textMuted }}>
              <strong style={{ color: P.text }}>Exigence de Qualité :</strong> Veuillez importer une image numérique haute résolution. Les radiographies floues, pixélisées ou de faible contraste compromettent la précision de l'analyse IA et seront rejetées par le système.
            </p>
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
            onClick={() => setMode((m: UIMode) => m === 'light' ? 'dark' : 'light')}
            className="p-1.5 rounded-lg transition-all"
            style={{ border: `1px solid ${P.border}`, color: P.textDim }}
            title={mode === 'light' ? 'Mode sombre' : 'Mode clair'}
          >
            {mode === 'light' ? <Moon size={14} /> : <Sun size={14} />}
          </button>
          <div className="h-4 w-[1px]" style={{ background: P.border }} />
          <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <Activity size={12} className="text-emerald-500" />
            <span className="text-[10px] font-bold text-emerald-600">Tous les points sont repositionnables manuellement</span>
          </div>
        </div>
        <div className="w-px h-4 opacity-20" style={{ background: P.border }} />
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono" style={{ color: P.textDim }}>L</span>
          <input type="range" min={50} max={200} value={imgFilters.brightness} onChange={e => setImgFilters((f: ImageFilters) => ({ ...f, brightness: +e.target.value }))} className="w-20 h-1 cursor-pointer" style={{ accentColor: P.accent }} title="Luminosité" />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-mono" style={{ color: P.textDim }}>C</span>
          <input type="range" min={50} max={300} value={imgFilters.contrast} onChange={e => setImgFilters((f: ImageFilters) => ({ ...f, contrast: +e.target.value }))} className="w-20 h-1 cursor-pointer" style={{ accentColor: P.accentWarning }} title="Contraste" />
        </div>
        <button onClick={() => setImgFilters((f: ImageFilters) => ({ ...f, invert: !f.invert }))} className="px-2 py-1 rounded text-[10px] font-mono transition-all" style={{ background: imgFilters.invert ? `${P.accent}20` : 'transparent', border: `1px solid ${imgFilters.invert ? P.accent : P.border}`, color: imgFilters.invert ? P.accent : P.textDim }}>INV</button>
        
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
          <button onClick={() => setMagnifierEnabled((v: boolean) => !v)} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all" style={{ background: magnifierEnabled ? `${P.accent}15` : 'transparent', border: `1px solid ${magnifierEnabled ? P.accent : P.border}`, color: magnifierEnabled ? P.accent : P.textMuted }}>
            {magnifierEnabled ? <ZoomOut size={13} /> : <ZoomIn size={13} />}
          </button>
        </div>

        <div className="w-px h-4 opacity-20" style={{ background: P.border }} />

        {/* Contrôles Esthétiques & Simulation */}
        <div className="flex items-center gap-2">
           <button 
              onClick={() => setVtoSettings((v: VTOSettings) => ({ ...v, showSoftTissue: !v.showSoftTissue }))}
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
              onClick={() => setVtoSettings((v: VTOSettings) => ({ ...v, showGhostFace: !v.showGhostFace }))}
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
              onClick={() => setVtoSettings((v: VTOSettings) => ({ ...v, enabled: !v.enabled }))}
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

        

        <button onClick={() => setIsStep1Fullscreen((v: boolean) => !v)} className="p-1.5 rounded-lg transition-all" style={{ border: `1px solid ${isStep1Fullscreen ? P.accent : P.border}`, color: isStep1Fullscreen ? P.accent : P.textDim, background: isStep1Fullscreen ? `${P.accent}15` : 'transparent' }} title={isStep1Fullscreen ? 'Quitter plein écran' : 'Plein écran'}>
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
                      const targetU1 = vtoSettings.u1_offset?.x || 0;
                      const targetL1 = vtoSettings.l1_offset?.x || 0;
                      const targetMand = vtoSettings.mand_offset?.x || 0;
                      setVtoSettings(v => ({...v, u1_offset: {x:0,y:0}, l1_offset: {x:0,y:0}, mand_offset: {x:0,y:0}}));
                      setTimeout(() => {
                         setVtoSettings(v => ({...v, u1_offset: {x:targetU1,y:0}, l1_offset: {x:targetL1,y:0}, mand_offset: {x:targetMand,y:0}}));
                      }, 100);
                    }}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <Activity size={14} className="animate-pulse" style={{ color: P.accentSuccess }} />
                  </button>
                  <button onClick={() => setVtoSettings(v => ({...v, enabled: false}))} className="p-1 rounded-lg hover:bg-white/10 transition-colors">
                    <X size={14} style={{ color: P.textDim }} />
                  </button>
                </div>
              </div>

              <div className="space-y-6">
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

        </div>
      </div>

    </div>
  );
};
