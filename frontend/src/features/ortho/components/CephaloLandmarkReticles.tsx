import { useState, type Dispatch, type SetStateAction } from 'react';
import { motion } from 'framer-motion';
import type { Landmark } from '../cephaloShared';

// Only label presentation changes; full clinical IDs and point coordinates remain untouched.
const compactName=(id:string)=>id.replace(/_incisal$/i,'i').replace(/_apex$/i,'a')
 .replace(/_facial_surface$/i,'·f').replace(/_anatomic$/i,'·a')
 .replace(/_soft$/i,'·s').replace(/_ant$/i,'·ant').replace(/_post$/i,'·post');
type Candidate={dx:number;dy:number;anchor:'start'|'end'|'middle'};
const candidates:Candidate[]=[
 {dx:22,dy:-22,anchor:'start'},{dx:-22,dy:-22,anchor:'end'},
 {dx:22,dy:32,anchor:'start'},{dx:-22,dy:32,anchor:'end'},
 {dx:56,dy:8,anchor:'start'},{dx:-56,dy:8,anchor:'end'},
 {dx:0,dy:-50,anchor:'middle'},{dx:0,dy:55,anchor:'middle'},
 {dx:78,dy:-28,anchor:'start'},{dx:-78,dy:36,anchor:'end'},
 {dx:105,dy:3,anchor:'start'},{dx:-105,dy:3,anchor:'end'},
 {dx:56,dy:-70,anchor:'start'},{dx:-56,dy:78,anchor:'end'},
 {dx:116,dy:62,anchor:'start'},{dx:-116,dy:-62,anchor:'end'},
];
type Rect={left:number;right:number;top:number;bottom:number};
const overlap=(a:Rect,b:Rect)=>a.left<b.right+6&&a.right>b.left-6&&a.top<b.bottom+6&&a.bottom>b.top-6;
// Text-only collision avoidance. Never filters, reorders, or modifies any anatomical point.
// If no safe position exists, keep the marker and full <title> for hover/focus.
const labelLayout=(points:Landmark[],width:number,height:number):Map<string,Candidate>=>{
 const placed:Rect[]=[], result=new Map<string,Candidate>();
 const crowd=(p:Landmark)=>points.filter(q=>q!==p&&Math.hypot(p.x-q.x,p.y-q.y)<120).length;
 const order=[...points].sort((a,b)=>crowd(b)-crowd(a)||a.id.localeCompare(b.id));
 for(const point of order){
  const labelWidth=compactName(point.id).length*15.2;
  let best:Candidate|null=null,bestBox:Rect|null=null,min=Infinity;
  for(const [rank,c] of candidates.entries()){
   const x=point.x+c.dx,y=point.y+c.dy;
   const left=x-(c.anchor==='end'?labelWidth:c.anchor==='middle'?labelWidth/2:0);
   const box={left,right:left+labelWidth,top:y-25,bottom:y+6};
   if(box.left<6||box.top<6||box.right>width-6||box.bottom>height-6)continue;
   if(placed.some(p=>overlap(p,box)))continue;
   const pointIntersections=points.filter(p=>p!==point&&p.x>=box.left-9&&p.x<=box.right+9&&p.y>=box.top-9&&p.y<=box.bottom+9).length;
   const score=rank*2 + pointIntersections*170 + Math.hypot(c.dx,c.dy)*0.12;
   if(score<min){min=score;best=c;bestBox=box;}
  }
  if(best&&bestBox){result.set(point.id,best);placed.push(bestBox);}
 }
 return result;
};

const SOFT_TISSUE_IDS = new Set([
  'ul', 'll', 'sn', 'stpog', 'ls', 'li', 'prn', 'cm', 'g_soft', 'n_soft', 'a_soft', 'st', 'b_soft', 'pog_soft', 'me_soft', 'g-soft', 'n-soft'
]);

interface CephaloLandmarkReticlesProps {
  landmarks: Landmark[];
  imageWidth: number;
  imageHeight: number;
  compactLabels?: boolean;
  isCalibrating: boolean;
  baseOpacity: number;
  activeDragId: string | null;
  activeDragPos: { id: string; x: number; y: number } | null;
  activePointId?: string | null;
  focusedPointId?: string | null;
  hoveredMetric?: { key: string; points: string[]; lines: string[] } | null;
  palette: {
    ptU: string;
    ptL: string;
    ptDefault: string;
    ptSoft: string;
    ptFocus: string;
    text: string;
    magnifierBg: string;
    isolationDim: number;
  };
  isPro: boolean;
  setActiveDragId: Dispatch<SetStateAction<string | null>>;
  setActiveDragPos: Dispatch<SetStateAction<{ id: string; x: number; y: number } | null>>;
  magnifierEnabled: boolean;
  setMagnifier: Dispatch<SetStateAction<{ x: number; y: number; show: boolean }>>;
  clientToSVG: (clientX: number, clientY: number) => { x: number; y: number } | null;
  onPointMouseDown?: (id: string) => void;
  onUpdateLandmarks: (newLandmarks: Landmark[]) => void;
}

export const CephaloLandmarkReticles = ({
  landmarks,
  imageWidth,
  imageHeight,
  compactLabels = false,
  isCalibrating,
  baseOpacity,
  activeDragId,
  activeDragPos,
  activePointId,
  focusedPointId,
  hoveredMetric,
  palette,
  isPro,
  setActiveDragId,
  setActiveDragPos,
  magnifierEnabled,
  setMagnifier,
  clientToSVG,
  onPointMouseDown,
  onUpdateLandmarks,
}: CephaloLandmarkReticlesProps) => {
  const P = palette;
  const [hoveredPointId, setHoveredPointId] = useState<string | null>(null);
  const labelPositions = compactLabels ? labelLayout(landmarks, imageWidth, imageHeight) : null;
  const isHoverActive = !!hoveredMetric;
  const isPointHovered = (ptId: string) =>
    !isHoverActive || hoveredMetric!.points.map(p => p.toLowerCase()).includes(ptId.toLowerCase());

  return (
    <>
      {!isCalibrating && baseOpacity > 0.08 && landmarks.map(pt => {
        const isSoft = SOFT_TISSUE_IDS.has(pt.id.toLowerCase());
        const isDragged = activeDragId === pt.id;
        const isActive = pt.id === activePointId;
        const isFocused = pt.id === focusedPointId;
        const isHovMetric = isPointHovered(pt.id);

        if (activeDragId && !isDragged) return null;

        const dispX = isDragged && activeDragPos ? activeDragPos.x : pt.x;
        const dispY = isDragged && activeDragPos ? activeDragPos.y : pt.y;
        const labelPosition = labelPositions?.get(pt.id);
        const displayLabel = !compactLabels || Boolean(labelPosition) || isDragged || isFocused || hoveredPointId === pt.id;

        const baseColor = isSoft ? P.ptSoft
          : pt.id.startsWith('U') ? P.ptU
            : pt.id.startsWith('L') ? P.ptL
              : P.ptDefault;
        const renderColor = (isActive || isFocused || isDragged) ? P.ptFocus : baseColor;

        const ptOp = activeDragId
          ? (isDragged ? 1 : P.isolationDim)
          : (isHovMetric ? baseOpacity : baseOpacity * 0.42);

        const glowStyle = isPro && (isDragged || isFocused || isHovMetric)
          ? { filter: `drop-shadow(0 0 6px ${renderColor})` } : {};

        return (
          <motion.g
            key={pt.id}
            animate={{ opacity: ptOp }}
            transition={{ duration: 0.12 }}
          >
            <g
              style={{ pointerEvents: 'all', cursor: isDragged ? 'grabbing' : 'grab', ...glowStyle }}
              onPointerDown={e => {
                e.stopPropagation();
                (e.currentTarget as Element).setPointerCapture(e.pointerId);
                setActiveDragId(pt.id);
                onPointMouseDown?.(pt.id);
              }}
              onPointerMove={e => {
                if (activeDragId !== pt.id) return;
                e.stopPropagation();
                const coords = clientToSVG(e.clientX, e.clientY);
                if (!coords) return;
                setActiveDragPos({ id: pt.id, ...coords });
                if (magnifierEnabled) setMagnifier({ x: coords.x, y: coords.y, show: true });
              }}
              onPointerUp={e => {
                if (activeDragId !== pt.id) return;
                e.stopPropagation();
                const coords = clientToSVG(e.clientX, e.clientY);
                setActiveDragId(null);
                setActiveDragPos(null);
                setMagnifier(m => ({ ...m, show: false }));
                if (coords) {
                  onUpdateLandmarks(
                    landmarks.map(l => l.id === pt.id ? { ...l, x: coords.x, y: coords.y } : l)
                  );
                }
              }}
              onPointerEnter={() => {
                setHoveredPointId(pt.id);
                if (!activeDragId && magnifierEnabled) {
                  setMagnifier({ x: pt.x, y: pt.y, show: true });
                }
              }}
              onPointerLeave={() => {
                setHoveredPointId(current => current === pt.id ? null : current);
                if (!activeDragId) setMagnifier(m => ({ ...m, show: false }));
              }}
            >
              {compactLabels && <title>{pt.id}</title>}
              <circle cx={dispX} cy={dispY} r={20} fill="transparent" stroke="transparent" />
              <circle
                cx={dispX}
                cy={dispY}
                r={isFocused || isDragged ? 4.5 : 2.5}
                fill={renderColor}
                vectorEffect="non-scaling-stroke"
              />

              {(isActive || isFocused || isDragged) && (
                <>
                  <circle
                    cx={dispX}
                    cy={dispY}
                    r={9}
                    fill="none"
                    stroke={renderColor}
                    strokeWidth="1.5"
                    opacity="0.55"
                    vectorEffect="non-scaling-stroke"
                  />
                  {isPro && (
                    <motion.circle
                      cx={dispX}
                      cy={dispY}
                      r={15}
                      fill="none"
                      stroke={renderColor}
                      strokeWidth="0.8"
                      vectorEffect="non-scaling-stroke"
                      animate={{ opacity: [0.5, 0.08, 0.5] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                    />
                  )}
                </>
              )}

              {displayLabel && (isHovMetric || isDragged || isFocused) && (
                <text
                  data-cephalo-landmark-label={pt.id}
                  x={dispX + (labelPosition?.dx ?? 0)}
                  y={dispY + (labelPosition?.dy ?? 0)}
                  dx={labelPosition ? undefined : '13'}
                  dy={labelPosition ? undefined : '-13'}
                  textAnchor={labelPosition?.anchor}
                  fontSize={compactLabels ? 24 : 10}
                  fontFamily="'IBM Plex Mono','JetBrains Mono',monospace"
                  fontWeight="900"
                  className="pointer-events-none select-none"
                  fill={P.text}
                  style={{ paintOrder: 'stroke', stroke: P.magnifierBg, strokeWidth: isPro ? '2px' : '3.5px' }}
                >
                  {labelPosition ? compactName(pt.id) : pt.id}
                </text>
              )}
            </g>
          </motion.g>
        );
      })}
    </>
  );
};
