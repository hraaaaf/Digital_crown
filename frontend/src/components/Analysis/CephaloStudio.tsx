import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, ZoomIn, ZoomOut, Maximize, CheckCircle2, Loader2 } from 'lucide-react';

import { cephaloRepository, type Point as BackendPoint } from '../../services/cephaloRepository';

// --- NOMENCLATURE OFFICIELLE (19 POINTS) ---
const LANDMARK_LABELS: Record<string, string> = {
  "Sella (S)": "S",
  "Nasion (N)": "N",
  "Orbitale (Or)": "Or",
  "Porion (Po)": "Po",
  "Subspinale (Point A)": "A",
  "Supramentale (Point B)": "B",
  "Pogonion (Pog)": "Pog",
  "Menton (Me)": "Me",
  "Gnathion (Gn)": "Gn",
  "Gonion (Go)": "Go",
  "Lower Incisal Incision": "LII",
  "Upper Incisal Incision": "UII",
  "Upper Lip": "UL",
  "Lower Lip": "LL",
  "Subnasale": "Sn",
  "Soft Tissue Pogonion": "stPog",
  "Posterior Nasal Spine (PNS)": "PNS",
  "Anterior Nasal Spine (ANS)": "ANS",
  "Articulare (Ar)": "Ar"
};

interface Point { x: number; y: number; }
interface CephaloStudioProps {
  analysisId: number;
  imageUrl: string;
  initialLandmarks: Record<string, Point>;
  onUpdateSuccess?: () => void;
}

export const CephaloStudio: React.FC<CephaloStudioProps> = ({ 
  analysisId, 
  imageUrl, 
  initialLandmarks,
  onUpdateSuccess 
}) => {
  const [landmarks, setLandmarks] = useState<Record<string, Point>>(initialLandmarks);
  const [isSaving, setIsSaving] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Dimensions de travail IA (Source de vérité mathématique)
  const VIEWBOX_WIDTH = 800;
  const VIEWBOX_HEIGHT = 640;

  // Écouteur pour la touche Espace (Pan mode)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault();
        setIsSpacePressed(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // --- LOGIQUE DE DRAG-AND-DROP ---
  const handleDragEnd = (name: string, info: any) => {
    if (!workspaceRef.current) return;

    const rect = workspaceRef.current.getBoundingClientRect();
    
    // Calcul de la position relative dans le repère 800x640
    // On compense le zoom et le pan (déplacement) de l'affichage
    const x = ((info.point.x - rect.left) / (rect.width)) * VIEWBOX_WIDTH;
    const y = ((info.point.y - rect.top) / (rect.height)) * VIEWBOX_HEIGHT;

    setLandmarks(prev => ({
      ...prev,
      [name]: { x, y }
    }));
  };

  // --- SYNCHRONISATION VIA REPOSITORY ---
  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Conversion au format plat [ {id, x, y} ] pour le Backend
      const formattedLandmarks: BackendPoint[] = Object.entries(landmarks).map(([id, p]) => ({
        id,
        x: p.x,
        y: p.y
      }));

      await cephaloRepository.refineAnalysis(analysisId, {
        landmarks: formattedLandmarks
      });

      if (onUpdateSuccess) onUpdateSuccess();
      alert("Points cliniques validés. Mesures recalculées.");
    } catch (error) {
      console.error("Erreur de synchronisation Cephalo:", error);
      alert("Erreur lors de la validation de l'analyse.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      
      {/* 1. BARRE D'OUTILS STUDIO */}
      <div className="flex items-center justify-between bg-white/50 p-3 rounded-2xl border border-slate-200/60 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex bg-slate-100 rounded-xl p-1 gap-1">
            <button onClick={() => setZoom(prev => Math.min(prev + 0.2, 3))} className="p-2 hover:bg-white rounded-lg transition-all text-slate-600"><ZoomIn size={18}/></button>
            <button onClick={() => setZoom(prev => Math.max(prev - 0.2, 0.5))} className="p-2 hover:bg-white rounded-lg transition-all text-slate-600"><ZoomOut size={18}/></button>
            <button onClick={() => setZoom(1)} className="p-2 hover:bg-white rounded-lg transition-all text-slate-600"><Maximize size={18}/></button>
          </div>
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
            Zoom : {Math.round(zoom * 100)}%
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setLandmarks(initialLandmarks)}
            className="flex items-center gap-2 px-4 py-2 text-slate-500 hover:text-[#003380] font-bold text-sm transition-all"
          >
            <RefreshCw size={16} /> Réinitialiser
          </button>
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-6 py-2.5 bg-[#003380] hover:bg-blue-900 text-white rounded-xl font-black text-sm shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
          >
            {isSaving ? <Loader2 className="animate-spin" size={18}/> : <CheckCircle2 size={18} />}
            Valider l'Analyse
          </button>
        </div>
      </div>

      {/* 2. ZONE DE TRAVAIL (WORKSPACE) */}
      <div className="flex-1 relative bg-slate-900 rounded-[2rem] overflow-hidden border border-slate-200 shadow-inner flex items-center justify-center group">
        
        {/* SKELETON LOADER POUR L'IMAGE */}
        {!isImageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center z-20 bg-slate-900/50 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="animate-spin text-white" size={32} />
              <span className="text-white/70 text-xs font-bold tracking-widest uppercase">Chargement Radio...</span>
            </div>
          </div>
        )}

        <motion.div 
          ref={workspaceRef}
          className={`relative transition-colors duration-200 ease-out ${isSpacePressed ? 'cursor-grab active:cursor-grabbing' : 'cursor-crosshair'}`}
          style={{ 
            width: '100%', 
            height: '100%', 
            maxWidth: '800px', 
            maxHeight: '640px',
            scale: zoom,
            aspectRatio: '800 / 640'
          }}
          drag={isSpacePressed}
          dragConstraints={{ left: -600, right: 600, top: -600, bottom: 600 }}
          dragElastic={0.1}
          dragMomentum={false}
        >
          {/* IMAGE RADIO DE FOND */}
          <img 
            src={imageUrl} 
            alt="Cephalometric X-Ray" 
            onLoad={() => setIsImageLoaded(true)}
            className={`absolute inset-0 w-full h-full object-contain pointer-events-none select-none transition-opacity duration-500 ${isImageLoaded ? 'opacity-90' : 'opacity-0'}`}
          />

          {/* CALQUE SVG INTERACTIF */}
          <svg 
            viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
            className={`absolute inset-0 w-full h-full z-10 overflow-visible ${isSpacePressed ? 'pointer-events-none' : ''}`}
          >
            {Object.entries(landmarks).map(([name, point]) => (
              <g key={name}>
                {/* POINT DRAGGABLE (Framer Motion) */}
                <motion.circle
                  cx={point.x}
                  cy={point.y}
                  r={6}
                  fill="#4ade80"
                  stroke="white"
                  strokeWidth={2}
                  drag
                  dragMomentum={false}
                  onDragEnd={(_, info) => handleDragEnd(name, info)}
                  whileHover={{ scale: 1.5 }}
                  whileDrag={{ scale: 0.8, fill: "#22c55e" }}
                  className="cursor-move drop-shadow-[0_0_8px_rgba(74,222,128,0.6)]"
                />
                
                {/* LABEL DU POINT */}
                <text
                  x={point.x + 10}
                  y={point.y - 10}
                  className="fill-white text-[10px] font-black pointer-events-none select-none drop-shadow-md"
                  style={{ paintOrder: 'stroke', stroke: 'rgba(0,0,0,0.5)', strokeWidth: '2px' }}
                >
                  {LANDMARK_LABELS[name] || name}
                </text>
              </g>
            ))}
          </svg>
        </motion.div>

        {/* INDICATEUR D'AIDE */}
        <div className="absolute bottom-6 left-6 px-4 py-2 bg-black/40 backdrop-blur-md rounded-full text-[10px] font-bold text-white/80 uppercase tracking-widest pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
          Drag & Drop pour corriger les points
        </div>
      </div>
    </div>
  );
};