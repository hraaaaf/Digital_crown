import React, { useState, useRef, useEffect } from 'react';
import { API_BASE } from '../../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  Upload, Loader2, Activity, ShieldAlert, CheckCircle2,
  History, Sun, Contrast, FlipHorizontal,
  RefreshCcw, Search, Type, SplitSquareVertical, XCircle, Trash2, Scan,
  TrendingUp, Minus, AlertTriangle, EyeOff, RotateCcw
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import { PanoramicHistory } from './PanoramicHistory';
import { XRayCanvas } from './XRayCanvas';
import { ReportViewer } from './ReportViewer';
import { usePanoramicStore, ANOMALY_TAXONOMY } from './stores/usePanoramicStore';
import { LivePreview } from '../admin/DocumentStudio/LivePreview';



interface Annotation {
  id: number;
  x: number;
  y: number;
  text: string;
}

export interface PanoramicStudioProps {
  patientId: number;
  patientName: string;
}

interface ImageFilters {
  brightness: number;
  contrast: number;
  invert: boolean;
}

export const PanoramicStudio: React.FC<PanoramicStudioProps> = ({ patientId, patientName }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'studio' | 'history'>('studio');
  const [imgSize, setImgSize] = useState<{w: number, h: number} | null>(null);
  const [activeDet, setActiveDet] = useState<string | null>(null);
  const [sidebarTab, setSidebarTab] = useState<'diagnostics' | 'report' | 'evolution'>('diagnostics');
  const [evolutionData, setEvolutionData] = useState<any>(null);
  const [evolutionLoading, setEvolutionLoading] = useState(false);
  const [imgFilters, setImgFilters] = useState<ImageFilters>({ brightness: 100, contrast: 110, invert: false });
  const [magnifier, setMagnifier] = useState<{ x: number, y: number, show: boolean }>({ x: 0, y: 0, show: false });
  const [magnifierEnabled, setMagnifierEnabled] = useState(false);
  const [toolMode, setToolMode] = useState<'select' | 'annotate'>('select');
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [compareMode, setCompareMode] = useState(false);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const { toothAnomalies, resetAll, toggleAnomaly } = usePanoramicStore();

  // Fetch temporal comparison whenever patientId changes
  useEffect(() => {
    if (!patientId) return;
    setEvolutionLoading(true);
    api.get(`/ia/patients/${patientId}/panoramic-comparison`)
      .then(res => setEvolutionData(res.data))
      .catch(() => setEvolutionData(null))
      .finally(() => setEvolutionLoading(false));
  }, [patientId]);

  const manualAnomaliesList = Object.entries(toothAnomalies).flatMap(([fdi, anomalies]) => 
    anomalies.map(anomaly => ({ fdi: parseInt(fdi), anomaly }))
  );


  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleSelectHistory = (analysis: any) => {
    const data = {
      id: analysis.id,
      file_url: `${API_BASE}/${analysis.image_path}`,
      vision: { detections_data: analysis.detections_data },
      report_narrative: analysis.report_narrative,
      created_at: analysis.created_at
    };
    
    if (compareMode) {
      setCompareResult(data);
      setViewMode('studio');
    } else {
      setResult(data);
      setViewMode('studio');
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(`/ia/upload-panoramic?patient_id=${patientId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (err) {
      console.error("Erreur lors de l'upload de la panoramique :", err);
      toast.error("Erreur lors de l'analyse panoramique.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async () => {
    if (!result?.id) return;
    
    setLoading(true);
    try {
      const rejectedIndices = result.vision?.detections_data?.detections
        ?.map((d: any, idx: number) => d.rejected ? idx : -1)
        ?.filter((idx: number) => idx !== -1) || [];

      const response = await api.post('/ia/generate-panoramic-report', {
        analysis_id: result.id,
        manual_anomalies: toothAnomalies,
        rejected_detections: rejectedIndices
      });
      
      setResult((prev: any) => ({
        ...prev,
        report_narrative: response.data.report_narrative
      }));
      
      toast.success("Bilan professionnel généré et archivé.");
      resetAll();
    } catch (err) {
      console.error("Erreur lors de la finalisation du bilan :", err);
      toast.error("Erreur lors de la génération du bilan.");
    } finally {
      setLoading(false);
    }
  };

  const toggleRejectDetection = (idx: number) => {
    setResult((prev: any) => {
      if (!prev?.vision?.detections_data?.detections) return prev;
      const newDetections = [...prev.vision.detections_data.detections];
      newDetections[idx] = { ...newDetections[idx], rejected: !newDetections[idx].rejected };
      return {
        ...prev,
        vision: {
          ...prev.vision,
          detections_data: {
            ...prev.vision.detections_data,
            detections: newDetections
          }
        }
      };
    });
  };

  const handleDownloadPDF = async () => {
    if (!result?.id) return;
    setDownloading(true);
    try {
      const response = await api.get(`/ia/panoramic/${result.id}/pdf`);
      window.open(response.data.pdf_url, '_blank');
    } catch (err) {
      console.error("Erreur téléchargement PDF :", err);
      toast.error("Erreur lors de la génération du PDF.");
    } finally {
      setDownloading(false);
    }
  };

  const handlePreview = async () => {
    if (!result?.id) return;
    setIsPreviewLoading(true);
    setPreviewPdfUrl(null);
    try {
      const response = await api.get(`/ia/panoramic/${result.id}/pdf`);
      setPreviewPdfUrl(response.data.pdf_url);
    } catch (err) {
      console.error("Erreur aperçu PDF :", err);
      toast.error("Impossible de charger l'aperçu PDF.");
    } finally {
      setIsPreviewLoading(false);
    }
  };




  const getPathologyColor = (pathology: string) => {
    const pathologies = ['Caries', 'Deep Caries', 'Periapical Lesion', 'Impacted'];
    const treatments = ['Implant', 'Crown', 'Endodontic', 'Restoration', 'Filling'];
    
    if (pathologies.includes(pathology)) return '#EF4444'; // Rouge
    if (treatments.includes(pathology)) return '#10B981'; // Émeraude
    return '#6366F1'; // Indigo
  };

  const handleImageClick = (e: React.MouseEvent) => {
    if (toolMode !== 'annotate' || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    const text = prompt("Détail clinique à ajouter :");
    if (text) {
      setAnnotations(prev => [...prev, { id: Date.now(), x, y, text }]);
    }
    setToolMode('select');
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!magnifierEnabled || !containerRef.current || !result) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMagnifier({ x, y, show: true });
  };

  const filterString = `brightness(${imgFilters.brightness}%) contrast(${imgFilters.contrast}%) invert(${imgFilters.invert ? 100 : 0}%)`;

  return (
    <div className="flex flex-col lg:flex-row h-auto min-h-screen lg:h-full gap-4 lg:gap-6 bg-slate-50/50 p-4 lg:p-6 overflow-y-auto lg:overflow-hidden">
      {/* Colonne Gauche : Workspace Visuel */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden min-h-[50vh] lg:min-h-0">
        <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200/60 p-4 lg:p-6 flex flex-col lg:flex-row items-start lg:items-center justify-between shrink-0 gap-4">
          <div>
            <h2 className="text-xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              Studio Panoramique IA - {patientName}
            </h2>
            <p className="text-sm text-slate-500 mt-1 font-medium italic">Pipeline Loki-Silvres V8 (Détection SOTA)</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-2 lg:gap-3 w-full lg:w-auto">
            <button 
              onClick={() => {
                setCompareMode(!compareMode);
                if (!compareMode) setViewMode('history');
                else setCompareResult(null);
              }}
              className={cn(
                "flex items-center gap-2 px-5 py-3 rounded-xl font-bold transition-all border",
                compareMode ? "bg-indigo-50 text-indigo-600 border-indigo-200 shadow-sm" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-200"
              )}
            >
              <SplitSquareVertical size={18} />
              {compareMode ? 'Quitter Comparaison' : 'Comparer T0/T1'}
            </button>

            <button 
              onClick={() => setViewMode(viewMode === 'studio' ? 'history' : 'studio')}
              className={cn(
                "flex items-center gap-2 px-5 py-3 rounded-xl font-bold transition-all border",
                viewMode === 'history' ? "bg-slate-800 text-white border-slate-800 shadow-lg" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-200"
              )}
            >
              <History size={18} />
              {viewMode === 'history' ? 'Retour Studio' : 'Historique'}
            </button>

            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleUpload} 
              accept="image/*" 
              className="hidden" 
            />
            <button 
              onClick={() => {
                setViewMode('studio');
                fileInputRef.current?.click();
              }}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-200 transition-all active:scale-95 disabled:opacity-50 flex-1 lg:flex-none"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
              {loading ? 'Analyse en cours...' : 'Nouvel Examen'}
            </button>
          </div>
        </div>

        <div className="flex-1 bg-slate-900 rounded-[2rem] overflow-hidden relative shadow-inner border-4 border-white flex items-center justify-center min-h-0">
          {viewMode === 'history' ? (
            <div className="absolute inset-0 bg-white overflow-y-auto p-8">
              <PanoramicHistory 
                patientId={patientId} 
                onSelect={handleSelectHistory} 
                onDelete={(deletedId) => {
                  if (result?.id === deletedId) {
                    setResult(null);
                  }
                  if (compareResult?.id === deletedId) {
                    setCompareResult(null);
                  }
                }}
              />
            </div>
          ) : (
            <>
              {!result && !loading && (
                <div className="text-slate-400 font-mono text-sm tracking-widest flex flex-col items-center justify-center gap-4 h-full p-12 text-center">
                  <div className="w-24 h-24 border-2 border-dashed border-slate-700 rounded-2xl flex items-center justify-center opacity-50 mb-2">
                    <Search size={32} className="text-slate-500" />
                  </div>
                  AUCUNE RADIOGRAPHIE CHARGÉE
                </div>
              )}
              
              {loading && (
                <div className="absolute inset-0 bg-slate-900/90 backdrop-blur-lg z-50 flex flex-col items-center justify-center overflow-hidden">
                  {/* Grille d'arrière-plan technique */}
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
                  
                  {/* Scanner UI */}
                  <div className="relative flex flex-col items-center">
                    <div className="relative w-32 h-32 mb-8">
                      {/* Cercle extérieur tournant */}
                      <div className="absolute inset-0 border-2 border-slate-700 rounded-full" />
                      <div className="absolute inset-0 border-2 border-indigo-500 rounded-full border-t-transparent border-b-transparent animate-spin" style={{ animationDuration: '3s' }} />
                      <div className="absolute inset-2 border-2 border-indigo-400/30 rounded-full border-l-transparent border-r-transparent animate-spin animate-reverse" style={{ animationDuration: '2s' }} />
                      
                      {/* Icône centrale */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Scan size={40} className="text-indigo-400 animate-pulse" />
                      </div>
                      
                      {/* Ligne de balayage */}
                      <div className="absolute top-0 left-0 w-full h-0.5 bg-indigo-400 shadow-[0_0_15px_rgba(129,140,248,0.8)] animate-scan" />
                    </div>

                    <div className="bg-black/40 backdrop-blur-md border border-white/10 px-8 py-4 rounded-2xl shadow-2xl flex flex-col items-center relative overflow-hidden">
                      {/* Effet lueur interne */}
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-indigo-500 to-transparent" />
                      
                      <p className="text-white font-black tracking-[0.3em] uppercase text-[11px] mb-2 flex items-center">
                        Analyse Structurelle
                        <span className="inline-flex ml-1 w-3 overflow-hidden animate-pulse">...</span>
                      </p>
                      <p className="text-indigo-300/80 text-[9px] font-mono tracking-widest uppercase mb-2">
                        Extraction des Landmarks
                      </p>
                      <p className="text-slate-400 text-[8px] font-mono uppercase tracking-[0.2em] bg-slate-800/80 px-3 py-1 rounded-full border border-slate-700/50 whitespace-nowrap">
                        Neural Engine v8.0 • Zéro-Hallucination
                      </p>
                    </div>
                  </div>
                  
                  <style>{`
                    @keyframes scan {
                      0%, 100% { top: 0; opacity: 0; }
                      10%, 90% { opacity: 1; }
                      50% { top: 100%; }
                    }
                    .animate-scan {
                      animation: scan 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
                    }
                    .animate-reverse {
                      animation-direction: reverse;
                    }
                  `}</style>
                </div>
              )}

              {result && result.file_url && (
                <div 
                  className={cn(
                    "relative w-full h-full p-8 flex gap-4 items-center justify-center group",
                    toolMode === 'annotate' ? "cursor-crosshair" : "cursor-none"
                  )}
                  ref={containerRef}
                  onMouseMove={handleMouseMove}
                  onClick={handleImageClick}
                  onMouseLeave={() => setMagnifier(m => ({ ...m, show: false }))}
                >
                  {/* AFFICHAGE COMPARAISON (SIDE BY SIDE) */}
                  {compareMode && compareResult && (
                    <div className="flex-1 h-full flex flex-col gap-2">
                      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Archive (T0) - {new Date(compareResult.created_at).toLocaleDateString()}</div>
                      <div className="flex-1 relative rounded-xl border-2 border-slate-200 overflow-hidden bg-black">
                        <img src={compareResult.file_url} className="w-full h-full object-contain opacity-80" />
                      </div>
                    </div>
                  )}

                  <div 
                    className={cn(
                      "relative flex items-center justify-center shadow-2xl rounded-lg overflow-hidden",
                      compareMode ? "flex-1 h-full" : "w-full h-full"
                    )}
                    style={{ 
                      maxHeight: '100%', 
                      maxWidth: '100%',
                      aspectRatio: !compareMode && imgSize ? `${imgSize.w} / ${imgSize.h}` : 'auto' 
                    }}
                  >
                    {compareMode && (
                      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 text-[10px] font-black text-white bg-indigo-600 px-3 py-1 rounded-full uppercase tracking-widest shadow-lg">Examen Actuel (T1)</div>
                    )}
                    <XRayCanvas 
                      imgUrl={result.file_url}
                      visionData={result.vision?.detections_data || null}
                      imgSize={imgSize}
                      onImgLoad={(e) => {
                        setImgSize({
                          w: e.currentTarget.naturalWidth,
                          h: e.currentTarget.naturalHeight
                        });
                      }}
                      filterString={filterString}
                      activeDet={activeDet}
                      onHoverDetection={(id) => setActiveDet(id)}
                    />


                    {imgSize && (
                      <svg 
                        className="absolute inset-0 w-full h-full pointer-events-none" 
                        viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
                      >
                        {/* RENDU DES ANNOTATIONS MANUELLES */}
                        {annotations.map((ann) => (
                          <motion.g 
                            key={ann.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                          >
                            <circle 
                              cx={(ann.x * imgSize.w) / 100} 
                              cy={(ann.y * imgSize.h) / 100} 
                              r={Math.max(imgSize.w * 0.008, 10)} 
                              fill="rgba(239, 68, 68, 0.8)" 
                              stroke="white" 
                              strokeWidth="2"
                            />
                            <foreignObject
                              x={(ann.x * imgSize.w) / 100 + 15}
                              y={(ann.y * imgSize.h) / 100 - 15}
                              width="200"
                              height="100"
                            >
                              <div className="bg-slate-900/90 backdrop-blur-sm text-white p-2 rounded-lg text-[12px] font-bold border border-white/20 shadow-xl inline-block max-w-[180px] leading-tight">
                                {ann.text}
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setAnnotations(prev => prev.filter(a => a.id !== ann.id));
                                  }}
                                  className="ml-2 text-red-400 hover:text-red-300"
                                >
                                  <XCircle size={12} className="inline" />
                                </button>
                              </div>
                            </foreignObject>
                          </motion.g>
                        ))}
                      </svg>
                    )}
                  </div>

                  {/* LOUPE CONTEXTUELLE */}
                  <AnimatePresence>
                    {magnifierEnabled && magnifier.show && result && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.5 }}
                        className="absolute pointer-events-none z-50 rounded-full border-4 border-white shadow-2xl overflow-hidden bg-slate-900"
                        style={{
                          width: 200,
                          height: 200,
                          left: `${magnifier.x}%`,
                          top: `${magnifier.y}%`,
                          transform: 'translate(-50%, -50%)',
                          boxShadow: '0 0 40px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.3)'
                        }}
                      >
                        <div 
                          className="absolute w-full h-full"
                          style={{
                            backgroundImage: `url(${result.file_url})`,
                            backgroundRepeat: 'no-repeat',
                            backgroundSize: '800%', // Zoom 8x
                            backgroundPosition: `${magnifier.x}% ${magnifier.y}%`,
                            filter: filterString
                          }}
                        />
                        {/* Réticule de la loupe */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-full h-[1px] bg-indigo-500/50" />
                          <div className="h-full w-[1px] bg-indigo-500/50" />
                          <div className="absolute w-4 h-4 border border-indigo-400 rounded-full" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* BARRE D'OUTILS IMAGE FLOTTANTE */}
                  <div className="absolute bottom-4 lg:bottom-8 left-1/2 -translate-x-1/2 bg-slate-800/90 backdrop-blur-md px-4 py-2 lg:px-6 lg:py-3 rounded-2xl border border-white/10 shadow-2xl flex flex-wrap justify-center items-center gap-2 lg:gap-6 z-40 w-[95%] lg:w-auto max-w-md lg:max-w-none">
                    <div className="flex items-center gap-3">
                      <Sun size={16} className="text-amber-400" />
                      <input 
                        type="range" min="50" max="200" value={imgFilters.brightness} 
                        onChange={(e) => setImgFilters(f => ({ ...f, brightness: Number(e.target.value) }))}
                        className="w-16 lg:w-24 accent-amber-400 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    <div className="w-[1px] h-6 bg-white/10" />
                    <div className="flex items-center gap-3">
                      <Contrast size={16} className="text-indigo-400" />
                      <input 
                        type="range" min="50" max="200" value={imgFilters.contrast} 
                        onChange={(e) => setImgFilters(f => ({ ...f, contrast: Number(e.target.value) }))}
                        className="w-16 lg:w-24 accent-indigo-400 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    <div className="w-[1px] h-6 bg-white/10" />
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => setImgFilters(f => ({ ...f, invert: !f.invert }))}
                        className={cn("p-2 rounded-lg transition-all", imgFilters.invert ? "bg-indigo-500 text-white" : "text-slate-400 hover:text-white")}
                        title="Inverser les couleurs (Négatif)"
                      >
                        <FlipHorizontal size={18} />
                      </button>
                      <button 
                        onClick={() => setMagnifierEnabled(!magnifierEnabled)}
                        className={cn("p-2 rounded-lg transition-all", magnifierEnabled ? "bg-indigo-500 text-white" : "text-slate-400 hover:text-white")}
                        title="Loupe contextuelle"
                      >
                        <Search size={18} />
                      </button>
                      <button 
                        onClick={() => setToolMode(toolMode === 'annotate' ? 'select' : 'annotate')}
                        className={cn("p-2 rounded-lg transition-all", toolMode === 'annotate' ? "bg-red-500 text-white" : "text-slate-400 hover:text-white")}
                        title="Ajouter un détail clinique"
                      >
                        <Type size={18} />
                      </button>
                      <button 
                        onClick={() => setImgFilters({ brightness: 100, contrast: 110, invert: false })}
                        className="p-2 text-slate-400 hover:text-white transition-all"
                        title="Réinitialiser les filtres"
                      >
                        <RefreshCcw size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Colonne Droite : Intelligence Clinique */}
      <div className="w-full lg:w-[400px] flex flex-col gap-4 shrink-0 lg:overflow-hidden min-h-[600px] lg:min-h-0">
        <div className="bg-white rounded-[2.5rem] shadow-sm border border-slate-200/60 flex-1 overflow-hidden flex flex-col">
          {result ? (
            <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col relative">
              
              {/* TABS HEADER */}
              <div className="sticky top-0 z-[50] bg-white/90 backdrop-blur-md border-b border-slate-100 p-2 flex gap-2 shrink-0">
                <button
                  onClick={() => setSidebarTab('diagnostics')}
                  className={cn("flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all", sidebarTab === 'diagnostics' ? "bg-indigo-600 text-white shadow-md shadow-indigo-200" : "bg-transparent text-slate-400 hover:bg-slate-50")}
                >
                  Diagnostics
                </button>
                <button
                  onClick={() => setSidebarTab('report')}
                  className={cn("flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all", sidebarTab === 'report' ? "bg-indigo-600 text-white shadow-md shadow-indigo-200" : "bg-transparent text-slate-400 hover:bg-slate-50")}
                >
                  Bilan PDF
                </button>
                <button
                  onClick={() => setSidebarTab('evolution')}
                  className={cn("flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all", sidebarTab === 'evolution' ? "bg-indigo-600 text-white shadow-md shadow-indigo-200" : "bg-transparent text-slate-400 hover:bg-slate-50")}
                >
                  Évolution
                </button>
              </div>

              {sidebarTab === 'evolution' ? (
                <div className="p-6 space-y-5 flex-1 flex flex-col">
                  {evolutionLoading ? (
                    <div className="flex-1 flex items-center justify-center">
                      <Loader2 size={24} className="animate-spin text-indigo-400" />
                    </div>
                  ) : !evolutionData?.available ? (
                    <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
                      <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center">
                        <TrendingUp size={22} className="text-slate-300" />
                      </div>
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Évolution indisponible</p>
                      <p className="text-[10px] text-slate-400 max-w-[180px]">
                        {evolutionData?.reason || 'Analysez au moins 2 bilans pour voir l\'évolution temporelle.'}
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Dates */}
                      <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest text-center">
                        {evolutionData.older_date} → {evolutionData.newer_date}
                      </div>

                      {/* Summary counters */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-rose-50 border border-rose-100 rounded-2xl p-3 text-center">
                          <div className="text-2xl font-black text-rose-600">{evolutionData.new_findings?.length ?? 0}</div>
                          <div className="text-[8px] font-bold text-rose-400 uppercase tracking-widest flex items-center justify-center gap-1 mt-0.5"><TrendingUp size={9} /> Nouvelles</div>
                        </div>
                        <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-3 text-center">
                          <div className="text-2xl font-black text-emerald-600">{evolutionData.resolved_findings?.length ?? 0}</div>
                          <div className="text-[8px] font-bold text-emerald-400 uppercase tracking-widest flex items-center justify-center gap-1 mt-0.5"><CheckCircle2 size={9} /> Résolues</div>
                        </div>
                        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-3 text-center">
                          <div className="text-2xl font-black text-amber-600">{evolutionData.worsened_findings?.length ?? 0}</div>
                          <div className="text-[8px] font-bold text-amber-400 uppercase tracking-widest flex items-center justify-center gap-1 mt-0.5"><AlertTriangle size={9} /> Aggravées</div>
                        </div>
                        <div className="bg-slate-50 border border-slate-100 rounded-2xl p-3 text-center">
                          <div className="text-2xl font-black text-slate-500">{evolutionData.stable_findings?.length ?? 0}</div>
                          <div className="text-[8px] font-bold text-slate-400 uppercase tracking-widest flex items-center justify-center gap-1 mt-0.5"><Minus size={9} /> Stables</div>
                        </div>
                      </div>

                      {/* Details */}
                      {evolutionData.new_findings?.length > 0 && (
                        <div className="space-y-1.5">
                          <h5 className="text-[8px] font-black text-rose-500 uppercase tracking-widest">Nouvelles anomalies</h5>
                          {evolutionData.new_findings.map((f: string, i: number) => (
                            <div key={i} className="text-[10px] text-slate-600 bg-rose-50 px-3 py-1.5 rounded-xl">{f}</div>
                          ))}
                        </div>
                      )}
                      {evolutionData.worsened_findings?.length > 0 && (
                        <div className="space-y-1.5">
                          <h5 className="text-[8px] font-black text-amber-500 uppercase tracking-widest">Aggravations</h5>
                          {evolutionData.worsened_findings.map((f: string, i: number) => (
                            <div key={i} className="text-[10px] text-slate-600 bg-amber-50 px-3 py-1.5 rounded-xl">{f}</div>
                          ))}
                        </div>
                      )}

                      {/* Narrative */}
                      <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-4">
                        <p className="text-[10px] font-semibold text-indigo-700 leading-relaxed">{evolutionData.summary_text}</p>
                      </div>
                    </>
                  )}
                </div>
              ) : sidebarTab === 'report' ? (
                <div className="flex-1 flex flex-col">
                  <ReportViewer
                    markdown={result.report_narrative}
                    isGenerating={loading}
                    engineName="Loki-Silvres V8 (Déterministe)"
                    onDownload={handleDownloadPDF}
                    isDownloading={downloading}
                    onPreview={handlePreview}
                  />
                </div>
              ) : (
                <div className="p-8 space-y-8 flex-1 flex flex-col">
                  {result.vision?.detections_data?.detections?.length > 0 && (
                    <div className="space-y-4">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                      Cartographie des Anomalies
                    </h4>
                    <div className="grid gap-3">
                      {/* Group by FDI */}
                      {Object.entries(
                        result.vision.detections_data.detections.reduce((acc: any, det: any, idx: number) => {
                          if (!acc[det.fdi]) acc[det.fdi] = [];
                          acc[det.fdi].push({ ...det, originalIdx: idx, uid: `det-${idx}` });
                          return acc;
                        }, {})
                      ).map(([fdiStr, dets]: [string, any]) => {
                        const fdi = parseInt(fdiStr);
                        // Is any detection active in this group?
                        const isActiveGroup = dets.some((d: any) => activeDet === d.uid);
                        // All rejected?
                        const allRejected = dets.every((d: any) => d.rejected);
                        
                        return (
                          <div 
                            key={`group-${fdi}`}
                            className={cn(
                              "rounded-2xl border transition-all duration-300 overflow-hidden",
                              isActiveGroup ? "border-indigo-400 shadow-xl shadow-indigo-100" : "border-slate-200",
                              allRejected ? "opacity-50" : ""
                            )}
                          >
                            <div className={cn(
                              "px-4 py-2 flex items-center justify-between border-b",
                              isActiveGroup ? "bg-indigo-600 text-white border-indigo-500" : "bg-slate-50 border-slate-100 text-slate-700"
                            )}>
                              <span className="font-black text-sm">Dent {fdi}</span>
                            </div>
                            
                            <div className="flex flex-col">
                              {dets.map((det: any) => {
                                const isItemActive = activeDet === det.uid;
                                return (
                                  <motion.div 
                                    key={det.uid} 
                                    onMouseEnter={() => setActiveDet(det.uid)}
                                    onMouseLeave={() => setActiveDet(null)}
                                    className={cn(
                                      "flex items-center justify-between p-3 border-b last:border-b-0 transition-all cursor-pointer group/det",
                                      isItemActive ? "bg-indigo-50/50" : "bg-white hover:bg-slate-50",
                                      det.rejected ? "opacity-40" : ""
                                    )}
                                  >
                                    <div className="flex items-center gap-3">
                                      <div 
                                        className="w-2.5 h-2.5 rounded-full shadow-sm"
                                        style={{ backgroundColor: det.rejected ? '#94a3b8' : getPathologyColor(det.label) }}
                                      />
                                      <span 
                                        className={cn(
                                          "text-xs font-bold tracking-wide",
                                          det.rejected ? "text-slate-400 line-through" : "text-slate-700"
                                        )}
                                      >
                                        {det.label.toUpperCase()}
                                      </span>
                                    </div>
                                    
                                    <div className="flex items-center gap-2">
                                      {det.confidence && (
                                        <span className={cn(
                                          "text-[9px] font-mono font-bold px-1.5 py-0.5 rounded",
                                          det.confidence >= 0.9 ? "bg-emerald-100 text-emerald-700" : 
                                          det.confidence >= 0.7 ? "bg-amber-100 text-amber-700" : "bg-rose-100 text-rose-700",
                                          det.rejected && "grayscale opacity-50"
                                        )}>
                                          {Math.round(det.confidence * 100)}%
                                        </span>
                                      )}
                                      
                                      <button
                                        onClick={(e) => { e.stopPropagation(); toggleRejectDetection(det.originalIdx); }}
                                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-all opacity-0 group-hover/det:opacity-100"
                                        title={det.rejected ? "Restaurer" : "Rejeter (Faux positif)"}
                                      >
                                        {det.rejected ? <RotateCcw size={14} /> : <EyeOff size={14} />}
                                      </button>
                                    </div>
                                  </motion.div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* SECTION SÉLECTIONS MANUELLES */}
                {(annotations.length > 0 || manualAnomaliesList.length > 0) && (
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                      <Type size={12} className="text-indigo-500" />
                      Ajustements Manuels
                    </h4>
                    <div className="space-y-2">
                      {manualAnomaliesList.map((item, idx) => {
                        const def = ANOMALY_TAXONOMY.find(t => t.id === item.anomaly);
                        const label = def ? def.label : item.anomaly;
                        return (
                          <div key={`manual-${idx}`} className="bg-indigo-50/50 border border-indigo-100 p-4 rounded-2xl flex justify-between items-center group transition-all">
                            <div className="flex items-center gap-3">
                              <span className="font-black text-sm text-indigo-900">Dent {item.fdi}</span>
                              <span className="text-xs font-bold text-slate-600">{label}</span>
                            </div>
                            <button 
                              onClick={() => toggleAnomaly(item.fdi, item.anomaly)}
                              className="text-red-400 hover:text-red-600 transition-all p-1 bg-white rounded-full shadow-sm opacity-0 group-hover:opacity-100"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        );
                      })}
                      {annotations.map((ann) => (
                        <div key={ann.id} className="bg-slate-50 border border-slate-200 p-4 rounded-2xl flex justify-between items-center group transition-all">
                          <span className="text-xs font-bold text-slate-700">{ann.text}</span>
                          <button 
                            onClick={() => setAnnotations(prev => prev.filter(a => a.id !== ann.id))}
                            className="text-red-400 hover:text-red-600 transition-all p-1 bg-white rounded-full shadow-sm opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="pt-4 mt-auto sticky bottom-0 bg-white pb-2 shrink-0">
                  <button 
                    onClick={async () => {
                      await handleFinalize();
                      setSidebarTab('report'); // Switch to report tab on finalize
                    }}
                    disabled={loading}
                    className="w-full py-5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-[1.5rem] font-black tracking-widest shadow-xl shadow-indigo-100 transition-all active:scale-95 flex items-center justify-center gap-3 group disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : <CheckCircle2 size={20} className="group-hover:scale-110 transition-transform" />}
                    VALIDER ET GÉNÉRER
                  </button>
                </div>

              </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8">
              <h3 className="text-xs font-black text-slate-400 tracking-[0.2em] mb-12 flex items-center gap-2 uppercase">
                <ShieldAlert size={16} className="text-indigo-500" />
                Intelligence Clinique IA
              </h3>
              <div className="flex flex-col items-center justify-center text-slate-300 gap-4 opacity-40">
                <div className="w-20 h-20 rounded-full bg-slate-50 flex items-center justify-center border-2 border-dashed border-slate-200">
                  <Activity size={40} />
                </div>
                <p className="text-[10px] font-black uppercase tracking-widest text-center">En attente d'imagerie panoramique...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #f1f5f9;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #e2e8f0;
        }
      `}</style>
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
                setPreviewPdfUrl(null);
                setIsPreviewLoading(false);
              }} 
              title="Aperçu du Bilan Panoramique" 
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>

  );
};

export default PanoramicStudio;
