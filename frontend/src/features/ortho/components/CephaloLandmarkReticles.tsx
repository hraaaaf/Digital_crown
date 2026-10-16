import { useMemo, useState, type Dispatch, type SetStateAction } from 'react';
import { motion } from 'framer-motion';
import type { Landmark } from '../cephaloShared';
import { cephaloLabelFontSize, layoutCephaloLandmarkLabels, layoutCephaloAnatomicalLabels } from './cephaloLabelLayout';

const SOFT_TISSUE_IDS = new Set([
  'ul', 'll', 'sn', 'stpog', 'ls', 'li', 'prn', 'cm', 'g_soft', 'n_soft', 'a_soft', 'st', 'b_soft', 'pog_soft', 'me_soft', 'g-soft', 'n-soft'
]);

interface CephaloLandmarkReticlesProps {
  landmarks: Landmark[];
  /** Anatomical image-space bounds, not CSS/viewBox viewport pixels. */
  imageWidth: number;
  imageHeight: number;
  /** Display-only labels, enabled in the desktop embedded workbench only. */
  compactLabels?: boolean;
  unitsPerPixel?: number;
  labelViewport?: string;
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
  compactLabels = false,
  unitsPerPixel = 1,
  labelViewport = '',
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
  // DOM focus must be rendered even when the parent does not control focusedPointId.
  const [keyboardFocusedId, setKeyboardFocusedId] = useState<string | null>(null);
  const [hoveredPointId, setHoveredPointId] = useState<string | null>(null);
  const isHoverActive = !!hoveredMetric;
  const hoveredIds = new Set(hoveredMetric?.points.map(p => p.toLowerCase()) ?? []);
  const isPointHovered = (ptId: string) =>
    hoveredPointId === ptId || (isHoverActive && hoveredIds.has(ptId.toLowerCase()));
  const priorityId = activeDragId ?? keyboardFocusedId ?? focusedPointId ?? hoveredPointId ?? activePointId ?? null;
  const shownLabels = new Set<string>();
  for (const point of landmarks) {
    if (compactLabels || (isHoverActive && hoveredIds.has(point.id.toLowerCase()))
      || point.id === keyboardFocusedId || point.id === focusedPointId
      || point.id === activeDragId || point.id === hoveredPointId
      || point.id === activePointId) shownLabels.add(point.id);
  }
  const labelPositions = compactLabels ? new Map() : layoutCephaloLandmarkLabels(
    landmarks.map(point => activeDragPos?.id === point.id
      ? { ...point, x: activeDragPos.x, y: activeDragPos.y } : point),
    shownLabels, priorityId, imageWidth, imageHeight,
  );
  const anatomicalLabels = useMemo(() => compactLabels
    ? layoutCephaloAnatomicalLabels(
        landmarks.map(point => activeDragPos?.id === point.id
          ? { ...point, x: activeDragPos.x, y: activeDragPos.y } : point),
        labelViewport, unitsPerPixel, imageWidth,
      )
    : new Map(), [compactLabels, landmarks, activeDragPos, labelViewport, unitsPerPixel, imageWidth]);
  const labelFontSize = compactLabels
    ? 16 * Math.max(0.1, Math.min(unitsPerPixel, 30))
    : cephaloLabelFontSize(imageWidth, imageHeight);

  return (
    <>
      {!isCalibrating && baseOpacity > 0.08 && landmarks.map(pt => {
        const isSoft = SOFT_TISSUE_IDS.has(pt.id.toLowerCase());
        const isDragged = activeDragId === pt.id;
        const isActive = pt.id === activePointId;
        const isFocused = pt.id === focusedPointId || pt.id === keyboardFocusedId;
        const labelPosition = labelPositions.get(pt.id);
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
          : (isFocused || isActive ? 1 : (isHovMetric ? baseOpacity * 0.92 : baseOpacity * 0.50));

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
              data-ceph03b-keyboard-focused={isFocused ? 'true' : undefined}
              tabIndex={0}
              role="button"
              aria-label={`Point anatomique ${pt.id}, flèches pour déplacer de 1 pixel image, Maj et flèches pour 10 pixels`}
              aria-keyshortcuts="ArrowUp ArrowDown ArrowLeft ArrowRight Shift+ArrowUp Shift+ArrowDown Shift+ArrowLeft Shift+ArrowRight"
              onFocus={() => setKeyboardFocusedId(pt.id)}
              onBlur={() => setKeyboardFocusedId(previous => previous === pt.id ? null : previous)}
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
                setHoveredPointId(pt.id);
                if (!activeDragId && magnifierEnabled) {
                  setMagnifier({ x: pt.x, y: pt.y, show: true });
                }
              }}
              onPointerLeave={() => {
                setHoveredPointId(previous => previous === pt.id ? null : previous);
                if (!activeDragId) setMagnifier(m => ({ ...m, show: false }));
              }}
            >
              <circle cx={dispX} cy={dispY} r={20} fill="transparent" stroke="transparent" />
              {isFocused && (
                <g data-ceph03b-focus-ring={pt.id} pointerEvents="none">
                  <circle cx={dispX} cy={dispY} r={19} fill="none"
                    stroke="#0b1220" strokeWidth="7" vectorEffect="non-scaling-stroke" />
                  <circle cx={dispX} cy={dispY} r={19} fill="none"
                    stroke="#ffffff" strokeWidth="3.5" vectorEffect="non-scaling-stroke" />
                </g>
              )}
              <circle
                cx={dispX}
                cy={dispY}
                r={isFocused || isDragged ? 5 : 3.5}
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

              {!compactLabels && labelPosition && (
                <>
                <rect
                  data-ceph03b-label-background={pt.id}
                  x={labelPosition.x - labelFontSize * 0.18}
                  y={labelPosition.y - labelPosition.height}
                  width={labelPosition.width + labelFontSize * 0.36}
                  height={labelPosition.height + labelFontSize * 0.26}
                  rx={labelFontSize * 0.18}
                  fill="#07111f"
                  fillOpacity="0.92"
                  stroke="#e2e8f0"
                  strokeOpacity="0.65"
                  strokeWidth="1.25"
                  vectorEffect="non-scaling-stroke"
                  pointerEvents="none"
                />
                <text
                  data-ceph03b-landmark-label={pt.id}
                  data-cephalo-landmark-label={compactLabels ? pt.id : undefined}
                  x={labelPosition.x}
                  y={labelPosition.y}
                  fontSize={labelFontSize}
                  fontFamily="'IBM Plex Mono','JetBrains Mono',monospace"
                  fontWeight="900"
                  className="pointer-events-none select-none"
                  fill="#f8fafc"
                  style={{ paintOrder: 'stroke', stroke: '#07111f', strokeWidth: labelFontSize * 0.1 }}
                >
                  {pt.id}
                </text>
                </>
              )}
            </g>
          </motion.g>
        );
      })}
      {compactLabels && !isCalibrating && baseOpacity > 0.08 && (
        <g data-cephalo-anatomical-labels="true" pointerEvents="none">
          {landmarks.map(point => {
            const place = anatomicalLabels.get(point.id);
            if (!place) return null;
            const emphasized = point.id === activeDragId || point.id === activePointId
              || point.id === keyboardFocusedId || point.id === hoveredPointId;
            return (
              <g key={point.id}>
                {place.leaderNeeded && <line
                  data-cephalo-label-leader={point.id}
                  x1={place.sourceX} y1={place.sourceY}
                  x2={place.leaderEndX} y2={place.leaderEndY}
                  stroke={emphasized ? '#fef08a' : '#93c5fd'}
                  strokeOpacity={emphasized ? 0.50 : 0.18}
                  strokeWidth={emphasized ? 1.2 : 0.65}
                  vectorEffect="non-scaling-stroke"
                />}
                <text
                  data-ceph03b-landmark-label={point.id}
                  data-cephalo-landmark-label={point.id}
                  x={place.x}
                  y={place.y}
                  textAnchor="start"
                  fontSize={labelFontSize}
                  fontFamily="'IBM Plex Mono','JetBrains Mono',monospace"
                  fontWeight={emphasized ? 800 : 700}
                  className="select-none"
                  fill={emphasized ? '#fef08a' : '#f8fafc'}
                  style={{ paintOrder: 'stroke', stroke: '#0b1220', strokeWidth: '3px' }}
                >{point.id}</text>
              </g>
            );
          })}
        </g>
      )}
    </>
  );
};
