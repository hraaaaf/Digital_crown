import type { Dispatch, SetStateAction } from 'react';
import { motion } from 'framer-motion';
import type { Landmark } from '../cephaloShared';

const SOFT_TISSUE_IDS = new Set([
  'ul', 'll', 'sn', 'stpog', 'ls', 'li', 'prn', 'cm', 'g_soft', 'n_soft', 'a_soft', 'st', 'b_soft', 'pog_soft', 'me_soft', 'g-soft', 'n-soft'
]);

interface CephaloLandmarkReticlesProps {
  landmarks: Landmark[];
  isCalibrating: boolean;
  baseOpacity: number;
  activeDragId: string | null;
  activeDragPos: { id: string; x: number; y: number } | null;
  activePointId?: string | null;
  focusedPointId?: string | null;
  hoveredMetric?: { key: string; points: string[]; lines: string[] } | null;
  palette: { ptU: string; ptL: string; ptDefault: string; isolationDim: number };
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
  const isHoverActive = !!hoveredMetric;
  const isPointHovered = (ptId: string) =>
    !isHoverActive ||
    hoveredMetric!.points.map(p => p.toLowerCase()).includes(ptId.toLowerCase());

  return (
    <>
      {/* ══ RÉTICULES — Pointer Events natifs (v4.2) ══════════════════
          ────────────────────────────────────────────────────────────
          PRINCIPE FONDAMENTAL :
            Pendant le drag, cx/cy/x/y de TOUS les éléments du point
            utilisent dispX/dispY = activeDragPos (coordonnée SVG
            temps-réel calculée par getScreenCTM().inverse()).
            Jamais pt.x/pt.y pendant le drag.
          ────────────────────────────────────────────────────────────
          setPointerCapture : garantit que onPointerMove/Up continuent
          même si le curseur sort de la hitbox (drag rapide).
          ══════════════════════════════════════════════════════════ */}
      {!isCalibrating && baseOpacity > 0.08 && landmarks.map(pt => {
        const isSoft = SOFT_TISSUE_IDS.has(pt.id.toLowerCase());
        const isDragged = activeDragId === pt.id;
        const isActive = pt.id === activePointId;
        const isFocused = pt.id === focusedPointId;
        const isHovMetric = isPointHovered(pt.id);

        // Mode Isolation : masquer tout sauf le point draggé
        if (activeDragId && !isDragged) return null;

        // ── Position d'affichage ──────────────────────────────────
        // C'est ici que réside le correctif : pendant le drag,
        // on affiche à la position calculée par getScreenCTM,
        // pas à la position commitée (pt.x, pt.y).
        const dispX = isDragged && activeDragPos ? activeDragPos.x : pt.x;
        const dispY = isDragged && activeDragPos ? activeDragPos.y : pt.y;

        const baseColor = isSoft ? '#ff8a65'
          : pt.id.startsWith('U') ? P.ptU
            : pt.id.startsWith('L') ? P.ptL
              : P.ptDefault;
        const renderColor = (isActive || isFocused || isDragged) ? '#ffffff' : baseColor;

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
                // setPointerCapture : les événements continuent même hors hitbox
                (e.currentTarget as Element).setPointerCapture(e.pointerId);
                setActiveDragId(pt.id);
                onPointMouseDown?.(pt.id);
              }}
              onPointerMove={e => {
                if (activeDragId !== pt.id) return;
                e.stopPropagation();
                const coords = clientToSVG(e.clientX, e.clientY);
                if (!coords) return;
                // Mettre à jour la position d'affichage en temps réel
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
                  // Commit de la position finale dans le tableau landmarks
                  onUpdateLandmarks(
                    landmarks.map(l => l.id === pt.id ? { ...l, x: coords.x, y: coords.y } : l)
                  );
                }
              }}
              onPointerEnter={() => {
                if (!activeDragId && magnifierEnabled) {
                  setMagnifier({ x: pt.x, y: pt.y, show: true });
                }
              }}
              onPointerLeave={() => {
                if (!activeDragId) setMagnifier(m => ({ ...m, show: false }));
              }}
            >
              {/* Hitbox magnétique invisible r=20 */}
              <circle cx={dispX} cy={dispY} r={20} fill="transparent" stroke="transparent" />

              {/* Point visuel — cx/cy = dispX/dispY (suit le curseur) */}
              <circle cx={dispX} cy={dispY}
                r={isFocused || isDragged ? 4.5 : 2.5}
                fill={renderColor}
                vectorEffect="non-scaling-stroke" />

              {/* Halo de sélection */}
              {(isActive || isFocused || isDragged) && (
                <>
                  <circle cx={dispX} cy={dispY} r={9}
                    fill="none" stroke={renderColor}
                    strokeWidth="1.5" opacity="0.55"
                    vectorEffect="non-scaling-stroke" />
                  {isPro && (
                    <motion.circle cx={dispX} cy={dispY} r={15}
                      fill="none" stroke={renderColor} strokeWidth="0.8"
                      vectorEffect="non-scaling-stroke"
                      animate={{ opacity: [0.5, 0.08, 0.5] }}
                      transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }} />
                  )}
                </>
              )}

              {/* Étiquette — ancrée sur dispX/dispY */}
              {(isHovMetric || isDragged || isFocused) && (
                <text
                  x={dispX} y={dispY} dx="13" dy="-13"
                  fontSize="10"
                  fontFamily="'IBM Plex Mono','JetBrains Mono',monospace"
                  fontWeight="900"
                  className="pointer-events-none select-none fill-white"
                  style={!isPro
                    ? { paintOrder: 'stroke', stroke: 'rgba(0,0,0,0.85)', strokeWidth: '3.5px' }
                    : {}}
                >
                  {pt.id}
                </text>
              )}
            </g>
          </motion.g>
        );
      })}
    </>
  );
};
