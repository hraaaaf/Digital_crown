import type { Dispatch, SetStateAction } from 'react';
import { motion } from 'framer-motion';
import type { Landmark } from '../cephaloShared';

const SOFT_TISSUE_IDS = new Set([
  'ul', 'll', 'sn', 'stpog', 'ls', 'li', 'prn', 'cm', 'g_soft', 'n_soft', 'a_soft', 'st', 'b_soft', 'pog_soft', 'me_soft', 'g-soft', 'n-soft'
]);

interface CephaloLandmarkReticlesProps {
  landmarks: Landmark[];
  /** Anatomical image-space bounds, not CSS/viewBox viewport pixels. */
  imageWidth: number;
  imageHeight: number;
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
  /** Optional atomic store command for rapid keyboard events. */
  onKeyboardNudgeLandmark?: (id: string, dx: number, dy: number, imageWidth: number, imageHeight: number) => void;
  onLandmarkDragPreview?: (preview: { id: string; x: number; y: number } | null) => void;
}

export const CephaloLandmarkReticles = ({
  landmarks,
  imageWidth,
  imageHeight,
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
  onKeyboardNudgeLandmark,
  onLandmarkDragPreview,
}: CephaloLandmarkReticlesProps) => {
  const P = palette;
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
              data-ceph03b-drag-handle={pt.id}
              tabIndex={0}
              role="button"
              aria-label={`Point anatomique ${pt.id}, flèches pour déplacer de 1 pixel image, Maj et flèches pour 10 pixels`}
              aria-keyshortcuts="ArrowUp ArrowDown ArrowLeft ArrowRight Shift+ArrowUp Shift+ArrowDown Shift+ArrowLeft Shift+ArrowRight"
              onKeyDown={e => {
                const key = e.key;
                if (key === 'Enter' || key === ' ') {
                  e.preventDefault();
                  e.stopPropagation();
                  onPointMouseDown?.(pt.id);
                  return;
                }
                if (key === 'Escape' && activeDragId === pt.id) {
                  e.preventDefault();
                  e.stopPropagation();
                  setActiveDragId(null);
                  setActiveDragPos(null);
                  onLandmarkDragPreview?.(null);
                  setMagnifier(m => ({ ...m, show: false }));
                  return;
                }
                const step = e.shiftKey ? 10 : 1;
                const delta = key === 'ArrowLeft' ? [-step, 0]
                  : key === 'ArrowRight' ? [step, 0]
                    : key === 'ArrowUp' ? [0, -step]
                      : key === 'ArrowDown' ? [0, step] : null;
                if (!delta || activeDragId || isCalibrating) return;
                e.preventDefault();
                e.stopPropagation();
                // In the clinical workspace prefer an atomic store command.
                // Read-modify-write from props can lose two same-tick keypresses.
                if (onKeyboardNudgeLandmark) {
                  onKeyboardNudgeLandmark(pt.id, delta[0], delta[1], imageWidth, imageHeight);
                  return;
                }
                // Standalone tracing fixtures retain a controlled-update fallback.
                const x = Math.max(0, Math.min(imageWidth, pt.x + delta[0]));
                const y = Math.max(0, Math.min(imageHeight, pt.y + delta[1]));
                if (x === pt.x && y === pt.y) return;
                onUpdateLandmarks(landmarks.map(item => item.id === pt.id
                  ? { ...item, x, y } : item));
              }}
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
                const preview = { id: pt.id, ...coords };
                setActiveDragPos(preview);
                onLandmarkDragPreview?.(preview);
                if (magnifierEnabled) setMagnifier({ x: coords.x, y: coords.y, show: true });
              }}
              onPointerUp={e => {
                if (activeDragId !== pt.id) return;
                e.stopPropagation();
                const coords = clientToSVG(e.clientX, e.clientY);
                setActiveDragId(null);
                setActiveDragPos(null);
                onLandmarkDragPreview?.(null);
                setMagnifier(m => ({ ...m, show: false }));
                if (coords) {
                  onUpdateLandmarks(
                    landmarks.map(l => l.id === pt.id ? { ...l, x: coords.x, y: coords.y } : l)
                  );
                }
              }}
              onPointerCancel={e => {
                if (activeDragId !== pt.id) return;
                e.stopPropagation();
                // A cancelled gesture is not a clinical edit; never persist its preview.
                setActiveDragId(null);
                setActiveDragPos(null);
                onLandmarkDragPreview?.(null);
                setMagnifier(m => ({ ...m, show: false }));
              }}
              onLostPointerCapture={() => {
                if (activeDragId !== pt.id) return;
                // OS/window interruption must not strand the point in dragging mode.
                setActiveDragId(null);
                setActiveDragPos(null);
                onLandmarkDragPreview?.(null);
                setMagnifier(m => ({ ...m, show: false }));
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

              {(isHovMetric || isDragged || isFocused) && (
                <text
                  x={dispX}
                  y={dispY}
                  dx="13"
                  dy="-13"
                  fontSize="10"
                  fontFamily="'IBM Plex Mono','JetBrains Mono',monospace"
                  fontWeight="900"
                  className="pointer-events-none select-none"
                  fill={P.text}
                  style={{ paintOrder: 'stroke', stroke: P.magnifierBg, strokeWidth: isPro ? '2px' : '3.5px' }}
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
