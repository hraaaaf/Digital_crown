/**
 * CephaloTracingLayerBase.tsx · Digital Crown
 *
 * Historical tracing geometry and interaction engine.
 * Scientific colors come from the global Céphalo semantic contract; app UI
 * colors and clinical status colors come from Digital Crown theme tokens.
 * Geometry, calculations, drag behavior and clinical thresholds are unchanged.
 */

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';
import type { Landmark, ImageFilters, VTOSettings } from './cephaloShared';
import { toDeg, projectPointOnLine, getPerpendicularTick, buildWedgePath } from './cephaloMath';
import { getCephaloPalette } from './cephaloTheme';
import {
  CEPHALO_SCIENTIFIC_COLORS,
  cephaloGeometryColor,
} from './cephaloVisualSemantics';
import { AnatomicalTooth } from './components/AnatomicalTooth';
import { WedgeZone } from './components/WedgeZone';
import { CephaloCalibrationOverlay } from './components/CephaloCalibrationOverlay';
import { CephaloMagnifierOverlay } from './components/CephaloMagnifierOverlay';
import { CephaloLandmarkReticles } from './components/CephaloLandmarkReticles';
import { CephaloSvgDefs } from './components/CephaloSvgDefs';
import { useCephaloInteraction } from './hooks/useCephaloInteraction';

export interface GhostData {
  landmarks: Landmark[];
  opacity: number;
  color: string;
}

export type TracingUIMode = 'standard' | 'pro';

export interface CephaloTracingLayerProps {
  imageSrc?: string;
  imgFilters?: ImageFilters;
  landmarks: Landmark[];
  baseOpacity?: number;
  ghosts?: GhostData[];
  imageWidth: number;
  imageHeight: number;
  onUpdateLandmarks: (newLandmarks: Landmark[]) => void;
  activePointId?: string | null;
  focusedPointId?: string | null;
  onPointMouseDown?: (id: string) => void;
  visualDebug?: {
    N_prime?: [number, number];
    A_prime?: [number, number];
    B_prime?: [number, number];
    normative_zones?: Array<{
      cx: number; cy: number; rx: number; ry: number; rotation?: number;
    }>;
  } | null;
  isCalibrating?: boolean;
  calibrationPoints?: { x: number; y: number }[];
  onAddCalibrationPoint?: (p: { x: number; y: number }) => void;
  uiMode?: TracingUIMode;
  hoveredMetric?: { key: string; points: string[]; lines: string[] } | null;
  onEmptyAreaClick?: (p: { x: number; y: number }) => void;
  magnifierEnabled?: boolean;
  performanceMode?: boolean;
  vto?: VTOSettings;
  activeAnalysis?: string;
}

type TracingPalette = {
  francfort: string;
  mandibule: string;
  mcNamara: string;
  sn: string;
  na: string;
  nb: string;
  ab: string;
  u1: string;
  l1: string;
  ptDefault: string;
  ptU: string;
  ptL: string;
  ptSoft: string;
  ptFocus: string;
  text: string;
  magnifierBg: string;
  magnifierRing: string;
  crosshairCol: string;
  isolationDim: number;
  wedgeNorm: string;
  wedgeComp: string;
  wedgeSevere: string;
  wedgeNormLine: string;
  wedgeU1Norm: string;
  wedgeU1Comp: string;
  wedgeU1Severe: string;
};

const getTracingPalette = (uiMode: TracingUIMode): TracingPalette => {
  const theme = getCephaloPalette();
  return {
    francfort: cephaloGeometryColor('fh'),
    mandibule: cephaloGeometryColor('mp'),
    mcNamara: CEPHALO_SCIENTIFIC_COLORS.skeletal,
    sn: cephaloGeometryColor('sn'),
    na: cephaloGeometryColor('na'),
    nb: cephaloGeometryColor('nb'),
    ab: cephaloGeometryColor('ab'),
    u1: cephaloGeometryColor('u1'),
    l1: cephaloGeometryColor('l1'),
    ptDefault: CEPHALO_SCIENTIFIC_COLORS.auxiliary,
    ptU: CEPHALO_SCIENTIFIC_COLORS.dental,
    ptL: CEPHALO_SCIENTIFIC_COLORS.dental,
    ptSoft: CEPHALO_SCIENTIFIC_COLORS.soft_tissue,
    ptFocus: theme.text,
    text: theme.text,
    magnifierBg: theme.bgInput,
    magnifierRing: theme.accent,
    crosshairCol: theme.accent,
    isolationDim: uiMode === 'pro' ? 0.05 : 0.06,
    wedgeNorm: theme.accentSuccess,
    wedgeComp: theme.accentWarning,
    wedgeSevere: theme.accentError,
    wedgeNormLine: theme.accentSuccess,
    wedgeU1Norm: theme.accentSuccess,
    wedgeU1Comp: theme.accentWarning,
    wedgeU1Severe: theme.accentError,
  };
};

const IMPA_MEAN = 90;
const IMPA_NORM_HALF = 5;
const IMPA_COMP_HALF = 10;
const IF_MEAN = 107;
const IF_NORM_HALF = 5;
const IF_COMP_LOW = 97;
const IF_COMP_HIGH = 120;
const IF_COMP_HALF = Math.max(IF_MEAN - IF_COMP_LOW, IF_COMP_HIGH - IF_MEAN);

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
  performanceMode = false,
  vto = { enabled: false, showGhostFace: true, showSoftTissue: true },
  activeAnalysis = 'all'
}) => {
  const P = getTracingPalette(uiMode);
  const isPro = uiMode === 'pro';

  const {
    svgRef,
    activeDragId,
    setActiveDragId,
    activeDragPos,
    setActiveDragPos,
    magnifier,
    setMagnifier,
    clientToSVG,
    getPoint,
    handleSvgClick,
  } = useCephaloInteraction({
    landmarks,
    imageWidth,
    imageHeight,
    magnifierEnabled,
    isCalibrating,
    onAddCalibrationPoint,
    onEmptyAreaClick,
  });

  const isHoverActive = !!hoveredMetric;
  const isLineHovered = (lineId: string) =>
    isHoverActive && hoveredMetric!.lines.map(l => l.toLowerCase()).includes(lineId.toLowerCase());

  const MAG_R = 80;
  const MAG_MAR = 40;
  const MAG_ZOOM = 3;

  let magX = magnifier.x + MAG_MAR + MAG_R;
  if (magX + MAG_R > imageWidth) magX = magnifier.x - MAG_MAR - MAG_R;
  if (magX - MAG_R < 0) magX = MAG_R + MAG_MAR;
  let magY = magnifier.y + MAG_MAR + MAG_R;
  if (magY + MAG_R > imageHeight) magY = magnifier.y - MAG_MAR - MAG_R;
  if (magY - MAG_R < 0) magY = MAG_R + MAG_MAR;

  const renderSkeletalLayer = (
    pts: Landmark[],
    isGhost = false,
    overrideColor?: string,
    layerOp = 1,
  ) => {
    const applyVTO = (points: Landmark[]) => {
      if (!vto.enabled || isGhost) return points;

      const u1x = vto.u1_offset?.x || 0;
      const l1x = vto.l1_offset?.x || 0;
      const mandX = vto.mand_offset?.x || 0;

      return points.map(pt => {
        const id = pt.id.toLowerCase();
        if (id.includes('u1')) return { ...pt, x: pt.x + u1x };
        if (id.includes('l1')) return { ...pt, x: pt.x + l1x + mandX };
        if (id === 'b' || id === 'pog' || id === 'me' || id === 'go') return { ...pt, x: pt.x + mandX };
        if (id === 'ls' || id === 'ul' || id === 'st') return { ...pt, x: pt.x + u1x * 0.75 };
        if (id === 'li' || id === 'll') return { ...pt, x: pt.x + (l1x * 0.8) + mandX };
        if (id === 'b_soft' || id === 'pog_soft' || id === 'me_soft' || id === 'stpog') return { ...pt, x: pt.x + mandX };
        if (id === 'sn' || id === 'a_soft') return { ...pt, x: pt.x + u1x * 0.25 };
        return pt;
      });
    };

    const finalPts = applyVTO(pts);
    const po = getPoint(finalPts, 'Po');
    const or_ = getPoint(finalPts, 'Or');
    const a = getPoint(finalPts, 'A');
    const b = getPoint(finalPts, 'B');
    const go = getPoint(finalPts, 'Go');
    const me = getPoint(finalPts, 'Me');
    const u1i = getPoint(finalPts, 'U1_incisal') ?? getPoint(finalPts, 'U1i');
    const u1a = getPoint(finalPts, 'U1_apex') ?? getPoint(finalPts, 'U1a');
    const l1i = getPoint(finalPts, 'L1_incisal') ?? getPoint(finalPts, 'L1i');
    const l1a = getPoint(finalPts, 'L1_apex') ?? getPoint(finalPts, 'L1a');
    const gSoft = getPoint(finalPts, 'G_soft') ?? getPoint(finalPts, 'g_soft') ?? getPoint(finalPts, 'g-soft');
    const nSoft = getPoint(finalPts, 'N_soft') ?? getPoint(finalPts, 'n_soft') ?? getPoint(finalPts, 'n-soft');
    const prn = getPoint(finalPts, 'Prn') ?? getPoint(finalPts, 'prn') ?? getPoint(finalPts, 'Nose_Tip');
    const cm = getPoint(finalPts, 'Cm') ?? getPoint(finalPts, 'cm');
    const sn = getPoint(finalPts, 'Sn_soft') ?? getPoint(finalPts, 'Sn') ?? getPoint(finalPts, 'sn');
    const aSoft = getPoint(finalPts, 'A_soft') ?? getPoint(finalPts, 'a_soft');
    const ls = getPoint(finalPts, 'Ls_soft') ?? getPoint(finalPts, 'Ls') ?? getPoint(finalPts, 'ls') ?? getPoint(finalPts, 'UL') ?? getPoint(finalPts, 'ul') ?? getPoint(finalPts, 'Upper_Lip');
    const st = getPoint(finalPts, 'St') ?? getPoint(finalPts, 'st') ?? getPoint(finalPts, 'Stomion');
    const li = getPoint(finalPts, 'Li_soft') ?? getPoint(finalPts, 'Li') ?? getPoint(finalPts, 'li') ?? getPoint(finalPts, 'LL') ?? getPoint(finalPts, 'll') ?? getPoint(finalPts, 'Lower_Lip');
    const bSoft = getPoint(finalPts, 'B_soft') ?? getPoint(finalPts, 'b_soft');
    const pogSoft = getPoint(finalPts, 'Pog_soft') ?? getPoint(finalPts, 'pog_soft') ?? getPoint(finalPts, 'stpog') ?? getPoint(finalPts, 'stPog') ?? getPoint(finalPts, 'Soft_Pogonion');
    const meSoft = getPoint(finalPts, 'Me_soft') ?? getPoint(finalPts, 'me_soft') ?? getPoint(finalPts, 'Soft_Menton');

    const ghostDash = isGhost ? '6,4' : undefined;
    const seg = (
      p1: Landmark | undefined,
      p2: Landmark | undefined,
      lineKey: string,
      defColor: string,
      opts?: { dash?: string; op?: number },
    ) => {
      if (!p1 || !p2) return null;

      if (activeAnalysis !== 'all' && !isGhost) {
        const analysis = activeAnalysis.toLowerCase();
        if (analysis === 'steiner' && !['sn', 'na', 'nb'].includes(lineKey)) return null;
        if (analysis === 'tweed' && !['fh', 'mp', 'u1', 'l1'].includes(lineKey)) return null;
        if (analysis === 'mcnamara' && !['fh', 'mcnamara_perp', 'coa', 'cogn', 'ansme'].includes(lineKey)) return null;
        if (analysis === 'wits' && !['occ'].includes(lineKey)) return null;
        if (analysis === 'esthetique' && !['eline'].includes(lineKey)) return null;
      }

      const color = overrideColor ?? defColor;
      const highlighted = !isGhost && isLineHovered(lineKey);
      const strokeWidth = highlighted ? 2.8 : 1.5;
      const opacity = (opts?.op ?? 1) * layerOp;
      return (
        <motion.line
          key={`${lineKey}-${isGhost}`}
          x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
          stroke={color}
          strokeDasharray={opts?.dash ?? ghostDash}
          vectorEffect="non-scaling-stroke"
          animate={performanceMode ? {} : { strokeWidth, opacity }}
          transition={{ duration: 0.14 }}
          style={!performanceMode && highlighted ? { filter: `drop-shadow(0 0 5px ${color})` } : {}}
        />
      );
    };

    const u1Active = !isGhost && (activeDragId === 'U1_incisal' || activeDragId === 'U1_apex');
    const l1Active = !isGhost && (activeDragId === 'L1_incisal' || activeDragId === 'L1_apex');
    const u1Glow = isPro ? `drop-shadow(0 0 12px ${P.u1})` : undefined;
    const l1Glow = isPro ? `drop-shadow(0 0 12px ${P.l1})` : undefined;

    let wedgeCompPath: string | null = null;
    let wedgeNormPath: string | null = null;

    if (!isGhost && l1a && l1i && go && me) {
      const mandDx = me.x - go.x;
      const mandDy = me.y - go.y;
      const mandLen = Math.sqrt(mandDx * mandDx + mandDy * mandDy);
      const toothDx = l1i.x - l1a.x;
      const toothDy = l1i.y - l1a.y;
      const toothLen = Math.sqrt(toothDx * toothDx + toothDy * toothDy);

      if (mandLen >= 2 && toothLen >= 2) {
        const mandAngle = toDeg(Math.atan2(mandDy, mandDx));
        const toothAngle = toDeg(Math.atan2(toothDy, toothDx));
        const perpA = mandAngle - 90;
        const perpB = mandAngle + 90;
        const angDiff = (a2: number, b2: number) => {
          let d = ((a2 - b2) % 360 + 360) % 360;
          if (d > 180) d -= 360;
          return Math.abs(d);
        };
        const idealAxis = angDiff(toothAngle, perpA) <= angDiff(toothAngle, perpB) ? perpA : perpB;
        const R = Math.min(Math.max(toothLen * 0.80, 40), 110);
        const Rinner = R * 0.30;
        wedgeCompPath = buildWedgePath(l1a.x, l1a.y, R, Rinner, idealAxis - IMPA_COMP_HALF, IMPA_COMP_HALF * 2);
        wedgeNormPath = buildWedgePath(l1a.x, l1a.y, R * 0.90, Rinner * 1.05, idealAxis - IMPA_NORM_HALF, IMPA_NORM_HALF * 2);
      }
    }

    const wNorm = overrideColor ?? P.wedgeNorm;
    const wComp = overrideColor ?? P.wedgeComp;
    const n = getPoint(finalPts, 'N');
    const s = getPoint(finalPts, 'S');
    const co = getPoint(finalPts, 'Co');
    const gn = getPoint(finalPts, 'Gn');
    const ans = getPoint(finalPts, 'ANS');
    const occAnt = getPoint(finalPts, 'Occ_Ant');
    const occPost = getPoint(finalPts, 'Occ_Post');

    const showSteiner = activeAnalysis === 'all' || activeAnalysis.toLowerCase() === 'steiner';
    const showTweed = activeAnalysis === 'all' || activeAnalysis.toLowerCase() === 'tweed';
    const showMcNamara = activeAnalysis === 'all' || activeAnalysis.toLowerCase() === 'mcnamara';
    const showWits = activeAnalysis === 'all' || activeAnalysis.toLowerCase() === 'wits';

    const softTissueColor = CEPHALO_SCIENTIFIC_COLORS.soft_tissue;

    return (
      <g key={isGhost ? `ghost-${layerOp}` : 'main-layer'}>
        {showTweed || showMcNamara ? seg(po, or_, 'fh', P.francfort) : null}
        {showTweed ? seg(go, me, 'mp', P.mandibule) : null}

        {showSteiner && (
          <>
            {seg(s, n, 'sn', P.sn)}
            {seg(n, a, 'na', P.na)}
            {seg(n, b, 'nb', P.nb)}
            {seg(a, b, 'ab', P.ab, { dash: isGhost ? '6,4' : '2,3', op: 0.50 })}
          </>
        )}

        {showMcNamara && (
          <>
            {seg(co, a, 'coa', cephaloGeometryColor('coa'))}
            {seg(co, gn, 'cogn', cephaloGeometryColor('cogn'))}
            {seg(ans, me, 'ansme', cephaloGeometryColor('ansme'), { dash: '2,2' })}
          </>
        )}

        {showWits && seg(occPost, occAnt, 'occ', cephaloGeometryColor('occ'), { dash: '4,4' })}

        {vto.showSoftTissue && !isGhost && (() => {
          const ls2 = getPoint(finalPts, 'Ls2') || getPoint(finalPts, 'ls2');
          const li2 = getPoint(finalPts, 'Li2') || getPoint(finalPts, 'li2');
          const profilePoints = [gSoft, nSoft, prn, cm, sn, aSoft, ls, ls2, st, li2, li, bSoft, pogSoft, meSoft].filter(Boolean) as Landmark[];
          profilePoints.sort((aPoint, bPoint) => aPoint.y - bPoint.y);
          if (profilePoints.length < 2) return null;

          const nPoint = getPoint(pts, 'N');
          const por = getPoint(pts, 'Po');
          const facesRight = nPoint && por ? nPoint.x > por.x : true;
          const edgeX = facesRight ? 0 : imageWidth;
          const getControlPoints = (p0: Landmark, p1: Landmark, p2: Landmark, t = 0.2) => {
            const d1 = Math.sqrt((p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2);
            const d2 = Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
            const fa = t * d1 / (d1 + d2);
            const fb = t * d2 / (d1 + d2);
            return [
              { x: p1.x - fa * (p2.x - p0.x), y: p1.y - fa * (p2.y - p0.y) },
              { x: p1.x + fb * (p2.x - p0.x), y: p1.y + fb * (p2.y - p0.y) },
            ];
          };

          let d = `M ${profilePoints[0].x} ${profilePoints[0].y}`;
          const nPts = profilePoints.length;
          for (let i = 0; i < nPts - 1; i++) {
            const p0 = profilePoints[i === 0 ? i : i - 1];
            const p1 = profilePoints[i];
            const p2 = profilePoints[i + 1];
            const p3 = profilePoints[i + 2 === nPts ? i + 1 : i + 2];
            const cp1 = getControlPoints(p0, p1, p2)[1];
            const cp2 = getControlPoints(p1, p2, p3)[0];
            d += ` C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${p2.x} ${p2.y}`;
          }

          return (
            <g>
              <defs>
                <linearGradient id="skinProfileGradient" x1={facesRight ? '100%' : '0%'} y1="0%" x2={facesRight ? '0%' : '100%'} y2="0%">
                  <stop offset="0%" stopColor={softTissueColor} stopOpacity="0.34" />
                  <stop offset="30%" stopColor={softTissueColor} stopOpacity="0.14" />
                  <stop offset="100%" stopColor={softTissueColor} stopOpacity="0" />
                </linearGradient>
                <linearGradient id="ghostFaceGradientDynamic" x1={facesRight ? '100%' : '0%'} y1="0%" x2={facesRight ? '0%' : '100%'} y2="0%">
                  <stop offset="0%" stopColor={softTissueColor} stopOpacity="0.22" />
                  <stop offset="60%" stopColor={softTissueColor} stopOpacity="0.08" />
                  <stop offset="100%" stopColor={softTissueColor} stopOpacity="0" />
                </linearGradient>
              </defs>
              <motion.path
                initial={false}
                animate={{ d: `${d} L ${edgeX} ${profilePoints[nPts - 1].y} L ${edgeX} ${profilePoints[0].y} Z` }}
                transition={{ type: 'spring', stiffness: 100, damping: 25 }}
                fill={vto.showGhostFace ? 'url(#ghostFaceGradientDynamic)' : 'url(#skinProfileGradient)'}
                style={{ pointerEvents: 'none' }}
              />
              <motion.path
                initial={false}
                animate={{ d }}
                transition={{ type: 'spring', stiffness: 100, damping: 25 }}
                fill="none"
                stroke={softTissueColor}
                strokeWidth="2.5"
                strokeLinejoin="round"
                strokeLinecap="round"
                opacity="0.9"
                style={!performanceMode ? { filter: `drop-shadow(0 0 8px ${softTissueColor})` } : {}}
                vectorEffect="non-scaling-stroke"
                className="pointer-events-none"
              />
            </g>
          );
        })()}

        {prn && pogSoft && (
          <g>
            <line
              x1={prn.x} y1={prn.y} x2={pogSoft.x} y2={pogSoft.y}
              stroke={softTissueColor}
              strokeWidth={isGhost ? '1' : '2'}
              strokeDasharray={isGhost ? '6,4' : '4,2'}
              opacity={isGhost ? '0.4' : '0.85'}
              vectorEffect="non-scaling-stroke"
              style={!isGhost && !performanceMode ? { filter: `drop-shadow(0 0 5px ${softTissueColor})` } : {}}
            />
            {!isGhost && ls && li && (() => {
              const dx = pogSoft.x - prn.x;
              const dy = pogSoft.y - prn.y;
              const lenSq = dx * dx + dy * dy;
              if (lenSq === 0) return null;
              const tLs = ((ls.x - prn.x) * dx + (ls.y - prn.y) * dy) / lenSq;
              const pLs = { x: prn.x + tLs * dx, y: prn.y + tLs * dy };
              const tLi = ((li.x - prn.x) * dx + (li.y - prn.y) * dy) / lenSq;
              const pLi = { x: prn.x + tLi * dx, y: prn.y + tLi * dy };
              return (
                <>
                  <line x1={ls.x} y1={ls.y} x2={pLs.x} y2={pLs.y} stroke={softTissueColor} strokeWidth="1.5" opacity="0.9" vectorEffect="non-scaling-stroke" />
                  <line x1={li.x} y1={li.y} x2={pLi.x} y2={pLi.y} stroke={softTissueColor} strokeWidth="1.5" opacity="0.9" vectorEffect="non-scaling-stroke" />
                  <circle cx={pLs.x} cy={pLs.y} r="2.5" fill={softTissueColor} />
                  <circle cx={pLi.x} cy={pLi.y} r="2.5" fill={softTissueColor} />
                </>
              );
            })()}
          </g>
        )}

        {wedgeCompPath && (
          <path d={wedgeCompPath} fill={wComp} fillOpacity="0.10" stroke={wComp} strokeWidth="0.9" strokeDasharray="4,2" vectorEffect="non-scaling-stroke" className="pointer-events-none" />
        )}
        {wedgeNormPath && (
          <path d={wedgeNormPath} fill={wNorm} fillOpacity="0.20" stroke={wNorm} strokeWidth="1.1" vectorEffect="non-scaling-stroke" className="pointer-events-none" />
        )}

        {u1i && u1a && (
          <AnatomicalTooth
            incisalPoint={u1i}
            apexPoint={u1a}
            color={overrideColor ?? P.u1}
            isHovered={!isGhost && isLineHovered('u1')}
            opacity={layerOp}
            isGhost={isGhost}
            isBeingDragged={u1Active}
            glowFilter={u1Glow}
          />
        )}
        {l1i && l1a && (
          <AnatomicalTooth
            incisalPoint={l1i}
            apexPoint={l1a}
            color={overrideColor ?? P.l1}
            isHovered={!isGhost && isLineHovered('l1')}
            opacity={layerOp}
            isGhost={isGhost}
            isBeingDragged={l1Active}
            glowFilter={l1Glow}
          />
        )}
      </g>
    );
  };

  const po = getPoint(landmarks, 'Po');
  const or_ = getPoint(landmarks, 'Or');
  let francfortLineExtended: { x1: number; y1: number; x2: number; y2: number } | null = null;
  if (po && or_) {
    const dx = or_.x - po.x;
    const dy = or_.y - po.y;
    francfortLineExtended = {
      x1: po.x - dx * 10, y1: po.y - dy * 10,
      x2: or_.x + dx * 10, y2: or_.y + dy * 10,
    };
  }

  const n0 = getPoint(landmarks, 'N');
  const ptA = getPoint(landmarks, 'A');
  const ptB = getPoint(landmarks, 'B');
  const francfortAngle = (po && or_) ? toDeg(Math.atan2(or_.y - po.y, or_.x - po.x)) : 0;
  const nPrime = (po && or_ && n0) ? projectPointOnLine(n0.x, n0.y, po.x, po.y, or_.x, or_.y) : null;
  const aPrime = (po && or_ && ptA) ? projectPointOnLine(ptA.x, ptA.y, po.x, po.y, or_.x, or_.y) : null;
  const bPrime = (po && or_ && ptB) ? projectPointOnLine(ptB.x, ptB.y, po.x, po.y, or_.x, or_.y) : null;

  let mcNamaraLine: { x1: number; y1: number; x2: number; y2: number } | null = null;
  if (n0 && nPrime) {
    const dx = nPrime.x - n0.x;
    const dy = nPrime.y - n0.y;
    mcNamaraLine = {
      x1: n0.x - dx * 1000, y1: n0.y - dy * 1000,
      x2: n0.x + dx * 1000, y2: n0.y + dy * 1000,
    };
  }

  const nPrimeTick = nPrime ? getPerpendicularTick(nPrime.x, nPrime.y, francfortAngle, 14) : null;
  const aPrimeTick = aPrime ? getPerpendicularTick(aPrime.x, aPrime.y, francfortAngle, 14) : null;
  const bPrimeTick = bPrime ? getPerpendicularTick(bPrime.x, bPrime.y, francfortAngle, 14) : null;

  const dragId = activeDragId ?? '';
  const l1Dragged = ['L1_incisal', 'L1_apex', 'L1i', 'L1a'].includes(dragId);
  const u1Dragged = ['U1_incisal', 'U1_apex', 'U1i', 'U1a'].includes(dragId);
  const frkDragged = dragId === 'Po' || dragId === 'Or';
  const mandDragged = dragId === 'Go' || dragId === 'Me';
  const wL1i = (l1Dragged || frkDragged || mandDragged) ? (getPoint(landmarks, 'L1_incisal') ?? getPoint(landmarks, 'L1i')) : null;
  const wL1a = (l1Dragged || frkDragged || mandDragged) ? (getPoint(landmarks, 'L1_apex') ?? getPoint(landmarks, 'L1a')) : null;
  const wU1i = (u1Dragged || frkDragged) ? (getPoint(landmarks, 'U1_incisal') ?? getPoint(landmarks, 'U1i')) : null;
  const wU1a = (u1Dragged || frkDragged) ? (getPoint(landmarks, 'U1_apex') ?? getPoint(landmarks, 'U1a')) : null;
  const wPo = (u1Dragged || frkDragged) ? getPoint(landmarks, 'Po') : null;
  const wOr = (u1Dragged || frkDragged) ? getPoint(landmarks, 'Or') : null;
  const wGo = (l1Dragged || mandDragged) ? getPoint(landmarks, 'Go') : null;
  const wMe = (l1Dragged || mandDragged) ? getPoint(landmarks, 'Me') : null;
  const showIMPA = !!(wL1i && wL1a && wGo && wMe);
  const showIF = !!(wU1i && wU1a && wPo && wOr);
  const skeletalOp = activeDragId ? P.isolationDim : baseOpacity;

  if (imageWidth === 0 || imageHeight === 0) return null;

  return (
    <div className="absolute inset-0 w-full h-full z-20">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${imageWidth} ${imageHeight}`}
        preserveAspectRatio="xMidYMid meet"
        className={cn('w-full h-full', isCalibrating ? 'cursor-crosshair' : 'cursor-default')}
        onClick={handleSvgClick}
        onPointerMove={e => {
          if (!magnifierEnabled || activeDragId) return;
          const coords = clientToSVG(e.clientX, e.clientY);
          if (coords) setMagnifier({ x: coords.x, y: coords.y, show: true });
        }}
        onPointerLeave={() => {
          if (!activeDragId) setMagnifier(m => ({ ...m, show: false }));
        }}
      >
        <CephaloSvgDefs magX={magX} magY={magY} MAG_R={MAG_R} isPro={isPro} />

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

        <motion.g animate={{ opacity: skeletalOp }} transition={{ duration: 0.10 }}>
          {ghosts.map(g => renderSkeletalLayer(g.landmarks, true, g.color, g.opacity))}
          {renderSkeletalLayer(landmarks, false, undefined, baseOpacity)}

          <g opacity={baseOpacity}>
            {isPro && visualDebug?.normative_zones?.map((z, i) => (
              <ellipse
                key={`zone-${i}`}
                cx={z.cx} cy={z.cy} rx={z.rx} ry={z.ry}
                fill={P.wedgeNorm}
                fillOpacity="0.04"
                stroke={P.wedgeNorm}
                strokeWidth="0.5"
                strokeDasharray="2,2"
                transform={`rotate(${z.rotation ?? 0},${z.cx},${z.cy})`}
                vectorEffect="non-scaling-stroke"
                className="pointer-events-none"
              />
            ))}
            {francfortLineExtended && (
              <line
                x1={francfortLineExtended.x1} y1={francfortLineExtended.y1}
                x2={francfortLineExtended.x2} y2={francfortLineExtended.y2}
                stroke={cephaloGeometryColor('fh')}
                strokeWidth="1.5"
                opacity="0.6"
                strokeDasharray="10,5"
                vectorEffect="non-scaling-stroke"
              />
            )}
          </g>
        </motion.g>

        {mcNamaraLine && nPrime && nPrimeTick && (
          <g>
            <line
              x1={mcNamaraLine.x1} y1={mcNamaraLine.y1}
              x2={mcNamaraLine.x2} y2={mcNamaraLine.y2}
              stroke={cephaloGeometryColor('mcnamara_perp')}
              strokeWidth="1.5"
              strokeDasharray="8,4"
              opacity="0.7"
              vectorEffect="non-scaling-stroke"
            />
            <line
              x1={nPrimeTick.x1} y1={nPrimeTick.y1}
              x2={nPrimeTick.x2} y2={nPrimeTick.y2}
              stroke={cephaloGeometryColor('mcnamara_perp')}
              strokeWidth="2"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={nPrime.x + 20} y={nPrime.y - 15}
              fontSize="12"
              fontWeight="600"
              fill={cephaloGeometryColor('mcnamara_perp')}
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              McNamara
            </text>
          </g>
        )}

        {aPrime && ptA && aPrimeTick && (
          <g>
            <line
              x1={ptA.x} y1={ptA.y}
              x2={aPrime.x} y2={aPrime.y}
              stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              strokeDasharray="5,5"
              strokeWidth="2"
              opacity="0.8"
              vectorEffect="non-scaling-stroke"
            />
            <line
              x1={aPrimeTick.x1} y1={aPrimeTick.y1}
              x2={aPrimeTick.x2} y2={aPrimeTick.y2}
              stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              strokeWidth="2.5"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={aPrime.x + 18} y={aPrime.y - 12}
              fontSize="14"
              fontWeight="bold"
              fill={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              A'
            </text>
          </g>
        )}

        {bPrime && ptB && bPrimeTick && (
          <g>
            <line
              x1={ptB.x} y1={ptB.y}
              x2={bPrime.x} y2={bPrime.y}
              stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              strokeDasharray="5,5"
              strokeWidth="2"
              opacity="0.8"
              vectorEffect="non-scaling-stroke"
            />
            <line
              x1={bPrimeTick.x1} y1={bPrimeTick.y1}
              x2={bPrimeTick.x2} y2={bPrimeTick.y2}
              stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              strokeWidth="2.5"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={bPrime.x + 18} y={bPrime.y - 12}
              fontSize="14"
              fontWeight="bold"
              fill={CEPHALO_SCIENTIFIC_COLORS.skeletal}
              style={{ userSelect: 'none', pointerEvents: 'none' }}
            >
              B'
            </text>
          </g>
        )}

        {showIMPA && (
          <WedgeZone
            apexPt={wL1a!}
            incisalPt={wL1i!}
            po={wGo!}
            or_={wMe!}
            label="IMPA"
            normMean={IMPA_MEAN}
            normHalf={IMPA_NORM_HALF}
            compHalf={IMPA_COMP_HALF}
            colors={{ norm: P.wedgeNorm, comp: P.wedgeComp, severe: P.wedgeSevere, normLine: P.wedgeNormLine }}
          />
        )}
        {showIF && (
          <WedgeZone
            apexPt={wU1a!}
            incisalPt={wU1i!}
            po={wPo!}
            or_={wOr!}
            label="I/F"
            normMean={IF_MEAN}
            normHalf={IF_NORM_HALF}
            compHalf={IF_COMP_HALF}
            colors={{ norm: P.wedgeU1Norm, comp: P.wedgeU1Comp, severe: P.wedgeU1Severe, normLine: P.wedgeU1Norm }}
          />
        )}

        <CephaloLandmarkReticles
          landmarks={landmarks}
          isCalibrating={isCalibrating}
          baseOpacity={baseOpacity}
          activeDragId={activeDragId}
          activeDragPos={activeDragPos}
          activePointId={activePointId}
          focusedPointId={focusedPointId}
          hoveredMetric={hoveredMetric}
          palette={P}
          isPro={isPro}
          setActiveDragId={setActiveDragId}
          setActiveDragPos={setActiveDragPos}
          magnifierEnabled={magnifierEnabled}
          setMagnifier={setMagnifier}
          clientToSVG={clientToSVG}
          onPointMouseDown={onPointMouseDown}
          onUpdateLandmarks={onUpdateLandmarks}
        />

        <CephaloCalibrationOverlay
          isCalibrating={isCalibrating}
          activeDragId={activeDragId}
          magnifier={magnifier}
          calibrationPoints={calibrationPoints}
        />

        <CephaloMagnifierOverlay
          magnifierEnabled={magnifierEnabled}
          magnifier={magnifier}
          imageSrc={imageSrc}
          imageWidth={imageWidth}
          imageHeight={imageHeight}
          imgFilters={imgFilters}
          magX={magX}
          magY={magY}
          MAG_R={MAG_R}
          MAG_ZOOM={MAG_ZOOM}
          palette={P}
        />
      </svg>
    </div>
  );
};
