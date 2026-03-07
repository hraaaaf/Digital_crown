/**
 * CephaloTracingLayer.tsx  ·  v4.2  ·  Digital Crown
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * FIXES v4.2 — BUG DE DÉSALIGNEMENT POINT / CURSEUR
 * ───────────────────────────────────────────────────
 *
 *  CAUSE RACINE DU BUG (double problème) :
 *
 *  1. framer-motion <motion.g drag> applique pendant le drag un
 *     CSS `transform: translate(Δx, Δy)` sur le groupe entier.
 *     Mais cx/cy des <circle> restent fixés à pt.x/pt.y (coords commitées).
 *     ➜ Le cercle visuel flotte par rapport à sa position SVG réelle.
 *     ➜ Le commentaire originel "cx/cy = TOUJOURS pt.x/pt.y" était FAUX :
 *       c'est précisément ce choix qui créait le désalignement.
 *
 *  2. screenToSVG utilisait getBoundingClientRect + window.scrollX/Y.
 *     Cette méthode IGNORE le letterboxing SVG (preserveAspectRatio=xMidYMid).
 *     Si le ratio conteneur ≠ ratio image, l'offset calculé est décalé.
 *
 *  CORRECTIONS :
 *
 *  ✦ Suppression totale de framer-motion drag (motion.g drag, onDrag, onDragEnd,
 *    lastDragRef, screenToSVG, info.point).
 *
 *  ✦ Remplacement par Pointer Events natifs SVG :
 *      onPointerDown  → setPointerCapture (drag reste captif même hors hitbox)
 *      onPointerMove  → calcul coordonnées via getScreenCTM().inverse()
 *      onPointerUp    → commit final + onUpdateLandmarks
 *
 *  ✦ clientToSVG via svg.getScreenCTM().inverse() :
 *      Méthode canonique du W3C SVG. Prend en compte automatiquement :
 *      - viewBox + preserveAspectRatio (letterboxing)
 *      - CSS transforms sur l'élément et ses ancêtres
 *      - Zoom navigateur + scroll
 *      ➜ AUCUN calcul manuel de ratios / offsets.
 *
 *  ✦ Pendant le drag, le point est rendu à dispX/dispY = activeDragPos
 *    (coordonnée SVG temps-réel), PAS à pt.x/pt.y.
 *    ➜ Le pixel visuel EST la coordonnée SVG réelle. Zéro décalage.
 *
 * Architecture v4.2 (logique métier inchangée) :
 *   ✦ Tooth Engine     — AnatomicalTooth recalculé frame-by-frame
 *   ✦ Dual WedgeZone   — IMPA L1/Plan Mand + I/F U1/Francfort (pendant drag)
 *   ✦ Wedges statiques — zones de tolérance toujours visibles derrière dents
 *   ✦ Mode Isolation   — opacity 5% pendant drag
 *   ✦ Loupe SVG        — zoom ×3 pixel-perfect
 *   ✦ IDs backend      — Po Or N S A B Go Me U1_incisal U1_apex L1_incisal L1_apex
 *   ✦ Normes COM       — IMPA 90°±5° (comp 80-100°), I/F 107°±5° (comp 97-120°)
 * ─────────────────────────────────────────────────────────────────────────────
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

// ─────────────────────────────────────────────────────────────────────────────
// TYPES EXPORTÉS
// ─────────────────────────────────────────────────────────────────────────────

export interface Landmark {
  id: string;
  x: number;
  y: number;
}

export interface GhostData {
  landmarks: Landmark[];
  opacity:   number;
  color:     string;
}

// ─────────────────────────────────────────────────────────────────────────────
// PROPS
// ─────────────────────────────────────────────────────────────────────────────

export interface CephaloTracingLayerProps {
  imageSrc?:      string;
  imgFilters?:    { brightness: number; contrast: number; invert: boolean };
  landmarks:      Landmark[];
  baseOpacity?:   number;
  ghosts?:        GhostData[];
  imageWidth:     number;
  imageHeight:    number;
  onUpdateLandmarks:    (newLandmarks: Landmark[]) => void;
  activePointId?:       string | null;
  focusedPointId?:      string | null;
  onPointMouseDown?:    (id: string) => void;
  visualDebug?: {
    N_prime?:         [number, number];
    A_prime?:         [number, number];
    B_prime?:         [number, number];
    normative_zones?: Array<{
      cx: number; cy: number; rx: number; ry: number; rotation?: number;
    }>;
  } | null;
  isCalibrating?:        boolean;
  calibrationPoints?:    { x: number; y: number }[];
  onAddCalibrationPoint?: (x: number, y: number) => void;
  uiMode?:         'standard' | 'pro';
  hoveredMetric?:  { key: string; points: string[]; lines: string[] } | null;
  onEmptyAreaClick?: (x: number, y: number) => void;
  magnifierEnabled?: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// DESIGN TOKENS — alignés sur cephalo_engine.py
// ─────────────────────────────────────────────────────────────────────────────

const PALETTE = {
  pro: {
    francfort:     '#00f5ff',
    mandibule:     '#8b5cf6',
    mcNamara:      '#eab308',
    sn:            '#00f5ff',
    na:            '#eab308',
    nb:            '#eab308',
    ab:            '#8b5cf6',
    u1:            '#00f5ff',
    l1:            '#32cd32',
    ptDefault:     '#00f5ff',
    ptU:           '#00f5ff',
    ptL:           '#32cd32',
    magnifierBg:   '#050505',
    magnifierRing: '#00f5ff',
    crosshairCol:  '#32cd32',
    isolationDim:  0.05,
    wedgeNorm:     '#32cd32',
    wedgeComp:     '#eab308',
    wedgeSevere:   '#ef4444',
    wedgeNormLine: '#32cd32',
    wedgeU1Norm:   '#00f5ff',
    wedgeU1Comp:   '#eab308',
    wedgeU1Severe: '#ef4444',
  },
  standard: {
    francfort:     '#2563eb',
    mandibule:     '#3b82f6',
    mcNamara:      '#d97706',
    sn:            '#60a5fa',
    na:            '#d97706',
    nb:            '#d97706',
    ab:            '#6366f1',
    u1:            '#ef4444',
    l1:            '#22c55e',
    ptDefault:     '#f59e0b',
    ptU:           '#ef4444',
    ptL:           '#22c55e',
    magnifierBg:   '#0f172a',
    magnifierRing: '#2563eb',
    crosshairCol:  '#22c55e',
    isolationDim:  0.06,
    wedgeNorm:     '#22c55e',
    wedgeComp:     '#f59e0b',
    wedgeSevere:   '#ef4444',
    wedgeNormLine: '#16a34a',
    wedgeU1Norm:   '#2563eb',
    wedgeU1Comp:   '#d97706',
    wedgeU1Severe: '#ef4444',
  },
} as const;

type PaletteKey = keyof typeof PALETTE;

// ─────────────────────────────────────────────────────────────────────────────
// NORMES CLINIQUES — cephalo_engine.py strict
//   IMPA  : mean=90°, norm=±5°, comp=(80°,100°)   → plan mandibulaire Go→Me
//   I/F   : mean=107°, norm=±5°, comp=(97°,120°)  → plan de Francfort  Po→Or
// ─────────────────────────────────────────────────────────────────────────────

const IMPA_MEAN      = 90;
const IMPA_NORM_HALF = 5;
const IMPA_COMP_HALF = 10;

const IF_MEAN      = 107;
const IF_NORM_HALF = 5;
const IF_COMP_LOW  = 97;
const IF_COMP_HIGH = 120;
const IF_COMP_HALF = Math.max(IF_MEAN - IF_COMP_LOW, IF_COMP_HIGH - IF_MEAN);

// ─────────────────────────────────────────────────────────────────────────────
// MATH HELPERS
// ─────────────────────────────────────────────────────────────────────────────

const toRad = (deg: number) => (deg * Math.PI) / 180;
const toDeg = (rad: number) => (rad * 180) / Math.PI;

/**
 * Calcule la projection orthogonale d'un point P sur la ligne définie par A-B.
 * Retourne les coordonnées du projeté orthogonal P'.
 */
function projectPointOnLine(
  px: number, py: number,
  ax: number, ay: number,
  bx: number, by: number
): { x: number; y: number } | null {
  const dx = bx - ax;
  const dy = by - ay;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return null; // A et B sont confondus
  
  // Calcul du paramètre t de la projection
  const t = ((px - ax) * dx + (py - ay) * dy) / lenSq;
  
  // Coordonnées du projeté
  return {
    x: ax + t * dx,
    y: ay + t * dy,
  };
}

/**
 * Calcule les coordonnées d'un tiquet (petit trait) perpendiculaire à une ligne.
 * Le tiquet est centré sur le point donné et a une longueur totale définie.
 * 
 * @param cx - x du centre du tiquet
 * @param cy - y du centre du tiquet  
 * @param lineAngle - angle de la ligne de référence en degrés
 * @param tickLength - longueur totale du tiquet
 * @returns objet avec les coordonnées x1,y1 et x2,y2 du tiquet
 */
function getPerpendicularTick(
  cx: number, cy: number,
  lineAngle: number,
  tickLength: number = 16
): { x1: number; y1: number; x2: number; y2: number } {
  // Angle perpendiculaire = angle de la ligne + 90°
  const perpAngle = toRad(lineAngle + 90);
  const halfLen = tickLength / 2;
  
  return {
    x1: cx + halfLen * Math.cos(perpAngle),
    y1: cy + halfLen * Math.sin(perpAngle),
    x2: cx - halfLen * Math.cos(perpAngle),
    y2: cy - halfLen * Math.sin(perpAngle),
  };
}

function polarPoint(cx: number, cy: number, r: number, angleDeg: number) {
  return {
    x: cx + r * Math.cos(toRad(angleDeg)),
    y: cy + r * Math.sin(toRad(angleDeg)),
  };
}

/**
 * buildWedgePath — secteur angulaire SVG (anneau creux ou plein).
 * Clamp à ±359.99° pour éviter le cercle dégénéré (largeArc=1 + sweep=360 = invisible).
 */
function buildWedgePath(
  cx: number, cy: number,
  rOuter: number, rInner: number,
  startDeg: number, sweepDeg: number,
): string {
  const clamped  = Math.max(-359.99, Math.min(359.99, sweepDeg));
  const endDeg   = startDeg + clamped;
  const largeArc = Math.abs(clamped) >= 180 ? 1 : 0;
  const cw       = clamped >= 0 ? 1 : 0;

  const p1 = polarPoint(cx, cy, rOuter, startDeg);
  const p2 = polarPoint(cx, cy, rOuter, endDeg);

  if (rInner <= 0) {
    return [
      `M ${cx} ${cy}`,
      `L ${p1.x} ${p1.y}`,
      `A ${rOuter} ${rOuter} 0 ${largeArc} ${cw} ${p2.x} ${p2.y}`,
      'Z',
    ].join(' ');
  }

  const p3  = polarPoint(cx, cy, rInner, endDeg);
  const p4  = polarPoint(cx, cy, rInner, startDeg);
  const ccw = cw ^ 1;

  return [
    `M ${p1.x} ${p1.y}`,
    `A ${rOuter} ${rOuter} 0 ${largeArc} ${cw}  ${p2.x} ${p2.y}`,
    `L ${p3.x} ${p3.y}`,
    `A ${rInner} ${rInner} 0 ${largeArc} ${ccw} ${p4.x} ${p4.y}`,
    'Z',
  ].join(' ');
}

// ─────────────────────────────────────────────────────────────────────────────
// TOOTH ENGINE — AnatomicalTooth
// Recalculé intégralement chaque frame via transform SVG direct.
// Gabarit local (base 100px) : y=-52 incisal | y=0 cervical | y=+52 apex
// ─────────────────────────────────────────────────────────────────────────────

interface ToothProps {
  incisalPoint:    { x: number; y: number };
  apexPoint:       { x: number; y: number };
  color:           string;
  isHovered:       boolean;
  opacity?:        number;
  isGhost?:        boolean;
  isBeingDragged?: boolean;
  glowFilter?:     string;
}

const AnatomicalTooth: React.FC<ToothProps> = React.memo(({
  incisalPoint, apexPoint, color,
  isHovered, opacity = 1,
  isGhost = false, isBeingDragged = false,
  glowFilter,
}) => {
  const cx    = (incisalPoint.x + apexPoint.x) / 2;
  const cy    = (incisalPoint.y + apexPoint.y) / 2;
  const dx    = incisalPoint.x - apexPoint.x;
  const dy    = incisalPoint.y - apexPoint.y;
  const dist  = Math.sqrt(dx * dx + dy * dy);
  const s     = dist > 1 ? dist / 100 : 0.01;
  const angle = toDeg(Math.atan2(dy, dx)) - 90;

  const dash      = isGhost ? '7,4' : undefined;
  const fillAlpha = isGhost ? 0.04 : isBeingDragged ? 0.28 : 0.14;
  const swC       = isHovered && !isGhost ? 2.5 : 1.5;
  const swA       = isHovered && !isGhost ? 2.2 : 1.2;

  return (
    <g
      transform={`translate(${cx},${cy}) rotate(${angle}) scale(${s})`}
      opacity={opacity}
      style={{ pointerEvents: 'none', filter: isBeingDragged && !isGhost ? glowFilter : undefined }}
    >
      {/* Silhouette anatomique couronne */}
      <path
        d="M 0,-52 C 15,-52 22,-28 22,-4 C 22,20 11,44 0,52 C -11,44 -22,20 -22,-4 C -22,-28 -15,-52 0,-52 Z"
        fill={color} fillOpacity={fillAlpha}
        stroke={color} strokeWidth={swC} strokeDasharray={dash}
        vectorEffect="non-scaling-stroke"
      />
      {/* Jonction cervicale */}
      <line x1="-22" y1="0" x2="22" y2="0"
        stroke={color} strokeWidth="1"
        strokeDasharray={isGhost ? '5,3' : '3,3'}
        opacity="0.45" vectorEffect="non-scaling-stroke"
      />
      {/* Axe incisif infini */}
      <line x1="0" y1="-2000" x2="0" y2="2000"
        stroke={color} strokeWidth={swA}
        strokeDasharray={isGhost ? '6,5' : undefined}
        opacity="0.80" vectorEffect="non-scaling-stroke"
      />
      {!isGhost && (
        <>
          <polygon points="0,-62 -7,-50 7,-50" fill={color} fillOpacity="0.95" vectorEffect="non-scaling-stroke" />
          <circle cx="0" cy="-52" r="3" fill={color} opacity="0.9" vectorEffect="non-scaling-stroke" />
          <circle cx="0" cy="52"  r="2.8" fill={color} opacity="0.72" vectorEffect="non-scaling-stroke" />
        </>
      )}
    </g>
  );
});
AnatomicalTooth.displayName = 'AnatomicalTooth';

// ─────────────────────────────────────────────────────────────────────────────
// WEDGE ZONE — visualisation temps réel de l'angle (active pendant le drag)
// ─────────────────────────────────────────────────────────────────────────────

interface WedgeZoneProps {
  apexPt:    { x: number; y: number };
  incisalPt: { x: number; y: number };
  po:        { x: number; y: number };
  or_:       { x: number; y: number };
  label:     string;
  normMean:  number;
  normHalf:  number;
  compHalf:  number;
  colors: { norm: string; comp: string; severe: string; normLine: string };
}

const WedgeZone: React.FC<WedgeZoneProps> = React.memo(({
  apexPt, incisalPt, po, or_,
  label, normMean, normHalf, compHalf, colors,
}) => {
  const toothVec = { x: incisalPt.x - apexPt.x, y: incisalPt.y - apexPt.y };
  const frkVec   = { x: or_.x - po.x,            y: or_.y - po.y };
  const toothMag = Math.sqrt(toothVec.x ** 2 + toothVec.y ** 2);
  const frkMag   = Math.sqrt(frkVec.x  ** 2 + frkVec.y  ** 2);
  if (toothMag < 2 || frkMag < 2) return null;

  // Angle = 180 - angle_brut (convention cephalo_engine.py)
  const cosA  = Math.max(-1, Math.min(1,
    (toothVec.x * frkVec.x + toothVec.y * frkVec.y) / (toothMag * frkMag)
  ));
  const angle = 180 - (toDeg(Math.acos(cosA)) % 180);
  const delta = angle - normMean;

  const isNorm    = Math.abs(delta) <= normHalf;
  const isComp    = !isNorm && Math.abs(delta) <= compHalf;
  const fillColor = isNorm ? colors.norm : isComp ? colors.comp : colors.severe;

  const R          = Math.min(Math.max(toothMag * 0.85, 50), 130);
  const Rinner     = R * 0.34;
  const frkAngle   = toDeg(Math.atan2(frkVec.y, frkVec.x));
  const toothAngle = toDeg(Math.atan2(toothVec.y, toothVec.x));

  let sweep = toothAngle - frkAngle;
  while (sweep >  180) sweep -= 360;
  while (sweep < -180) sweep += 360;

  const normAxis  = frkAngle + (normMean - 90);
  const dCurrent  = buildWedgePath(apexPt.x, apexPt.y, R, Rinner, frkAngle, sweep);
  const dNorm     = buildWedgePath(apexPt.x, apexPt.y, R * 0.92, Rinner * 1.08, normAxis - normHalf, normHalf * 2);
  const dComp     = buildWedgePath(apexPt.x, apexPt.y, R, Rinner, normAxis - compHalf, compHalf * 2);
  const normEnd   = polarPoint(apexPt.x, apexPt.y, R * 1.12, normAxis);
  const labelPos  = polarPoint(apexPt.x, apexPt.y, R + 20, toothAngle);

  return (
    <g className="pointer-events-none">
      <path d={dComp} fill={colors.comp} fillOpacity="0.09"
        stroke={colors.comp} strokeWidth="0.8" strokeDasharray="3,2" vectorEffect="non-scaling-stroke" />
      <path d={dNorm} fill={colors.norm} fillOpacity="0.14"
        stroke={colors.norm} strokeWidth="0.9" vectorEffect="non-scaling-stroke" />
      <path d={dCurrent} fill={fillColor} fillOpacity="0.22"
        stroke={fillColor} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
      <line x1={apexPt.x} y1={apexPt.y} x2={normEnd.x} y2={normEnd.y}
        stroke={colors.normLine} strokeWidth="1.3" strokeDasharray="5,3"
        opacity="0.9" vectorEffect="non-scaling-stroke" />
      <circle cx={apexPt.x} cy={apexPt.y} r="4"
        fill={fillColor} fillOpacity="0.5" stroke={fillColor}
        strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <text x={labelPos.x} y={labelPos.y} fontSize="11"
        fontFamily="'IBM Plex Mono','JetBrains Mono',monospace" fontWeight="800"
        fill={fillColor} textAnchor="middle" dominantBaseline="middle"
        style={{ userSelect: 'none', pointerEvents: 'none' }}>
        {label} {angle.toFixed(1)}°
      </text>
    </g>
  );
});
WedgeZone.displayName = 'WedgeZone';

// ─────────────────────────────────────────────────────────────────────────────
// Points tissu mou non interactifs (vision_service.py)
// ─────────────────────────────────────────────────────────────────────────────

const SOFT_TISSUE_IDS = new Set(['ul', 'll', 'sn', 'pog_soft', 'prn', 'stpog']);

// ─────────────────────────────────────────────────────────────────────────────
// COMPOSANT PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

export const CephaloTracingLayer: React.FC<CephaloTracingLayerProps> = ({
  imageSrc,
  imgFilters,
  landmarks,
  baseOpacity = 1,
  ghosts = [],
  imageWidth,
  imageHeight,
  onUpdateLandmarks,
  activePointId,
  focusedPointId,
  onPointMouseDown,
  visualDebug,
  isCalibrating = false,
  calibrationPoints,
  onAddCalibrationPoint,
  uiMode = 'standard',
  hoveredMetric,
  onEmptyAreaClick,
  magnifierEnabled = true,
}) => {
  if (imageWidth === 0 || imageHeight === 0) return null;

  const P     = PALETTE[uiMode as PaletteKey];
  const isPro = uiMode === 'pro';

  // ── Refs ──────────────────────────────────────────────────────────────────
  const svgRef = useRef<SVGSVGElement>(null);

  // ── State ─────────────────────────────────────────────────────────────────
  /**
   * activeDragId  : ID du point en cours de drag
   * activeDragPos : position SVG temps-réel calculée via getScreenCTM()
   *
   * IMPORTANT : pendant le drag, les cercles SVG sont rendus à
   * dispX/dispY = activeDragPos (pas à pt.x/pt.y). C'est ce qui garantit
   * que le pixel visuel correspond exactement à la coordonnée SVG réelle.
   */
  const [activeDragId,  setActiveDragId]  = useState<string | null>(null);
  const [activeDragPos, setActiveDragPos] = useState<{ id: string; x: number; y: number } | null>(null);
  const [magnifier,     setMagnifier]     = useState<{ x: number; y: number; show: boolean }>(
    { x: 0, y: 0, show: false }
  );

  useEffect(() => {
    if (!magnifierEnabled && magnifier.show) setMagnifier(m => ({ ...m, show: false }));
  }, [magnifierEnabled]); // eslint-disable-line

  // ─────────────────────────────────────────────────────────────────────────
  // clientToSVG — conversion pixel-perfect via getScreenCTM().inverse()
  //
  // getScreenCTM() retourne la matrice de l'espace SVG user-space vers le
  // viewport écran. Son inverse transforme (clientX, clientY) en coordonnées
  // SVG, en tenant compte automatiquement de :
  //   - viewBox + preserveAspectRatio (letterboxing exact)
  //   - CSS transforms sur le SVG et ses ancêtres
  //   - Zoom navigateur / scroll
  //
  // Ne jamais utiliser getBoundingClientRect + scaling manuel.
  // ─────────────────────────────────────────────────────────────────────────

  const clientToSVG = useCallback((clientX: number, clientY: number): { x: number; y: number } | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const svgPt = pt.matrixTransform(ctm.inverse());
    return {
      x: Math.max(0, Math.min(imageWidth,  svgPt.x)),
      y: Math.max(0, Math.min(imageHeight, svgPt.y)),
    };
  }, [imageWidth, imageHeight]);

  // ─────────────────────────────────────────────────────────────────────────
  // GETPOINT — résolveur temps réel
  // Retourne activeDragPos pour le point draggé (pour lignes, dents, wedges)
  // ─────────────────────────────────────────────────────────────────────────

  const getPoint = useCallback((pts: Landmark[], id: string): Landmark | undefined => {
    const pt = pts.find(l => l.id === id || l.id.toLowerCase() === id.toLowerCase());
    if (pts === landmarks && pt && activeDragPos?.id === pt.id) {
      return { ...pt, x: activeDragPos.x, y: activeDragPos.y };
    }
    return pt;
  }, [landmarks, activeDragPos]);

  // ─────────────────────────────────────────────────────────────────────────
  // HOVER METRIC
  // ─────────────────────────────────────────────────────────────────────────

  const isHoverActive  = !!hoveredMetric;
  const isPointHovered = (ptId: string) =>
    !isHoverActive ||
    hoveredMetric!.points.map(p => p.toLowerCase()).includes(ptId.toLowerCase());
  const isLineHovered  = (lineId: string) =>
    isHoverActive &&
    hoveredMetric!.lines.map(l => l.toLowerCase()).includes(lineId.toLowerCase());

  // ─────────────────────────────────────────────────────────────────────────
  // CLICK HANDLER (calibration / empty area)
  // ─────────────────────────────────────────────────────────────────────────

  const handleSvgClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (activeDragId) return; // fin d'un drag → ignorer le click synthétique
    const coords = clientToSVG(e.clientX, e.clientY);
    if (!coords) return;
    if (isCalibrating && onAddCalibrationPoint) {
      onAddCalibrationPoint(coords.x, coords.y);
      return;
    }
    if (e.target === e.currentTarget && onEmptyAreaClick) {
      onEmptyAreaClick(coords.x, coords.y);
    }
  }, [clientToSVG, activeDragId, isCalibrating, onAddCalibrationPoint, onEmptyAreaClick]);

  // ─────────────────────────────────────────────────────────────────────────
  // LOUPE — positionnement adaptatif (évite les bords)
  // ─────────────────────────────────────────────────────────────────────────

  const MAG_R    = 80;
  const MAG_MAR  = 40;
  const MAG_ZOOM = 3;

  let magX = magnifier.x + MAG_MAR + MAG_R;
  if (magX + MAG_R > imageWidth)  magX = magnifier.x - MAG_MAR - MAG_R;
  if (magX - MAG_R < 0)           magX = MAG_R + MAG_MAR;
  let magY = magnifier.y + MAG_MAR + MAG_R;
  if (magY + MAG_R > imageHeight) magY = magnifier.y - MAG_MAR - MAG_R;
  if (magY - MAG_R < 0)           magY = MAG_R + MAG_MAR;

  // ─────────────────────────────────────────────────────────────────────────
  // CALQUE SQUELETTIQUE
  // ─────────────────────────────────────────────────────────────────────────

  const renderSkeletalLayer = (
    pts:           Landmark[],
    isGhost      = false,
    overrideColor?: string,
    layerOp      = 1,
  ) => {
    const po  = getPoint(pts, 'Po');
    const or_ = getPoint(pts, 'Or');
    const a   = getPoint(pts, 'A');
    const b   = getPoint(pts, 'B');
    const go  = getPoint(pts, 'Go');
    const me  = getPoint(pts, 'Me');
    const u1i = getPoint(pts, 'U1_incisal') ?? getPoint(pts, 'U1i');
    const u1a = getPoint(pts, 'U1_apex')    ?? getPoint(pts, 'U1a');
    const l1i = getPoint(pts, 'L1_incisal') ?? getPoint(pts, 'L1i');
    const l1a = getPoint(pts, 'L1_apex')    ?? getPoint(pts, 'L1a');

    const ghostDash = isGhost ? '6,4' : undefined;

    const seg = (
      p1: Landmark | undefined, p2: Landmark | undefined,
      lineKey: string, defColor: string,
      opts?: { dash?: string; op?: number },
    ) => {
      if (!p1 || !p2) return null;
      const c   = overrideColor ?? defColor;
      const isH = !isGhost && isLineHovered(lineKey);
      const sw  = isH ? 2.8 : 1.5;
      const op  = (opts?.op ?? 1) * layerOp;
      return (
        <motion.line
          key={`${lineKey}-${isGhost}`}
          x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
          stroke={c} strokeDasharray={opts?.dash ?? ghostDash}
          vectorEffect="non-scaling-stroke"
          animate={{ strokeWidth: sw, opacity: op }}
          transition={{ duration: 0.14 }}
          style={isH ? { filter: `drop-shadow(0 0 5px ${c})` } : {}}
        />
      );
    };

    const u1Active = !isGhost && (activeDragId === 'U1_incisal' || activeDragId === 'U1_apex');
    const l1Active = !isGhost && (activeDragId === 'L1_incisal' || activeDragId === 'L1_apex');
    const u1Glow   = isPro ? `drop-shadow(0 0 12px ${P.u1})` : undefined;
    const l1Glow   = isPro ? `drop-shadow(0 0 12px ${P.l1})` : undefined;

    // ── Wedge IMPA statique (zones de tolérance, toujours visibles) ────────
    // Référence : Plan Mandibulaire Go → Me (pas le plan de Francfort)
    // Axe idéal  : perpendiculaire au plan mand. → IMPA = 90°
    // Rendu AVANT AnatomicalTooth → derrière les incisives

    let wedgeCompPath: string | null = null;
    let wedgeNormPath: string | null = null;

    if (!isGhost && l1a && l1i && go && me) {
      const mandDx   = me.x - go.x;
      const mandDy   = me.y - go.y;
      const mandLen  = Math.sqrt(mandDx * mandDx + mandDy * mandDy);
      const toothDx  = l1i.x - l1a.x;
      const toothDy  = l1i.y - l1a.y;
      const toothLen = Math.sqrt(toothDx * toothDx + toothDy * toothDy);

      if (mandLen >= 2 && toothLen >= 2) {
        const mandAngle  = toDeg(Math.atan2(mandDy, mandDx));
        const toothAngle = toDeg(Math.atan2(toothDy, toothDx));

        // Choisir la perpendiculaire la plus proche de l'axe réel de la dent
        const perpA    = mandAngle - 90;
        const perpB    = mandAngle + 90;
        const angDiff  = (a2: number, b2: number) => {
          let d = ((a2 - b2) % 360 + 360) % 360;
          if (d > 180) d -= 360;
          return Math.abs(d);
        };
        const idealAxis = angDiff(toothAngle, perpA) <= angDiff(toothAngle, perpB) ? perpA : perpB;

        const R      = Math.min(Math.max(toothLen * 0.80, 40), 110);
        const Rinner = R * 0.30;

        wedgeCompPath = buildWedgePath(l1a.x, l1a.y, R, Rinner,
          idealAxis - IMPA_COMP_HALF, IMPA_COMP_HALF * 2);
        wedgeNormPath = buildWedgePath(l1a.x, l1a.y, R * 0.90, Rinner * 1.05,
          idealAxis - IMPA_NORM_HALF, IMPA_NORM_HALF * 2);
      }
    }

    const wNorm = overrideColor ?? P.wedgeNorm;
    const wComp = overrideColor ?? P.wedgeComp;

    return (
      <g key={isGhost ? `ghost-${layerOp}` : 'main-layer'}>
        {/* Plans de référence */}
        {seg(po, or_, 'fh', P.francfort)}
        {seg(go, me,  'mp', P.mandibule)}
        {/* Note: Les lignes S-N, N-A, N-B (analyse de Steiner) ont été supprimées
            pour se concentrer sur l'analyse McNamara et les normes COM */}
        {seg(a,  b,   'ab', P.ab,  { dash: isGhost ? '6,4' : '2,3', op: 0.50 })}

        {/* Secteur JAUNE compensation ±10° — en premier = derrière */}
        {wedgeCompPath && (
          <path d={wedgeCompPath} fill={wComp} fillOpacity="0.10"
            stroke={wComp} strokeWidth="0.9" strokeDasharray="4,2"
            vectorEffect="non-scaling-stroke" className="pointer-events-none" />
        )}
        {/* Secteur VERT norme ±5° — en second = devant le jaune */}
        {wedgeNormPath && (
          <path d={wedgeNormPath} fill={wNorm} fillOpacity="0.20"
            stroke={wNorm} strokeWidth="1.1"
            vectorEffect="non-scaling-stroke" className="pointer-events-none" />
        )}

        {/* Incisive supérieure U1 */}
        {u1i && u1a && (
          <AnatomicalTooth incisalPoint={u1i} apexPoint={u1a}
            color={overrideColor ?? P.u1}
            isHovered={!isGhost && isLineHovered('u1')}
            opacity={layerOp} isGhost={isGhost}
            isBeingDragged={u1Active} glowFilter={u1Glow} />
        )}
        {/* Incisive inférieure L1 */}
        {l1i && l1a && (
          <AnatomicalTooth incisalPoint={l1i} apexPoint={l1a}
            color={overrideColor ?? P.l1}
            isHovered={!isGhost && isLineHovered('l1')}
            opacity={layerOp} isGhost={isGhost}
            isBeingDragged={l1Active} glowFilter={l1Glow} />
        )}
      </g>
    );
  };

  // ─────────────────────────────────────────────────────────────────────────
  // PLAN DE FRANCFORT ÉTENDU (pour voir les projections A', B')
  // ─────────────────────────────────────────────────────────────────────────
  
  const po = getPoint(landmarks, 'Po');
  const or_ = getPoint(landmarks, 'Or');
  
  // Plan de Francfort étendu à l'infini pour les projections
  let francfortLineExtended: { x1: number; y1: number; x2: number; y2: number } | null = null;
  if (po && or_) {
    const dx = or_.x - po.x;
    const dy = or_.y - po.y;
    francfortLineExtended = {
      x1: po.x - dx * 10, y1: po.y - dy * 10,
      x2: or_.x + dx * 10, y2: or_.y + dy * 10,
    };
  }

  // PROJECTIONS McNAMARA (N', A', B') - calculées en temps réel côté frontend
  // pour rester synchronisées quand les landmarks bougent
  const n0 = getPoint(landmarks, 'N');
  const ptA = getPoint(landmarks, 'A');
  const ptB = getPoint(landmarks, 'B');
  
  // Calcul de l'angle du plan de Francfort (pour les tiquets perpendiculaires)
  const francfortAngle = (po && or_) ? toDeg(Math.atan2(or_.y - po.y, or_.x - po.x)) : 0;
  
  // Calcul de N' (projection de N sur le plan de Francfort)
  const nPrime = (po && or_ && n0) 
    ? projectPointOnLine(n0.x, n0.y, po.x, po.y, or_.x, or_.y)
    : null;
  
  // Calcul de A' (projection de A sur le plan de Francfort)
  const aPrime = (po && or_ && ptA)
    ? projectPointOnLine(ptA.x, ptA.y, po.x, po.y, or_.x, or_.y)
    : null;
  
  // Calcul de B' (projection de B sur le plan de Francfort)
  const bPrime = (po && or_ && ptB)
    ? projectPointOnLine(ptB.x, ptB.y, po.x, po.y, or_.x, or_.y)
    : null;
  
  // LIGNE McNAMARA (perpendiculaire au plan de Francfort passant par N')
  let mcNamaraLine: { x1: number; y1: number; x2: number; y2: number } | null = null;
  if (n0 && nPrime) {
    const dx = nPrime.x - n0.x;
    const dy = nPrime.y - n0.y;
    mcNamaraLine = {
      x1: n0.x - dx * 1000, y1: n0.y - dy * 1000,
      x2: n0.x + dx * 1000, y2: n0.y + dy * 1000,
    };
  }
  
  // Tiquets perpendiculaires pour N', A', B' (style premium)
  const nPrimeTick = nPrime ? getPerpendicularTick(nPrime.x, nPrime.y, francfortAngle, 14) : null;
  const aPrimeTick = aPrime ? getPerpendicularTick(aPrime.x, aPrime.y, francfortAngle, 14) : null;
  const bPrimeTick = bPrime ? getPerpendicularTick(bPrime.x, bPrime.y, francfortAngle, 14) : null;

  // ─────────────────────────────────────────────────────────────────────────
  // WEDGE ZONES dynamiques (pendant drag)
  // ─────────────────────────────────────────────────────────────────────────
  // CORRECTION: L'IMPA utilise le PLAN MANDIBULAIRE (Go→Me), pas le plan Francfort!
  // L'I/F utilise le plan Francfort (Po→Or)
  // ─────────────────────────────────────────────────────────────────────────

  const dragId     = activeDragId ?? '';
  const l1Dragged  = ['L1_incisal', 'L1_apex', 'L1i', 'L1a'].includes(dragId);
  const u1Dragged  = ['U1_incisal', 'U1_apex', 'U1i', 'U1a'].includes(dragId);
  const frkDragged = dragId === 'Po' || dragId === 'Or';
  const mandDragged = dragId === 'Go' || dragId === 'Me';

  const wL1i = (l1Dragged || frkDragged || mandDragged) ? (getPoint(landmarks, 'L1_incisal') ?? getPoint(landmarks, 'L1i')) : null;
  const wL1a = (l1Dragged || frkDragged || mandDragged) ? (getPoint(landmarks, 'L1_apex')    ?? getPoint(landmarks, 'L1a')) : null;
  const wU1i = (u1Dragged || frkDragged) ? (getPoint(landmarks, 'U1_incisal') ?? getPoint(landmarks, 'U1i')) : null;
  const wU1a = (u1Dragged || frkDragged) ? (getPoint(landmarks, 'U1_apex')    ?? getPoint(landmarks, 'U1a')) : null;
  const wPo  = (u1Dragged || frkDragged) ? getPoint(landmarks, 'Po') : null;
  const wOr  = (u1Dragged || frkDragged) ? getPoint(landmarks, 'Or') : null;
  // IMPA utilise Go et Me (plan mandibulaire), pas Po/Or!
  const wGo  = (l1Dragged || mandDragged) ? getPoint(landmarks, 'Go') : null;
  const wMe  = (l1Dragged || mandDragged) ? getPoint(landmarks, 'Me') : null;

  const showIMPA = !!(wL1i && wL1a && wGo && wMe);
  const showIF   = !!(wU1i && wU1a && wPo && wOr);

  // Mode isolation : opacité réduite pendant drag
  const skeletalOp = activeDragId ? P.isolationDim : baseOpacity;

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="absolute inset-0 w-full h-full z-20">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${imageWidth} ${imageHeight}`}
        preserveAspectRatio="xMidYMid meet"
        className={cn('w-full h-full', isCalibrating ? 'cursor-crosshair' : 'cursor-default')}
        onClick={handleSvgClick}
        onPointerMove={e => {
          // Loupe passive (hors drag — le drag a son propre handler sur le g)
          if (!magnifierEnabled || activeDragId) return;
          const coords = clientToSVG(e.clientX, e.clientY);
          if (coords) setMagnifier({ x: coords.x, y: coords.y, show: true });
        }}
        onPointerLeave={() => {
          if (!activeDragId) setMagnifier(m => ({ ...m, show: false }));
        }}
      >
        {/* ── DEFS ──────────────────────────────────────────────────── */}
        <defs>
          <clipPath id="cephalo-mag-clip">
            <circle cx={magX} cy={magY} r={MAG_R} />
          </clipPath>
          {isPro && (
            <filter id="dc-glow-pro" x="-80%" y="-80%" width="260%" height="260%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          )}
        </defs>

        {/* ══ IMAGE DE FOND ═══════════════════════════════════════════
            Radiographie céphalométrique - rendue en premier (arrière-plan)
            ══════════════════════════════════════════════════════════ */}
        {imageSrc && (
          <image
            href={imageSrc}
            x={0}
            y={0}
            width={imageWidth}
            height={imageHeight}
            preserveAspectRatio="none"
            style={{
              filter: imgFilters ? [
                `brightness(${imgFilters.brightness ?? 100}%)`,
                `contrast(${imgFilters.contrast ?? 100}%)`,
                `invert(${imgFilters.invert ? 100 : 0}%)`,
              ].join(' ') : undefined,
            }}
          />
        )}

        {/* ══ CALQUE SQUELETTIQUE ═══════════════════════════════════════
            Atténué à P.isolationDim pendant tout drag (Mode Isolation)
            ══════════════════════════════════════════════════════════ */}
        <motion.g animate={{ opacity: skeletalOp }} transition={{ duration: 0.10 }}>
          {ghosts.map(g => renderSkeletalLayer(g.landmarks, true, g.color, g.opacity))}
          {renderSkeletalLayer(landmarks, false, undefined, baseOpacity)}

          <g opacity={baseOpacity}>
            {isPro && visualDebug?.normative_zones?.map((z, i) => (
              <ellipse key={`zone-${i}`}
                cx={z.cx} cy={z.cy} rx={z.rx} ry={z.ry}
                fill="rgba(0,245,255,0.04)" stroke="#00f5ff"
                strokeWidth="0.5" strokeDasharray="2,2"
                transform={`rotate(${z.rotation ?? 0},${z.cx},${z.cy})`}
                vectorEffect="non-scaling-stroke" className="pointer-events-none" />
            ))}
            {/* Ligne de Référence - Plan de Francfort étendu */}
            {francfortLineExtended && (
              <line
                x1={francfortLineExtended.x1} y1={francfortLineExtended.y1}
                x2={francfortLineExtended.x2} y2={francfortLineExtended.y2}
                stroke="#ff6b6b"
                strokeWidth="1.5"
                opacity="0.6"
                strokeDasharray="10,5"
                vectorEffect="non-scaling-stroke" />
            )}
          </g>
        </motion.g>

        {/* ══ PROJECTIONS A' ET B' + LIGNE McNAMARA ═══════════════════════
            Toujours visibles, hors du groupe à opacité variable
            ═══════════════════════════════════════════════════════════ */}
        
        {/* Ligne McNamara (perpendiculaire au plan de Francfort par N') */}
        {mcNamaraLine && nPrime && nPrimeTick && (
          <g>
            {/* Ligne McNamara subtile */}
            <line
              x1={mcNamaraLine.x1} y1={mcNamaraLine.y1}
              x2={mcNamaraLine.x2} y2={mcNamaraLine.y2}
              stroke="#ff00ff" 
              strokeWidth="1.5"
              strokeDasharray="8,4"
              opacity="0.7"
              vectorEffect="non-scaling-stroke" />
            {/* Tiquet perpendiculaire pour N' */}
            <line
              x1={nPrimeTick.x1} y1={nPrimeTick.y1}
              x2={nPrimeTick.x2} y2={nPrimeTick.y2}
              stroke="#ff00ff"
              strokeWidth="2"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke" />
            {/* Label McNamara */}
            <text
              x={nPrime.x + 20} y={nPrime.y - 15}
              fontSize="12" 
              fontWeight="600"
              fill="#ff00ff"
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              McNamara
            </text>
          </g>
        )}
        
        {/* Projection A → A' */}
        {aPrime && ptA && aPrimeTick && (
          <g>
            {/* Ligne de projection A → A' */}
            <line
              x1={ptA.x} y1={ptA.y}
              x2={aPrime.x} y2={aPrime.y}
              stroke="#ff0000" 
              strokeDasharray="5,5" 
              strokeWidth="2"
              opacity="0.8"
              vectorEffect="non-scaling-stroke" />
            {/* Tiquet perpendiculaire premium */}
            <line
              x1={aPrimeTick.x1} y1={aPrimeTick.y1}
              x2={aPrimeTick.x2} y2={aPrimeTick.y2}
              stroke="#ff0000"
              strokeWidth="2.5"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke" />
            {/* Label A' */}
            <text
              x={aPrime.x + 18} y={aPrime.y - 12}
              fontSize="14" 
              fontWeight="bold"
              fill="#ff0000"
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              A'
            </text>
          </g>
        )}
        
        {/* Projection B → B' */}
        {bPrime && ptB && bPrimeTick && (
          <g>
            {/* Ligne de projection B → B' */}
            <line
              x1={ptB.x} y1={ptB.y}
              x2={bPrime.x} y2={bPrime.y}
              stroke="#00ff00" 
              strokeDasharray="5,5" 
              strokeWidth="2"
              opacity="0.8"
              vectorEffect="non-scaling-stroke" />
            {/* Tiquet perpendiculaire premium */}
            <line
              x1={bPrimeTick.x1} y1={bPrimeTick.y1}
              x2={bPrimeTick.x2} y2={bPrimeTick.y2}
              stroke="#00ff00"
              strokeWidth="2.5"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke" />
            {/* Label B' */}
            <text
              x={bPrime.x + 18} y={bPrime.y - 12}
              fontSize="14" 
              fontWeight="bold"
              fill="#00ff00"
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              B'
            </text>
          </g>
        )}

        {/* ══ WEDGES DYNAMIQUES (pendant drag) ═══════════════════════════
            Hors du motion.g d'isolation → toujours à 100% d'opacité
            ══════════════════════════════════════════════════════════ */}
        {showIMPA && (
          <WedgeZone apexPt={wL1a!} incisalPt={wL1i!} po={wGo!} or_={wMe!}
            label="IMPA" normMean={IMPA_MEAN} normHalf={IMPA_NORM_HALF} compHalf={IMPA_COMP_HALF}
            colors={{ norm: P.wedgeNorm, comp: P.wedgeComp, severe: P.wedgeSevere, normLine: P.wedgeNormLine }} />
        )}
        {showIF && (
          <WedgeZone apexPt={wU1a!} incisalPt={wU1i!} po={wPo!} or_={wOr!}
            label="I/F" normMean={IF_MEAN} normHalf={IF_NORM_HALF} compHalf={IF_COMP_HALF}
            colors={{ norm: P.wedgeU1Norm, comp: P.wedgeU1Comp, severe: P.wedgeU1Severe, normLine: P.wedgeU1Norm }} />
        )}

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
          if (SOFT_TISSUE_IDS.has(pt.id.toLowerCase())) return null;

          const isDragged   = activeDragId === pt.id;
          const isActive    = pt.id === activePointId;
          const isFocused   = pt.id === focusedPointId;
          const isHovMetric = isPointHovered(pt.id);

          // Mode Isolation : masquer tout sauf le point draggé
          if (activeDragId && !isDragged) return null;

          // ── Position d'affichage ──────────────────────────────────
          // C'est ici que réside le correctif : pendant le drag,
          // on affiche à la position calculée par getScreenCTM,
          // pas à la position commitée (pt.x, pt.y).
          const dispX = isDragged && activeDragPos ? activeDragPos.x : pt.x;
          const dispY = isDragged && activeDragPos ? activeDragPos.y : pt.y;

          const baseColor   = pt.id.startsWith('U') ? P.ptU
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

        {/* ══ CALIBRATION ══════════════════════════════════════════════ */}
        {isCalibrating && calibrationPoints && (
          <g>
            {calibrationPoints.map((cpt, i) => (
              <path key={`calib-${i}`}
                d={[
                  `M ${cpt.x-16} ${cpt.y} L ${cpt.x+16} ${cpt.y}`,
                  `M ${cpt.x} ${cpt.y-16} L ${cpt.x} ${cpt.y+16}`,
                ].join(' ')}
                stroke="#eab308" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
            ))}
            {calibrationPoints.length === 2 && (
              <line
                x1={calibrationPoints[0].x} y1={calibrationPoints[0].y}
                x2={calibrationPoints[1].x} y2={calibrationPoints[1].y}
                stroke="#eab308" strokeWidth="2" strokeDasharray="4,4"
                vectorEffect="non-scaling-stroke" />
            )}
          </g>
        )}

        {/* ══ LOUPE SVG PIXEL-PERFECT ═══════════════════════════════════
            Image repositionnée : x = magX - cursor.x × zoom
            Croix de visée au centre exact.
            ══════════════════════════════════════════════════════════ */}
        {magnifierEnabled && magnifier.show && imageSrc && (
          <g className="pointer-events-none">
            <circle cx={magX} cy={magY} r={MAG_R}
              fill={P.magnifierBg} stroke={P.magnifierRing}
              strokeWidth="2" vectorEffect="non-scaling-stroke" />
            <image
              href={imageSrc}
              x={magX - magnifier.x * MAG_ZOOM}
              y={magY - magnifier.y * MAG_ZOOM}
              width={imageWidth  * MAG_ZOOM}
              height={imageHeight * MAG_ZOOM}
              clipPath="url(#cephalo-mag-clip)"
              preserveAspectRatio="none"
              style={{
                filter: [
                  `brightness(${imgFilters?.brightness ?? 100}%)`,
                  `contrast(${imgFilters?.contrast ?? 100}%)`,
                  `invert(${imgFilters?.invert ? 100 : 0}%)`,
                ].join(' '),
              }}
            />
            <circle cx={magX} cy={magY} r={MAG_R - 1}
              fill="none" stroke={P.magnifierRing}
              strokeWidth="1" opacity="0.35" vectorEffect="non-scaling-stroke" />
            <line x1={magX-14} y1={magY} x2={magX+14} y2={magY}
              stroke={P.crosshairCol} strokeWidth="1.2" opacity="0.95" vectorEffect="non-scaling-stroke" />
            <line x1={magX} y1={magY-14} x2={magX} y2={magY+14}
              stroke={P.crosshairCol} strokeWidth="1.2" opacity="0.95" vectorEffect="non-scaling-stroke" />
            <circle cx={magX} cy={magY} r={2.2}
              fill={P.crosshairCol} opacity="1" vectorEffect="non-scaling-stroke" />
          </g>
        )}
      </svg>
    </div>
  );
};