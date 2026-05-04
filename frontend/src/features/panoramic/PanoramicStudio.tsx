import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Loader2, Activity, ShieldAlert, CheckCircle2, 
  History, Sun, Contrast, FlipHorizontal, 
  RefreshCcw, Info, Search, Type, SplitSquareVertical, XCircle, Trash2
} from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import { PanoramicHistory } from './PanoramicHistory';

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
  const [activeDet, setActiveDet] = useState<number | null>(null);
  const [imgFilters, setImgFilters] = useState<ImageFilters>({ brightness: 100, contrast: 110, invert: false });
  const [magnifier, setMagnifier] = useState<{ x: number, y: number, show: boolean }>({ x: 0, y: 0, show: false });
  const [magnifierEnabled, setMagnifierEnabled] = useState(true);
  const [toolMode, setToolMode] = useState<'select' | 'annotate'>('select');
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [compareMode, setCompareMode] = useState(false);
  const [compareResult, setCompareResult] = useState<any>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleSelectHistory = (analysis: any) => {
    const data = {
      id: analysis.id,
      file_url: `http://localhost:8000/${analysis.image_path}`,
      vision: analysis.detections_data,
      report: { narrative_report: analysis.report_narrative },
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
      alert("Une erreur est survenue lors de l'analyse.");
    } finally {
      setLoading(false);
    }
  };

  const getPathologyColor = (pathology: string) => {
    switch(pathology) {
      case 'Caries': return 'rgba(234, 179, 8, 1)'; // Yellow
      case 'Deep Caries': return 'rgba(239, 68, 68, 1)'; // Red
      case 'Periapical Lesions': return 'rgba(168, 85, 247, 1)'; // Purple
      case 'Impacted Teeth': return 'rgba(59, 130, 246, 1)'; // Blue
      default: return 'rgba(34, 197, 94, 1)'; // Green
    }
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
    if (!containerRef.current || !result) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setMagnifier({ x, y, show: true });
  };

  const filterString = `brightness(${imgFilters.brightness}%) contrast(${imgFilters.contrast}%) invert(${imgFilters.invert ? 100 : 0}%)`;

  return (
    <div className="flex flex-col md:flex-row h-full gap-6 bg-slate-50/50 p-6 overflow-hidden">
      {/* Colonne Gauche : Workspace Visuel */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200/60 p-6 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              <Activity className="text-indigo-600" />
              Studio Panoramique IA - {patientName}
            </h2>
            <p className="text-sm text-slate-500 mt-1 font-medium italic">Analyse DENTEX SOTA (Deep Learning Hierarchical Engine)</p>
          </div>
          
          <div className="flex items-center gap-3">
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
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg shadow-indigo-200 transition-all active:scale-95 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
              {loading ? 'Analyse en cours...' : 'Nouvel Examen'}
            </button>
          </div>
        </div>

        <div className="flex-1 bg-slate-900 rounded-[2rem] overflow-hidden relative shadow-inner border-4 border-white flex items-center justify-center min-h-0">
          {viewMode === 'history' ? (
            <div className="absolute inset-0 bg-white overflow-y-auto p-8">
              <PanoramicHistory patientId={patientId} onSelect={handleSelectHistory} />
            </div>
          ) : (
            <>
              {!result && !loading && (
                <div className="text-slate-500 font-mono text-sm tracking-widest flex flex-col items-center gap-4">
                  <Activity size={40} className="text-slate-700 animate-pulse" />
                  AUCUNE RADIOGRAPHIE CHARGÉE
                </div>
              )}
              
              {loading && (
                <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-md z-50 flex flex-col items-center justify-center">
                  <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
                  <p className="text-indigo-400 font-black tracking-[0.3em] animate-pulse uppercase text-xs">Extraction des Landmarks</p>
                  <p className="text-slate-500 text-[10px] mt-2 font-mono">Neural Engine v4.3 • SOTA DENTEX</p>
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
                    <img 
                      src={result.file_url} 
                      alt="Panoramique" 
                      className="w-full h-full object-contain" 
                      style={{ filter: filterString }}
                      onLoad={(e) => {
                        setImgSize({
                          w: e.currentTarget.naturalWidth,
                          h: e.currentTarget.naturalHeight
                        });
                      }}
                    />
                    
                    {imgSize && (
                      <svg 
                        className="absolute inset-0 w-full h-full pointer-events-none" 
                        viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
                      >
                        {result.vision?.detections?.map((det: any, idx: number) => {
                          const [x_min, y_min, x_max, y_max] = det.bbox;
                          const width = x_max - x_min;
                          const height = y_max - y_min;
                          const color = getPathologyColor(det.pathology);
                          
                          return (
                            <motion.g 
                              key={idx}
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: activeDet === null || activeDet === idx ? 1 : 0.15, scale: 1 }}
                              transition={{ duration: 0.3 }}
                            >
                              <rect 
                                x={x_min} 
                                y={y_min} 
                                width={width} 
                                height={height} 
                                fill={color} 
                                fillOpacity={activeDet === idx ? 0.35 : 0.1}
                                stroke={color} 
                                strokeWidth={activeDet === idx ? Math.max(imgSize.w * 0.005, 4) : Math.max(imgSize.w * 0.002, 2)}
                                rx={imgSize.w * 0.005}
                                className="transition-all duration-300"
                              />
                              <text 
                                x={x_min} 
                                y={y_min - (imgSize.h * 0.01)} 
                                fill={color}
                                fontSize={activeDet === idx ? Math.max(imgSize.h * 0.02, 18) : Math.max(imgSize.h * 0.015, 12)}
                                fontWeight="900"
                                style={{ 
                                  textShadow: '0px 2px 4px rgba(0,0,0,0.9)',
                                  transition: 'all 0.3s ease'
                                }}
                              >
                                {det.tooth}
                              </text>
                            </motion.g>
                          );
                        })}

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
                  <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-slate-800/90 backdrop-blur-md px-6 py-3 rounded-2xl border border-white/10 shadow-2xl flex items-center gap-6 z-40">
                    <div className="flex items-center gap-3">
                      <Sun size={16} className="text-amber-400" />
                      <input 
                        type="range" min="50" max="200" value={imgFilters.brightness} 
                        onChange={(e) => setImgFilters(f => ({ ...f, brightness: Number(e.target.value) }))}
                        className="w-24 accent-amber-400 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    <div className="w-[1px] h-6 bg-white/10" />
                    <div className="flex items-center gap-3">
                      <Contrast size={16} className="text-indigo-400" />
                      <input 
                        type="range" min="50" max="200" value={imgFilters.contrast} 
                        onChange={(e) => setImgFilters(f => ({ ...f, contrast: Number(e.target.value) }))}
                        className="w-24 accent-indigo-400 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
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
      <div className="w-[400px] flex flex-col gap-4 shrink-0 overflow-hidden">
        <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200/60 p-6 flex-1 overflow-hidden flex flex-col">
          <h3 className="text-sm font-black text-slate-400 tracking-[0.2em] mb-6 flex items-center gap-2 uppercase shrink-0">
            <ShieldAlert size={16} className="text-indigo-500" />
            Intelligence Clinique IA
          </h3>

          {result ? (
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-6">
              {result.vision?.mode_inference === 'MOCK' && (
                <div className="bg-amber-50 text-amber-700 p-4 rounded-2xl text-[11px] font-bold border border-amber-200 flex items-start gap-3">
                  <Info size={16} className="mt-0.5 shrink-0" />
                  <div>
                    <p className="uppercase tracking-wider mb-1">Mode Simulation Actif</p>
                    <p className="font-medium opacity-80 leading-relaxed">Les poids du modèle SOTA n'ont pas été détectés. Utilisation du moteur heuristique de démonstration.</p>
                  </div>
                </div>
              )}

              <div className="bg-slate-50/80 rounded-2xl p-5 border border-slate-100">
                <div className="prose prose-sm prose-slate max-w-none">
                  {result.report?.narrative_report?.split('\n').map((line: string, i: number) => (
                    <p key={i} className="mb-2 text-slate-700 font-medium leading-relaxed text-[13px]">
                      {line.startsWith('•') ? (
                        <span className="flex items-start gap-2">
                          <span className="text-indigo-500 mt-1 shrink-0">•</span>
                          <span>{line.replace('•', '').trim()}</span>
                        </span>
                      ) : line}
                    </p>
                  ))}
                </div>
              </div>

              {result.vision?.detections?.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
                    <Activity size={12} />
                    Cartographie des Anomalies
                  </h4>
                  <div className="grid gap-2">
                    {result.vision.detections.map((det: any, idx: number) => (
                      <motion.div 
                        key={idx} 
                        onMouseEnter={() => setActiveDet(idx)}
                        onMouseLeave={() => setActiveDet(null)}
                        whileHover={{ x: 8 }}
                        className={cn(
                          "flex items-center justify-between p-4 rounded-2xl border transition-all duration-300 cursor-pointer",
                          activeDet === idx 
                            ? "bg-indigo-600 border-indigo-600 text-white shadow-xl shadow-indigo-100" 
                            : "bg-white border-slate-100 text-slate-600 hover:border-indigo-200"
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <div 
                            className={cn(
                              "w-3 h-3 rounded-full shadow-sm",
                              activeDet === idx ? "bg-white" : ""
                            )} 
                            style={activeDet === idx ? {} : { backgroundColor: getPathologyColor(det.pathology) }}
                          />
                          <span className="font-black text-sm">Dent {det.tooth}</span>
                        </div>
                        <span 
                          className={cn(
                            "text-[10px] font-black tracking-widest px-3 py-1.5 rounded-lg border",
                            activeDet === idx 
                              ? "bg-white/20 border-white/30 text-white" 
                              : "bg-slate-50 border-slate-200"
                          )}
                          style={activeDet === idx ? {} : { color: getPathologyColor(det.pathology) }}
                        >
                          {det.pathology.toUpperCase()}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION DÉTAILS MANUELS DANS LE RAPPORT */}
              {annotations.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
                    <Type size={12} />
                    Détails Cliniques Ajoutés
                  </h4>
                  <div className="space-y-2">
                    {annotations.map((ann) => (
                      <div key={ann.id} className="bg-indigo-50/50 border border-indigo-100 p-3 rounded-xl flex justify-between items-center group transition-all hover:border-indigo-300">
                        <span className="text-xs font-bold text-slate-700">{ann.text}</span>
                        <button 
                          onClick={() => setAnnotations(prev => prev.filter(a => a.id !== ann.id))}
                          className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all p-1"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="pt-6 border-t border-slate-100 sticky bottom-0 bg-white pb-2">
                <button className="w-full py-5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-[1.25rem] font-black tracking-widest shadow-xl shadow-indigo-100 transition-all active:scale-95 flex items-center justify-center gap-3 group">
                  <CheckCircle2 size={20} className="group-hover:scale-110 transition-transform" />
                  VALIDER ET ARCHIVER
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4 opacity-40">
              <div className="w-16 h-16 rounded-full bg-slate-50 flex items-center justify-center border-2 border-dashed border-slate-200">
                <Activity size={32} />
              </div>
              <p className="text-xs font-bold uppercase tracking-widest text-center">En attente d'imagerie...</p>
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
          background: #e2e8f0;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #cbd5e1;
        }
      `}</style>
    </div>
  );
};

export default PanoramicStudio;
