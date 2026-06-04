import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePanoramicStore, ANOMALY_TAXONOMY } from './stores/usePanoramicStore';
import type { AnomalyCategory } from './stores/usePanoramicStore';

interface BoundingBox {
  x_min: number; y_min: number; x_max: number; y_max: number; confidence: number;
}

interface EliteDetection {
  label: string; fdi: number; bbox: BoundingBox; confidence: number; rejected?: boolean;
}

interface FullAnalysis {
  detections: EliteDetection[];
}

interface XRayCanvasProps {
  imgUrl: string;
  visionData: FullAnalysis | null;
  imgSize: { w: number, h: number } | null;
  onImgLoad: (e: React.SyntheticEvent<HTMLImageElement>) => void;
  filterString: string;
  activeDet: string | null;
  onHoverDetection?: (id: string | null) => void;
}

const CATEGORY_COLORS: Record<AnomalyCategory, string> = {
  'Conservatrice': '#6366F1', // Indigo
  'Endodontie': '#EF4444',    // Rouge
  'Parodontie': '#10B981',    // Emeraude
  'Chirurgie': '#F59E0B',     // Ambre
  'Prothèse': '#EC4899',      // Rose
  'ATM/Sinus': '#8B5CF6'      // Violet
};

export const XRayCanvas: React.FC<XRayCanvasProps> = ({
  imgUrl, visionData, imgSize, onImgLoad, filterString, activeDet, onHoverDetection
}) => {
  const [popover, setPopover] = useState<{ screenX: number, screenY: number, fdi: number } | null>(null);
  const [activeCategory, setActiveCategory] = useState<AnomalyCategory>('Conservatrice');
  const [customInput, setCustomInput] = useState("");

  const { 
    toothAnomalies, toggleAnomaly, 
    multiSelectMode, startMultiSelect, finishMultiSelect, cancelMultiSelect 
  } = usePanoramicStore();

  const mapFdi = (x_rel: number, y_rel: number) => {
    const curvature = 0.15;
    const center_y = 0.52;
    const occlusal_y = curvature * Math.pow(x_rel - 0.5, 2) + center_y;
    const is_upper = y_rel < occlusal_y;
    const is_right_side = x_rel < 0.5;
    const quadrant = is_upper ? (is_right_side ? 1 : 2) : (is_right_side ? 4 : 3);
    const dist_from_center = Math.abs(x_rel - 0.5) * 2;
    let tooth_num;
    if (dist_from_center < 0.08) tooth_num = 1;
    else if (dist_from_center < 0.14) tooth_num = 2;
    else if (dist_from_center < 0.20) tooth_num = 3;
    else if (dist_from_center < 0.28) tooth_num = 4;
    else if (dist_from_center < 0.36) tooth_num = 5;
    else if (dist_from_center < 0.55) tooth_num = 6;
    else if (dist_from_center < 0.75) tooth_num = 7;
    else tooth_num = 8;
    return quadrant * 10 + tooth_num;
  };

  const handleSvgClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!imgSize) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x_rel = (e.clientX - rect.left) / rect.width;
    const y_rel = (e.clientY - rect.top) / rect.height;
    const fdi = mapFdi(x_rel, y_rel);
    
    if (multiSelectMode.active) {
      finishMultiSelect(fdi);
      return;
    }

    setPopover({ screenX: (x_rel * 100), screenY: (y_rel * 100), fdi });

    // Activate detection for this tooth in sidebar table
    if (visionData?.detections) {
      const idx = visionData.detections.findIndex(det => det.fdi === fdi);
      if (idx !== -1) {
        onHoverDetection?.(`det-${idx}`);
      }
    }
  };
  
  const displayItems = useMemo(() => {
    if (!visionData?.detections) return [];
    return visionData.detections.map((det, idx) => ({
      id: `det-${idx}`, label: det.label, fdi: det.fdi, bbox: det.bbox, confidence: det.confidence, rejected: det.rejected, isParent: false
    }));
  }, [visionData]);

  const getClinicalColor = (label: string) => {
    const labelLower = label.toLowerCase();
    if (labelLower.includes('carie') || labelLower.includes('lésion')) return '#EF4444';
    if (labelLower.includes('implant') || labelLower.includes('couronne')) return '#10B981';
    return '#6366F1';
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-slate-950 rounded-[2rem] shadow-inner">
      <img 
        src={imgUrl} alt="OPG" 
        className="w-full h-full object-contain transition-all duration-700"
        style={{ filter: filterString }}
        onLoad={onImgLoad}
      />
      
      {imgSize && (
        <svg 
          className="absolute inset-0 w-full h-full cursor-crosshair" 
          viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
          preserveAspectRatio="xMidYMid meet"
          onClick={handleSvgClick}
        >
          {/* Grille Dentaire (Quadrillage) */}
          {[1,2,3,4].flatMap(quad => [1,2,3,4,5,6,7,8].map(num => quad*10 + num)).map(fdi => {
            const is_upper = Math.floor(fdi / 10) <= 2;
            const is_right = Math.floor(fdi / 10) === 1 || Math.floor(fdi / 10) === 4;
            const num = fdi % 10;
            const dist_x = [0, 0.04, 0.11, 0.17, 0.24, 0.32, 0.45, 0.65, 0.85][num];
            const x_rel = is_right ? 0.5 - (dist_x / 2) : 0.5 + (dist_x / 2);
            const curvature = 0.15;
            const occlusal_y = curvature * Math.pow(x_rel - 0.5, 2) + 0.52;
            const y_rel = is_upper ? occlusal_y - 0.15 : occlusal_y + 0.15;

            const cx = x_rel * imgSize.w;
            const cy = y_rel * imgSize.h;
            
            return (
              <g key={`grid-${fdi}`} className="opacity-40 hover:opacity-100 transition-opacity pointer-events-none">
                <rect x={cx - imgSize.w * 0.015} y={cy - imgSize.h * 0.05} width={imgSize.w * 0.03} height={imgSize.h * 0.1} fill="transparent" stroke="rgba(255,255,255,0.3)" strokeWidth="1" strokeDasharray="4 4" rx="4" />
                <text x={cx} y={is_upper ? cy - imgSize.h * 0.06 : cy + imgSize.h * 0.06} fill="rgba(255,255,255,0.5)" fontSize={Math.max(imgSize.w * 0.01, 10)} textAnchor="middle" alignmentBaseline="middle" className="font-mono font-bold">{fdi}</text>
              </g>
            );
          })}

          {displayItems.map((item) => {
            const { x_min, y_min, x_max, y_max } = item.bbox;
            const width = Math.max(x_max - x_min, 1);
            const height = Math.max(y_max - y_min, 1);
            const color = item.rejected ? '#94a3b8' : getClinicalColor(item.label);
            const isActive = activeDet === item.id;
            
            return (
              <motion.g 
                key={item.id} 
                animate={{ opacity: item.rejected ? 0.3 : (activeDet === null || isActive ? 1 : 0.3) }}
                onMouseEnter={() => onHoverDetection?.(item.id)}
                onMouseLeave={() => onHoverDetection?.(null)}
                style={{ cursor: 'pointer', pointerEvents: 'all' }}
              >
                <rect 
                  x={x_min} y={y_min} width={width} height={height} 
                  fill={isActive && !item.rejected ? color : 'transparent'} fillOpacity={0.15}
                  stroke={color} strokeWidth={isActive ? 3 : (item.rejected ? 1 : 2)} strokeDasharray={item.rejected ? "4 4" : "none"} rx={4}
                />
                <foreignObject x={x_min} y={Math.max(0, y_min - 25)} width="200" height="30" className="overflow-visible pointer-events-none">
                  <div className="inline-flex px-2 py-0.5 rounded bg-slate-900/80 text-white font-black text-[9px] border border-white/10 whitespace-nowrap items-center gap-1">
                    {item.fdi}: {item.label}
                    {item.confidence && (
                      <span className="text-[7px] text-slate-400 font-mono bg-black/40 px-1 rounded">
                        {Math.round(item.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </foreignObject>
              </motion.g>
            );
          })}
          
          {/* Rendu manuel par spécialité */}
          {Object.entries(toothAnomalies).map(([fdiStr, anomalies]) => {
            const fdi = parseInt(fdiStr);
            const is_upper = Math.floor(fdi / 10) <= 2;
            const is_right = Math.floor(fdi / 10) === 1 || Math.floor(fdi / 10) === 4;
            const num = fdi % 10;
            const dist_x = [0, 0.04, 0.11, 0.17, 0.24, 0.32, 0.45, 0.65, 0.85][num];
            const x_rel = is_right ? 0.5 - (dist_x / 2) : 0.5 + (dist_x / 2);
            const curvature = 0.15;
            const occlusal_y = curvature * Math.pow(x_rel - 0.5, 2) + 0.52;
            const y_rel = is_upper ? occlusal_y - 0.15 : occlusal_y + 0.15;

            return (
              <foreignObject key={`manual-${fdi}`} x={x_rel * imgSize.w - 50} y={y_rel * imgSize.h - 10} width="100" height="100" className="overflow-visible pointer-events-none">
                <div className="flex flex-col gap-0.5 items-center">
                  <div className="bg-white/10 backdrop-blur-md text-white text-[8px] font-black px-1.5 rounded-full border border-white/20 mb-1">{fdi}</div>
                  {anomalies.map(aId => {
                    const def = ANOMALY_TAXONOMY.find(t => t.id === aId);
                    const label = def ? def.label : aId;
                    const color = def ? CATEGORY_COLORS[def.category] : '#4B5563'; // Slate-600 fallback
                    return (
                      <div key={aId} className="px-1.5 py-0.5 rounded text-[8px] font-bold text-white shadow-lg whitespace-nowrap" style={{ backgroundColor: color }}>
                        {label}
                      </div>
                    );
                  })}
                </div>
              </foreignObject>
            );
          })}
        </svg>
      )}

      {/* MODE MULTI-SÉLECTION ACTIF */}
      <AnimatePresence>
        {multiSelectMode.active && (
          <motion.div 
            initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 20, opacity: 0 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-indigo-600 text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-4 border border-white/20 z-[1001]"
          >
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center animate-pulse">
              <span className="font-black text-xs">{multiSelectMode.startFdi}</span>
            </div>
            <div className="text-sm font-bold">
              Sélectionnez la dent de fin pour <span className="underline">{ANOMALY_TAXONOMY.find(t => t.id === multiSelectMode.anomalyId)?.label}</span>
            </div>
            <button onClick={cancelMultiSelect} className="bg-white/10 hover:bg-white/20 p-2 rounded-xl transition-all">
              Annuler
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* POPOVER MENU D'ANOMALIES CATÉGORISÉ (DESIGN ELITE) */}
      {popover && !multiSelectMode.active && (
        <div 
          className="absolute z-[1000] bg-[#0B0F19]/90 backdrop-blur-3xl border border-white/10 p-0 rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden"
          style={{ left: `${popover.screenX}%`, top: `${popover.screenY}%`, width: '380px', transform: 'translate(-50%, -50%)' }}
        >
          {/* Header */}
          <div className="p-5 bg-gradient-to-b from-white/10 to-transparent border-b border-white/10 flex items-center justify-between">
            <div>
              <h3 className="text-white font-black tracking-[0.2em] text-xs uppercase">Diagnostic Clinique</h3>
              <p className="text-indigo-400 font-mono text-[10px] mt-1">Dent {popover.fdi} • Sélection</p>
            </div>
            <button onClick={() => setPopover(null)} className="text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 p-2 rounded-full transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
          
          {/* Tabs Spécialités */}
          <div className="flex bg-black/40 p-2 gap-2 overflow-x-auto custom-scrollbar border-b border-white/5">
            {(['Conservatrice', 'Endodontie', 'Parodontie', 'Chirurgie', 'Prothèse', 'ATM/Sinus'] as AnomalyCategory[]).map(cat => (
              <button 
                key={cat} onClick={() => setActiveCategory(cat)}
                className={`px-4 py-2 rounded-xl text-[10px] font-bold tracking-wide whitespace-nowrap transition-all border ${
                  activeCategory === cat 
                    ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.3)]' 
                    : 'bg-transparent text-slate-400 border-transparent hover:text-white hover:bg-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Liste des Anomalies */}
          <div className="p-5 max-h-[320px] overflow-y-auto custom-scrollbar flex flex-col gap-2">
            {/* Affichage des saisies manuelles pour cette dent */}
            {(toothAnomalies[popover.fdi] || [])
              .filter(aId => !ANOMALY_TAXONOMY.some(t => t.id === aId))
              .map(customText => (
                <button
                  key={customText}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleAnomaly(popover.fdi, customText);
                  }}
                  className="text-left px-4 py-3 text-[11px] font-bold rounded-2xl transition-all border group flex items-center justify-between bg-slate-700/50 border-slate-500 text-white"
                >
                  <span>{customText}</span>
                  <span className="text-[8px] bg-slate-600 px-1.5 py-0.5 rounded text-slate-300 uppercase tracking-tighter">Manuel</span>
                  <div className="w-2 h-2 rounded-full bg-slate-400" />
                </button>
            ))}

            {/* Taxonomie standard */}
            {ANOMALY_TAXONOMY.filter(a => a.category === activeCategory).map((anomaly) => {
              const isActive = (toothAnomalies[popover.fdi] || []).includes(anomaly.id);
              return (
                <button
                  key={anomaly.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (anomaly.isMultiTooth) {
                      startMultiSelect(popover.fdi, anomaly.id);
                      setPopover(null);
                    } else {
                      toggleAnomaly(popover.fdi, anomaly.id);
                    }
                  }}
                  className={`text-left px-5 py-3.5 text-[11px] font-bold rounded-2xl transition-all border group flex items-center justify-between ${
                    isActive 
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200 shadow-[inset_0_0_20px_rgba(99,102,241,0.15)]' 
                      : 'bg-white/[0.02] border-white/5 text-slate-300 hover:bg-white/[0.06] hover:border-white/20 hover:text-white'
                  }`}
                >
                  <span className="tracking-wide">{anomaly.label}</span>
                  {anomaly.isMultiTooth && (
                    <span className="text-[8px] bg-white/10 px-2 py-0.5 rounded-md text-slate-400 uppercase tracking-widest font-mono">Zone</span>
                  )}
                  {isActive && <div className="w-2.5 h-2.5 rounded-full bg-indigo-400 shadow-[0_0_10px_rgba(129,140,248,0.8)]" />}
                </button>
              );
            })}
          </div>
          
          {/* Saisie Manuelle */}
          <div className="p-3 bg-black/40 border-t border-white/10">
            <form onSubmit={(e) => {
              e.preventDefault();
              if (customInput.trim()) {
                toggleAnomaly(popover.fdi, customInput.trim());
                setCustomInput("");
              }
            }} className="flex gap-2">
              <input 
                type="text" 
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Saisie libre (ex: Fracture...)"
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 outline-none focus:border-indigo-500 transition-all"
              />
              <button 
                type="submit"
                disabled={!customInput.trim()}
                className="bg-indigo-600 disabled:opacity-50 text-white px-3 py-2 rounded-xl text-xs font-bold transition-all hover:bg-indigo-500"
              >
                Ajouter
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


