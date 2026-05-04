import React from 'react';
import { motion } from 'framer-motion';

interface Detection {
  tooth: number;
  pathology: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x_min, y_min, x_max, y_max]
}

interface XRayCanvasProps {
  imgUrl: string;
  detections: Detection[];
  imgSize: { w: number, h: number } | null;
  onImgLoad: (e: React.SyntheticEvent<HTMLImageElement>) => void;
  filterString: string;
  activeDet: number | null;
  onHoverDet: (idx: number | null) => void;
}

export const XRayCanvas: React.FC<XRayCanvasProps> = ({
  imgUrl,
  detections,
  imgSize,
  onImgLoad,
  filterString,
  activeDet,
  onHoverDet
}) => {
  
  // Tâche 5.1 : Logique de couleur (Rouge pour les pathologies, Émeraude pour les traitements/restaurations)
  const getClinicalColor = (pathology: string) => {
    const pathologies = ['Caries', 'Deep Caries', 'Periapical Lesion', 'Impacted'];
    const treatments = ['Implant', 'Crown', 'Endodontic', 'Restoration', 'Filling'];
    
    if (pathologies.includes(pathology)) return '#EF4444'; // Rouge Vif (Danger/Soin requis)
    if (treatments.includes(pathology)) return '#10B981'; // Émeraude (Stabilité/Existant)
    return '#6366F1'; // Indigo (Autre/Indéfini)
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-slate-950 rounded-xl">
      <img 
        src={imgUrl} 
        alt="OPG Analysis" 
        className="w-full h-full object-contain transition-all duration-700"
        style={{ filter: filterString }}
        onLoad={onImgLoad}
      />
      
      {imgSize && (
        <svg 
          className="absolute inset-0 w-full h-full pointer-events-none" 
          viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
          preserveAspectRatio="xMidYMid meet"
        >
          {detections?.map((det, idx) => {
            const [x_min, y_min, x_max, y_max] = det.bbox;
            const width = x_max - x_min;
            const height = y_max - y_min;
            const color = getClinicalColor(det.pathology);
            const isActive = activeDet === idx;
            
            return (
              <motion.g 
                key={idx}
                initial={{ opacity: 0 }}
                animate={{ 
                  opacity: activeDet === null || isActive ? 1 : 0.1,
                  filter: isActive ? 'drop-shadow(0 0 8px ' + color + ')' : 'none'
                }}
                transition={{ duration: 0.2 }}
                style={{ pointerEvents: 'auto', cursor: 'pointer' }}
                onMouseEnter={() => onHoverDet(idx)}
                onMouseLeave={() => onHoverDet(null)}
              >
                {/* Boîte de Détection SOTA */}
                <rect 
                  x={x_min} 
                  y={y_min} 
                  width={width} 
                  height={height} 
                  fill="transparent"
                  stroke={color} 
                  strokeWidth={isActive ? Math.max(imgSize.w * 0.003, 3) : Math.max(imgSize.w * 0.001, 1)}
                  rx={imgSize.w * 0.002}
                  className="transition-all duration-300"
                />
                
                {/* Overlay de sélection */}
                {isActive && (
                  <rect 
                    x={x_min} 
                    y={y_min} 
                    width={width} 
                    height={height} 
                    fill={color}
                    fillOpacity={0.15}
                    rx={imgSize.w * 0.002}
                  />
                )}

                {/* Badge FDI Haute Visibilité */}
                <foreignObject
                  x={x_min}
                  y={y_min - Math.max(imgSize.h * 0.03, 25)}
                  width={Math.max(imgSize.w * 0.05, 50)}
                  height={Math.max(imgSize.h * 0.04, 30)}
                >
                  <div 
                    className="inline-flex items-center justify-center px-2 py-0.5 rounded-md text-white font-black text-[11px] shadow-xl border border-white/20 transition-transform duration-300"
                    style={{ 
                      backgroundColor: color,
                      transform: isActive ? 'scale(1.2) translateY(-4px)' : 'scale(1)',
                    }}
                  >
                    {det.tooth}
                  </div>
                </foreignObject>
              </motion.g>
            );
          })}
        </svg>
      )}
    </div>
  );
};
