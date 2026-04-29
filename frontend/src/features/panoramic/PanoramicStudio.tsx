import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, Loader2, Activity, ShieldAlert, CheckCircle2, History } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import { PanoramicHistory } from './PanoramicHistory';

export interface PanoramicStudioProps {
  patientId: number;
  patientName: string;
}

export const PanoramicStudio: React.FC<PanoramicStudioProps> = ({ patientId, patientName }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'studio' | 'history'>('studio');
  const [imgSize, setImgSize] = useState<{w: number, h: number} | null>(null);
  const [activeDet, setActiveDet] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSelectHistory = (analysis: any) => {
    setResult({
      id: analysis.id,
      file_url: `http://localhost:8000/${analysis.image_path}`,
      vision: analysis.detections_data,
      report: { narrative_report: analysis.report_narrative },
      created_at: analysis.created_at
    });
    setViewMode('studio');
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

  return (
    <div className="flex flex-col md:flex-row h-full gap-6 bg-slate-50/50 p-6">
      {/* Colonne Gauche : Workspace Visuel */}
      <div className="flex-1 flex flex-col gap-4">
        <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200/60 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              <Activity className="text-indigo-600" />
              Studio Panoramique IA - {patientName}
            </h2>
            <p className="text-sm text-slate-500 mt-1 font-medium">Analyse hiérarchique DENTEX (SOTA)</p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setViewMode(viewMode === 'studio' ? 'history' : 'studio')}
              className={cn(
                "flex items-center gap-2 px-5 py-3 rounded-xl font-bold transition-all border",
                viewMode === 'history' ? "bg-slate-800 text-white border-slate-800" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-200"
              )}
            >
              <History size={18} />
              {viewMode === 'history' ? 'Retour au Studio' : 'Historique'}
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
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-md shadow-indigo-200 transition-all active:scale-95 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
              {loading ? 'Analyse DENTEX...' : 'Nouvel Examen'}
            </button>
          </div>
        </div>

        <div className="flex-1 bg-slate-900 rounded-[2rem] overflow-hidden relative shadow-inner border-4 border-white flex items-center justify-center min-h-[500px]">
          {viewMode === 'history' ? (
            <div className="absolute inset-0 bg-white overflow-y-auto p-8">
              <PanoramicHistory patientId={patientId} onSelect={handleSelectHistory} />
            </div>
          ) : (
            <>
              {!result && !loading && (
                <div className="text-slate-500 font-mono text-sm tracking-widest flex flex-col items-center gap-4">
                  <Activity size={40} className="text-slate-700" />
                  AUCUNE RADIOGRAPHIE CHARGÉE
                </div>
              )}
              
              {loading && (
                <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                  <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
                  <p className="text-indigo-400 font-black tracking-[0.2em] animate-pulse">INFÉRENCE EN COURS</p>
                </div>
              )}

              {result && result.file_url && (
                <div className="relative w-full h-full p-4 flex items-center justify-center group">
                  <div 
                    className="relative flex items-center justify-center" 
                    style={{ 
                      maxHeight: '100%', 
                      maxWidth: '100%',
                      aspectRatio: imgSize ? `${imgSize.w} / ${imgSize.h}` : 'auto' 
                    }}
                  >
                    <img 
                      src={result.file_url} 
                      alt="Panoramique" 
                      className="w-full h-full object-contain rounded-xl shadow-2xl" 
                      style={{ filter: 'contrast(1.1) brightness(1.05)' }}
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
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: idx * 0.15, duration: 0.4, ease: "easeOut" }}
                              style={{
                                opacity: activeDet === null || activeDet === idx ? 1 : 0.2,
                                transition: 'opacity 0.3s ease'
                              }}
                            >
                              <rect 
                                x={x_min} 
                                y={y_min} 
                                width={width} 
                                height={height} 
                                fill={color} 
                                fillOpacity={activeDet === idx ? 0.4 : 0.15}
                                stroke={color} 
                                strokeWidth={activeDet === idx ? Math.max(imgSize.w * 0.004, 3) : Math.max(imgSize.w * 0.002, 2)}
                                rx={imgSize.w * 0.005}
                                className="transition-all duration-300"
                              />
                              <text 
                                x={x_min} 
                                y={y_min - (imgSize.h * 0.015)} 
                                fill={color}
                                fontSize={activeDet === idx ? Math.max(imgSize.h * 0.022, 16) : Math.max(imgSize.h * 0.018, 14)}
                                fontWeight="900"
                                style={{ 
                                  textShadow: '0px 2px 4px rgba(0,0,0,0.8)',
                                  transition: 'all 0.3s ease'
                                }}
                              >
                                DENT {det.tooth}
                              </text>
                            </motion.g>
                          );
                        })}
                      </svg>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Colonne Droite : Intelligence Clinique */}
      <div className="w-[400px] flex flex-col gap-4">
        <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200/60 p-6 flex-1 overflow-y-auto">
          <h3 className="text-sm font-black text-slate-400 tracking-[0.2em] mb-6 flex items-center gap-2 uppercase">
            <ShieldAlert size={16} />
            Diagnostic IA
          </h3>

          {result ? (
            <div className="space-y-6">
              {result.vision?.mode_inference === 'MOCK' && (
                <div className="bg-amber-50 text-amber-700 p-3 rounded-xl text-xs font-bold border border-amber-200 flex items-start gap-2">
                  <Activity size={16} className="mt-0.5 shrink-0" />
                  Mode Simulation (Poids PyTorch non détectés). Données cliniques générées à des fins de démonstration.
                </div>
              )}

              <div className="prose prose-sm prose-slate max-w-none">
                {result.report?.narrative_report?.split('\n').map((line: string, i: number) => (
                  <p key={i} className="mb-2 text-slate-700 font-medium leading-relaxed">
                    {line.startsWith('•') ? (
                      <span className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        <span>{line.replace('•', '').trim()}</span>
                      </span>
                    ) : line}
                  </p>
                ))}
              </div>

              {result.vision?.detections?.length > 0 && (
                <div className="mt-8 space-y-3">
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-4">Cartographie des anomalies</h4>
                  {result.vision.detections.map((det: any, idx: number) => (
                    <motion.div 
                      key={idx} 
                      onMouseEnter={() => setActiveDet(idx)}
                      onMouseLeave={() => setActiveDet(null)}
                      whileHover={{ scale: 1.02, x: 5 }}
                      className={`flex items-center justify-between p-3 rounded-xl border cursor-default transition-colors duration-300 ${activeDet === idx ? 'bg-white shadow-md border-indigo-200' : 'bg-slate-50 border-slate-100'}`}
                    >
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-3 h-3 rounded-full shadow-sm" 
                          style={{ backgroundColor: getPathologyColor(det.pathology) }}
                        />
                        <span className="font-bold text-slate-700">Dent {det.tooth}</span>
                      </div>
                      <span 
                        className="text-[11px] font-black tracking-wide px-2 py-1 rounded shadow-sm border"
                        style={{ 
                          color: getPathologyColor(det.pathology),
                          borderColor: getPathologyColor(det.pathology).replace('1)', '0.3)'),
                          backgroundColor: getPathologyColor(det.pathology).replace('1)', '0.05)')
                        }}
                      >
                        {det.pathology.toUpperCase()}
                      </span>
                    </motion.div>
                  ))}
                </div>
              )}
              
              {result.vision?.detections && (
                <div className="pt-6 mt-6 border-t border-slate-100">
                  <button className="w-full py-4 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-xl font-bold tracking-wide shadow-lg shadow-indigo-200 transition-all active:scale-95 flex items-center justify-center gap-2">
                    <CheckCircle2 size={18} />
                    VALIDER ET INTÉGRER AU DOSSIER
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4 opacity-50">
              <CheckCircle2 size={48} strokeWidth={1} />
              <p className="text-sm font-medium text-center">En attente d'imagerie pour générer le rapport clinique.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PanoramicStudio;
