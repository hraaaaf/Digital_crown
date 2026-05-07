import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  confidence: number;
}

interface Finding {
  label: string;
  confidence: number;
  bbox: BoundingBox;
}

interface ToothObject {
  fdi_number: number;
  bbox: BoundingBox;
  findings: Finding[];
}

interface FullAnalysis {
  teeth: ToothObject[];
  general_findings: Finding[];
}

interface XRayCanvasProps {
  imgUrl: string;
  visionData: FullAnalysis | null;
  imgSize: { w: number, h: number } | null;
  onImgLoad: (e: React.SyntheticEvent<HTMLImageElement>) => void;
  filterString: string;
  activeDet: string | null;
  onHoverDet: (id: string | null) => void;
}

export const XRayCanvas: React.FC<XRayCanvasProps> = ({
  imgUrl,
  visionData,
  imgSize,
  onImgLoad,
  filterString,
  activeDet,
  onHoverDet
}) => {
  
  // Aplatir toutes les boîtes à dessiner pour faciliter le mapping SVG
  const displayItems = useMemo(() => {
    if (!visionData) return [];
    let items: Array<{ id: string, label: string, fdi?: number, bbox: BoundingBox, isParent: boolean }> = [];
    
    // Ajouter les dents et leurs pathologies
    visionData.teeth.forEach((tooth) => {
      // Boîte globale de la dent
      items.push({
        id: `tooth-${tooth.fdi_number}`,
        label: `Dent ${tooth.fdi_number}`,
        fdi: tooth.fdi_number,
        bbox: tooth.bbox,
        isParent: true
      });
      // Boîtes des pathologies internes
      tooth.findings.forEach((finding, fIdx) => {
        items.push({
          id: `finding-${tooth.fdi_number}-${fIdx}`,
          label: finding.label,
          fdi: tooth.fdi_number,
          bbox: finding.bbox,
          isParent: false
        });
      });
    });

    // Ajouter les findings généraux
    visionData.general_findings.forEach((gf, gIdx) => {
      items.push({
        id: `general-${gIdx}`,
        label: gf.label,
        bbox: gf.bbox,
        isParent: false
      });
    });

    return items;
  }, [visionData]);

  const getClinicalColor = (label: string, isParent: boolean) => {
    if (isParent) return 'rgba(255, 255, 255, 0.4)'; // Blanc translucide pour la dent globale
    
    const labelLower = label.toLowerCase();
    if (labelLower.includes('carie') || labelLower.includes('lésion') || labelLower.includes('kyste')) return '#EF4444'; // Rouge
    if (labelLower.includes('implant') || labelLower.includes('couronne') || labelLower.includes('restauration')) return '#10B981'; // Vert
    return '#F59E0B'; // Orange pour le reste (canal, sinus, etc.)
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-slate-950 rounded-[2rem] shadow-inner">
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
          {displayItems.map((item) => {
            const { x_min, y_min, x_max, y_max } = item.bbox;
            const width = Math.max(x_max - x_min, 1);
            const height = Math.max(y_max - y_min, 1);
            const color = getClinicalColor(item.label, item.isParent);
            const isActive = activeDet === item.id;
            
            return (
              <motion.g 
                key={item.id}
                initial={{ opacity: 0 }}
                animate={{ 
                  opacity: activeDet === null || isActive ? 1 : 0.3,
                  filter: isActive && !item.isParent ? `drop-shadow(0 0 8px ${color})` : 'none'
                }}
                transition={{ duration: 0.2 }}
                style={{ pointerEvents: item.isParent ? 'none' : 'auto', cursor: item.isParent ? 'default' : 'pointer' }}
                onMouseEnter={() => !item.isParent && onHoverDet(item.id)}
                onMouseLeave={() => !item.isParent && onHoverDet(null)}
              >
                {/* Boîte de Détection */}
                <rect 
                  x={x_min} 
                  y={y_min} 
                  width={width} 
                  height={height} 
                  fill={isActive && !item.isParent ? color : 'transparent'}
                  fillOpacity={isActive && !item.isParent ? 0.2 : 0}
                  stroke={color} 
                  strokeWidth={isActive ? Math.max(imgSize.w * 0.003, 3) : Math.max(imgSize.w * 0.001, 1)}
                  rx={imgSize.w * 0.002}
                  strokeDasharray={item.isParent ? "5,5" : "0"}
                  className="transition-all duration-300"
                />
                
                {/* Badge pour les findings ou le FDI global */}
                {!item.isParent && (
                  <foreignObject
                    x={x_min}
                    y={Math.max(0, y_min - Math.max(imgSize.h * 0.03, 25))}
                    width={Math.max(imgSize.w * 0.1, 100)}
                    height={Math.max(imgSize.h * 0.04, 30)}
                    className="overflow-visible"
                  >
                    <div 
                      className="inline-flex items-center justify-center px-2 py-0.5 rounded-md text-white font-black text-[10px] shadow-xl border border-white/20 transition-transform duration-300 whitespace-nowrap"
                      style={{ 
                        backgroundColor: color,
                        transform: isActive ? 'scale(1.1) translateY(-2px)' : 'scale(1)',
                        transformOrigin: 'bottom left'
                      }}
                    >
                      {item.fdi ? `${item.fdi} : ` : ''}{item.label}
                    </div>
                  </foreignObject>
                )}

                {item.isParent && item.fdi && (
                  <text
                    x={x_min + width / 2}
                    y={y_min - 5}
                    fill="rgba(255,255,255,0.7)"
                    fontSize={Math.max(imgSize.h * 0.02, 12)}
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    {item.fdi}
                  </text>
                )}
              </motion.g>
            );
          })}
        </svg>
      )}
    </div>
  );
};

