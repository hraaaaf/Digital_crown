import React from 'react';
import { useCephaloUnitsPerPixel } from './components/useCephaloUnitsPerPixel';
import { CephaloTracingLayer as BaseCephaloTracingLayer, getCephaloZoomViewBox } from './CephaloTracingLayerBase';
import type { CephaloTracingLayerProps, GhostData, TracingUIMode } from './CephaloTracingLayerBase';
import type { Landmark } from './cephaloShared';
import { projectPointOnLine } from './cephaloMath';
import { getCephaloPalette } from './cephaloTheme';
import {
  CEPHALO_SCIENTIFIC_COLORS,
  cephaloGeometryColor,
} from './cephaloVisualSemantics';
import {
  CEPHALO_METRIC_FOCUS_EVENT,
  CEPHALO_ANALYSIS_CHANGE_EVENT,
  publishCephaloAnalysis,
  type CephaloAnalysisMode,
  type CephaloMetricFocus,
} from './cephaloAnalysisBridge';

export type { CephaloTracingLayerProps, GhostData, TracingUIMode };

type AnalysisMode = CephaloAnalysisMode;

const ANALYSIS_OPTIONS: Array<{ id: AnalysisMode; label: string; shortLabel?: string }> = [
  { id: 'all', label: 'Tous' },
  { id: 'steiner', label: 'Steiner' },
  { id: 'tweed', label: 'Tweed' },
  { id: 'mcnamara', label: 'McNamara', shortLabel: 'McN' },
  { id: 'com', label: 'COM' },
  { id: 'ricketts', label: 'Ricketts', shortLabel: 'Rick.' },
];

const MODE_LANDMARKS: Record<Exclude<AnalysisMode, 'all'>, Set<string>> = {
  steiner: new Set([
    's', 'n', 'a', 'b',
    'u1_incisal', 'u1i', 'u1_apex', 'u1a',
    'l1_incisal', 'l1i', 'l1_apex', 'l1a',
    'gn_anatomic', 'u1_facial_surface', 'l1_facial_surface',
    'd_steiner_1959', 'occ_steiner_ant', 'occ_steiner_post',
  ]),
  tweed: new Set([
    'po', 'po_anatomic', 'or', 'go', 'me',
    'u1_incisal', 'u1i', 'u1_apex', 'u1a',
    'l1_incisal', 'l1i', 'l1_apex', 'l1a',
    'ls_soft', 'ls', 'li_soft', 'li', 'pog_soft', 'stpog', 'soft_pogonion',
  ]),
  mcnamara: new Set([
    'po', 'or', 'n', 'a', 'b', 'co', 'gn', 'ans', 'me',
  ]),
  com: new Set([
    's', 'n', 'a', 'b', 'po', 'or', 'go', 'me',
    'u1_incisal', 'u1i', 'u1_apex', 'u1a',
    'l1_incisal', 'l1i', 'l1_apex', 'l1a',
  ]),
  ricketts: new Set([
    'g_soft', 'g-soft', 'n_soft', 'n-soft', 'prn', 'nose_tip', 'cm',
    'sn_soft', 'sn', 'a_soft', 'ls_soft', 'ls', 'ls2', 'ul', 'upper_lip',
    'st', 'stomion', 'li2', 'li_soft', 'li', 'll', 'lower_lip',
    'b_soft', 'pog_soft', 'stpog', 'soft_pogonion', 'me_soft', 'soft_menton',
  ]),
};

const COM_BASE_SUPPRESSED_LANDMARKS = new Set(['n', 'nasion', 'a', 'point_a', 'b', 'point_b']);

const normalizeMode = (value?: string): AnalysisMode => {
  const normalized = (value || 'all').trim().toLowerCase();
  if (normalized === 'steiner') return 'steiner';
  if (normalized === 'tweed') return 'tweed';
  if (normalized === 'mcnamara') return 'mcnamara';
  if (normalized === 'com') return 'com';
  if (normalized === 'ricketts' || normalized === 'esthetique') return 'ricketts';
  return 'all';
};

const filterLandmarks = (landmarks: Landmark[], mode: AnalysisMode) => {
  if (mode === 'all') return landmarks;
  const allowed = MODE_LANDMARKS[mode];
  return landmarks.filter(item => allowed.has(item.id.toLowerCase()));
};

const findPoint = (landmarks: Landmark[], id: string) =>
  landmarks.find(item => item.id.toLowerCase() === id.toLowerCase());

const findPointAny = (landmarks: Landmark[], ...ids: string[]) => {
  for (const id of ids) {
    const point = findPoint(landmarks, id);
    if (point) return point;
  }
  return undefined;
};

const unitAxis = (start?: Landmark, end?: Landmark) => {
  if (!start || !end) return null;
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const length = Math.hypot(dx, dy);
  if (!Number.isFinite(length) || length <= 1e-9) return null;
  return { x: dx / length, y: dy / length };
};

/**
 * R19 analysis tracing controller.
 *
 * R18's historical drawing engine remains byte-identical in
 * CephaloTracingLayerBase.tsx. This controller separates COM from McNamara
 * and applies the global Céphalo scientific color vocabulary without changing
 * geometry or clinical calculation. Digital Crown tokens still own all UI
 * chrome, surfaces, text, borders and interaction focus.
 */
export const CephaloTracingLayer: React.FC<CephaloTracingLayerProps> = (props) => {
  const P = getCephaloPalette();
  const overlaySvgRef = React.useRef<SVGSVGElement>(null);
  const overlayViewBox = getCephaloZoomViewBox(props.imageWidth, props.imageHeight, props.viewZoom, props.viewPan);
  const labelUnit = useCephaloUnitsPerPixel(overlaySvgRef, !!props.compactLabels, overlayViewBox);
  const layerVisible = (id: 'landmarks' | 'plans' | 'measurements') => props.layerPresentation?.visibility[id] ?? true;
  const layerOpacity = (id: 'landmarks' | 'plans' | 'measurements') => props.layerPresentation?.opacity[id] ?? 1;
  const [mode, setMode] = React.useState<AnalysisMode>(() => normalizeMode(props.activeAnalysis));
  const [metricFocus, setMetricFocus] = React.useState<CephaloMetricFocus | null>(props.hoveredMetric ?? null);

  React.useEffect(() => {
    if (props.activeAnalysis) setMode(normalizeMode(props.activeAnalysis));
  }, [props.activeAnalysis]);

  React.useEffect(() => {
    publishCephaloAnalysis(mode);
  }, [mode]);

  // The ready-made analysis selector is a peer control of the overlay tabs.
  // Both surfaces must update the same tracing mode without changing any geometry.
  React.useEffect(() => {
    const onAnalysisChange = (event: Event) => {
      const requested = normalizeMode((event as CustomEvent<CephaloAnalysisMode>).detail);
      setMode(current => current === requested ? current : requested);
    };
    window.addEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysisChange as EventListener);
    return () => window.removeEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysisChange as EventListener);
  }, []);

  React.useEffect(() => {
    const onMetric = (event: Event) => {
      setMetricFocus((event as CustomEvent<CephaloMetricFocus | null>).detail ?? null);
    };
    window.addEventListener(CEPHALO_METRIC_FOCUS_EVENT, onMetric as EventListener);
    return () => window.removeEventListener(CEPHALO_METRIC_FOCUS_EVENT, onMetric as EventListener);
  }, []);

  React.useEffect(() => {
    if (props.hoveredMetric) setMetricFocus(props.hoveredMetric);
  }, [props.hoveredMetric]);

  const filteredLandmarks = React.useMemo(
    () => filterLandmarks(props.landmarks, mode),
    [props.landmarks, mode],
  );

  const filteredGhosts = React.useMemo<GhostData[]>(
    () => (props.ghosts || []).map(ghost => ({
      ...ghost,
      landmarks: filterLandmarks(ghost.landmarks, mode),
    })),
    [props.ghosts, mode],
  );

  const baseLandmarks = React.useMemo(
    () => mode === 'com'
      ? filteredLandmarks.filter(item => !COM_BASE_SUPPRESSED_LANDMARKS.has(item.id.toLowerCase()))
      : filteredLandmarks,
    [filteredLandmarks, mode],
  );

  // COM overlays live in a separate SVG. Resolve text-only collisions against
  // the ACTUAL rendered base labels in CSS pixels, so landscape radiographs and
  // 100/150% zoom use the same legibility contract. This never moves landmarks.
  const [comLabelOffsets, setComLabelOffsets] = React.useState<Record<string, { x: number; y: number }>>({});
  React.useLayoutEffect(() => {
    if (!props.compactLabels || mode !== 'com') return;
    const svg = overlaySvgRef.current;
    const base = svg?.parentElement?.querySelector('svg[data-cephalo-viewport="base"]');
    const matrix = svg?.getScreenCTM();
    if (!svg || !base || !matrix) return;
    type Box = { left: number; right: number; top: number; bottom: number };
    const labels = Array.from(svg.querySelectorAll<SVGTextElement>('[data-cephalo-overlay-label]'));
    const baseBoxes = Array.from(base.querySelectorAll<SVGTextElement>('[data-cephalo-landmark-label]'))
      .map(node => node.getBoundingClientRect());
    const placed: Box[] = [];
    const next: Record<string, { x: number; y: number }> = {};
    const screen = svg.getBoundingClientRect();
    const intersects = (a: Box, b: Box) =>
      Math.min(a.right,b.right)-Math.max(a.left,b.left) > -2
      && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top) > -2;
    const alternatives = [
      { x: 50, y: -34 }, { x: -50, y: -34 },
      { x: 40, y: 34 }, { x: -50, y: 34 },
      { x: 5, y: -52 }, { x: 5, y: 55 },
      { x: 75, y: -45 }, { x: -75, y: -45 },
      { x: 75, y: 44 }, { x: -75, y: 44 },
      { x: 105, y: -5 }, { x: -105, y: -5 },
      { x: 105, y: 57 }, { x: -105, y: 57 },
      { x: 0, y: -82 }, { x: 0, y: 85 },
    ];
    for (const text of labels) {
      const id = (text.getAttribute('data-cephalo-overlay-label') || '').toLowerCase();
      const marker = text.parentElement?.querySelector('circle[cx][cy]');
      if (!marker || !id) continue;
      const x = Number(marker.getAttribute('cx'));
      const y = Number(marker.getAttribute('cy'));
      const currentX = Number(text.getAttribute('x'));
      const currentY = Number(text.getAttribute('y'));
      if (![x,y,currentX,currentY].every(Number.isFinite)) continue;
      const rendered = text.getBoundingClientRect();
      const preferred = id === 'a' ? { x: 62/3, y: -38/3 }
        : id === 'b' ? { x: 60/3, y: 40/3 } : { x: 5, y: -6 };
      const possibilities = [preferred, ...alternatives];
      let choice = possibilities[0];
      let chosenBox: Box | null = null;
      for (const offset of possibilities) {
        const dx = x + offset.x * labelUnit - currentX;
        const dy = y + offset.y * labelUnit - currentY;
        const pixelX = matrix.a * dx + matrix.c * dy;
        const pixelY = matrix.b * dx + matrix.d * dy;
        const candidate: Box = { left: rendered.left+pixelX, right: rendered.right+pixelX,
          top: rendered.top+pixelY, bottom: rendered.bottom+pixelY };
        if (candidate.left < screen.left+2 || candidate.right > screen.right-2
          || candidate.top < screen.top+2 || candidate.bottom > screen.bottom-2) continue;
        if (baseBoxes.some(box => intersects(candidate,box)) || placed.some(box => intersects(candidate,box))) continue;
        choice = offset;
        chosenBox = candidate;
        break;
      }
      next[id] = choice;
      if (chosenBox) placed.push(chosenBox);
    }
    setComLabelOffsets(previous => {
      const same = Object.keys(previous).length === Object.keys(next).length
        && Object.entries(next).every(([id,p]) =>
          previous[id]?.x === p.x && previous[id]?.y === p.y);
      return same ? previous : next;
    });
  }, [mode, props.compactLabels, props.landmarks, props.imageWidth, props.imageHeight,
      props.viewZoom, props.viewPan?.x, props.viewPan?.y, labelUnit, comLabelOffsets]);

  const baseGhosts = React.useMemo<GhostData[]>(
    () => mode === 'com'
      ? filteredGhosts.map(ghost => ({
          ...ghost,
          landmarks: ghost.landmarks.filter(item => !COM_BASE_SUPPRESSED_LANDMARKS.has(item.id.toLowerCase())),
        }))
      : filteredGhosts,
    [filteredGhosts, mode],
  );

  const mergeLandmarkUpdate = React.useCallback((updatedSubset: Landmark[]) => {
    if (mode === 'all') {
      props.onUpdateLandmarks(updatedSubset);
      return;
    }
    const updates = new Map(updatedSubset.map(item => [item.id.toLowerCase(), item]));
    const merged = props.landmarks.map(item => updates.get(item.id.toLowerCase()) ?? item);
    const existing = new Set(props.landmarks.map(item => item.id.toLowerCase()));
    for (const item of updatedSubset) {
      if (!existing.has(item.id.toLowerCase())) merged.push(item);
    }
    props.onUpdateLandmarks(merged);
  }, [mode, props.landmarks, props.onUpdateLandmarks]);

  const baseAnalysis = mode === 'ricketts' ? 'esthetique' : mode === 'com' ? 'wits' : mode;

  const po = findPointAny(props.landmarks, 'Po', 'Porion');
  const orPoint = findPointAny(props.landmarks, 'Or', 'Orbitale');
  const n = findPointAny(props.landmarks, 'N', 'Nasion');
  const s = findPointAny(props.landmarks, 'S', 'Sella');
  const pog = findPointAny(props.landmarks, 'Pog');
  const a = findPointAny(props.landmarks, 'A', 'Point_A');
  const b = findPointAny(props.landmarks, 'B', 'Point_B');
  const go = findPointAny(props.landmarks, 'Go', 'Gonion');
  const me = findPointAny(props.landmarks, 'Me', 'Menton');
  const u1i = findPointAny(props.landmarks, 'U1_incisal', 'U1i');
  const u1a = findPointAny(props.landmarks, 'U1_apex', 'U1a');
  const l1i = findPointAny(props.landmarks, 'L1_incisal', 'L1i');
  const l1a = findPointAny(props.landmarks, 'L1_apex', 'L1a');

  const aOnNPog = a && n && pog
    ? projectPointOnLine(a.x, a.y, n.x, n.y, pog.x, pog.y)
    : null;

  const frankfort = unitAxis(po, orPoint);
  const frankfortPerp = frankfort
    ? (() => {
        let x = -frankfort.y;
        let y = frankfort.x;
        if (y < 0) { x = -x; y = -y; }
        return { x, y };
      })()
    : null;

  const nVerticalStart = n && frankfortPerp
    ? { x: n.x - frankfortPerp.x * props.imageHeight, y: n.y - frankfortPerp.y * props.imageHeight }
    : null;
  const nVerticalEnd = n && frankfortPerp
    ? { x: n.x + frankfortPerp.x * props.imageHeight, y: n.y + frankfortPerp.y * props.imageHeight }
    : null;

  const projectOnNVertical = (point?: Landmark) =>
    point && nVerticalStart && nVerticalEnd
      ? projectPointOnLine(point.x, point.y, nVerticalStart.x, nVerticalStart.y, nVerticalEnd.x, nVerticalEnd.y)
      : null;

  const aOnNVertical = projectOnNVertical(a);
  const bOnNVertical = projectOnNVertical(b);
  const sOnNVertical = projectOnNVertical(s);
  const aPrime = a && po && orPoint ? projectPointOnLine(a.x, a.y, po.x, po.y, orPoint.x, orPoint.y) : null;
  const bPrime = b && po && orPoint ? projectPointOnLine(b.x, b.y, po.x, po.y, orPoint.x, orPoint.y) : null;

  const incisalVector = u1i && l1i ? { x: u1i.x - l1i.x, y: u1i.y - l1i.y } : null;
  const overjetEnd = l1i && frankfort && incisalVector
    ? (() => {
        const amount = incisalVector.x * frankfort.x + incisalVector.y * frankfort.y;
        return { x: l1i.x + frankfort.x * amount, y: l1i.y + frankfort.y * amount };
      })()
    : null;

  const showRickettsHard = mode === 'ricketts' || mode === 'all';
  const showRickettsMarkers = mode === 'ricketts';
  const showCom = mode === 'com';
  const hasCanonicalFocus = showCom && metricFocus?.authority === 'LOT06_EXECUTABLE_MEASUREMENT_CONTRACT';
  const focusedConstructionIds = new Set(metricFocus?.constructionIds ?? []);
  const focusedPointIds = new Set((metricFocus?.points ?? []).map(id => id.toLowerCase()));
  const comStyle = (requirements: { constructions?: string[]; points?: string[] }, geometryKey: string) => {
    const constructionMatch = !(requirements.constructions?.length)
      || requirements.constructions.every(id => focusedConstructionIds.has(id));
    const pointMatch = !(requirements.points?.length)
      || requirements.points.every(id => focusedPointIds.has(id.toLowerCase()));
    const active = !hasCanonicalFocus || (constructionMatch && pointMatch);
    return {
      stroke: cephaloGeometryColor(geometryKey),
      opacity: layerVisible('plans') ? (active ? 0.96 : 0.16) * layerOpacity('plans') : 0,
      strokeWidth: active && hasCanonicalFocus ? 2.6 : 1.7,
    };
  };

  return (
    <div className="absolute inset-0 z-20 h-full w-full" data-cephalo-analysis={mode}>
      <BaseCephaloTracingLayer
        {...props}
        landmarks={baseLandmarks}
        ghosts={baseGhosts}
        onUpdateLandmarks={mergeLandmarkUpdate}
        activeAnalysis={baseAnalysis}
        hoveredMetric={metricFocus ?? props.hoveredMetric ?? null}
      />

      {(showRickettsHard || showCom) && (layerVisible('plans') || layerVisible('landmarks') || layerVisible('measurements')) && props.imageWidth > 0 && props.imageHeight > 0 && (
        <svg
          ref={overlaySvgRef}
          data-cephalo-viewport="analysis"
          viewBox={overlayViewBox}
          preserveAspectRatio="xMidYMid meet"
          className="pointer-events-none absolute inset-0 z-[28] h-full w-full"
          aria-hidden="true"
        >
          {layerVisible('plans') && showRickettsHard && po && orPoint && (
            <line
              data-r18-construction="ricketts-frankfort"
              x1={po.x} y1={po.y} x2={orPoint.x} y2={orPoint.y}
              stroke={cephaloGeometryColor('fh')} strokeWidth="1.6" strokeDasharray="8,4"
              opacity={0.9 * layerOpacity('plans')} vectorEffect="non-scaling-stroke"
            />
          )}
          {layerVisible('plans') && showRickettsHard && n && pog && (
            <line
              data-r18-construction="ricketts-n-pog"
              x1={n.x} y1={n.y} x2={pog.x} y2={pog.y}
              stroke={cephaloGeometryColor('npog')} strokeWidth="1.8"
              opacity={0.92 * layerOpacity('plans')} vectorEffect="non-scaling-stroke"
            />
          )}
          {layerVisible('plans') && showRickettsHard && a && aOnNPog && (
            <line
              data-r18-construction="ricketts-convexity"
              x1={a.x} y1={a.y} x2={aOnNPog.x} y2={aOnNPog.y}
              stroke={cephaloGeometryColor('convexity')} strokeWidth="1.6" strokeDasharray="3,3"
              opacity={0.95 * layerOpacity('plans')} vectorEffect="non-scaling-stroke"
            />
          )}
          {layerVisible('landmarks') && showRickettsMarkers && [po, orPoint, n, pog, a].filter(Boolean).map(point => {
            const p = point as Landmark;
            return (
              <g key={`ricketts-${p.id}`} data-r18-point={p.id} opacity={layerOpacity('landmarks')}>
                <circle cx={p.x} cy={p.y} r="3.4" fill={P.bgInput} stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
                <text x={p.x + 10} y={p.y - 10} fill={P.text} fontSize="10" fontWeight="800">{p.id}</text>
              </g>
            );
          })}

          {showCom && po && orPoint && (() => {
            const style = comStyle({ constructions: ['FH_PO_OR_V1'] }, 'fh');
            return <line data-r19-construction="com-frankfort" x1={po.x} y1={po.y} x2={orPoint.x} y2={orPoint.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && go && me && (() => {
            const style = comStyle({ constructions: ['TWEED_DC_MP_GO_ME_V1'] }, 'mp');
            return <line data-r19-construction="com-mandibular" x1={go.x} y1={go.y} x2={me.x} y2={me.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && u1a && u1i && (() => {
            const style = comStyle({ points: ['U1_apex', 'U1_incisal'] }, 'u1');
            return <line data-r19-construction="com-u1-axis" x1={u1a.x} y1={u1a.y} x2={u1i.x} y2={u1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && l1a && l1i && (() => {
            const style = comStyle({ points: ['L1_apex', 'L1_incisal'] }, 'l1');
            return <line data-r19-construction="com-l1-axis" x1={l1a.x} y1={l1a.y} x2={l1i.x} y2={l1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && nVerticalStart && nVerticalEnd && (() => {
            const style = comStyle({ constructions: ['NASION_VERTICAL_FH_V1'] }, 'mcnamara_perp');
            return <line data-r19-construction="com-nasion-vertical" x1={nVerticalStart.x} y1={nVerticalStart.y} x2={nVerticalEnd.x} y2={nVerticalEnd.y} strokeDasharray="7,5" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && a && aOnNVertical && (() => {
            const style = comStyle({ constructions: ['NASION_VERTICAL_FH_V1'], points: ['A'] }, 'situation_a');
            return <line data-r19-construction="com-situation-a" x1={a.x} y1={a.y} x2={aOnNVertical.x} y2={aOnNVertical.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && b && bOnNVertical && (() => {
            const style = comStyle({ constructions: ['NASION_VERTICAL_FH_V1'], points: ['B'] }, 'situation_b');
            return <line data-r19-construction="com-situation-b" x1={b.x} y1={b.y} x2={bOnNVertical.x} y2={bOnNVertical.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && s && sOnNVertical && (() => {
            const style = comStyle({ constructions: ['CRANIOM_S_TO_N_VERTICAL_DEPTH_V1'] }, 'facial_depth');
            return <line data-r19-construction="com-facial-depth" x1={s.x} y1={s.y} x2={sOnNVertical.x} y2={sOnNVertical.y} strokeDasharray="4,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && a && aPrime && (() => {
            const style = comStyle({ constructions: ['CRANIOM_AB_PRIME_V1'], points: ['A'] }, 'a_prime');
            return <line data-r19-construction="com-a-prime-drop" x1={a.x} y1={a.y} x2={aPrime.x} y2={aPrime.y} strokeDasharray="3,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && b && bPrime && (() => {
            const style = comStyle({ constructions: ['CRANIOM_AB_PRIME_V1'], points: ['B'] }, 'b_prime');
            return <line data-r19-construction="com-b-prime-drop" x1={b.x} y1={b.y} x2={bPrime.x} y2={bPrime.y} strokeDasharray="3,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && aPrime && bPrime && (() => {
            const style = comStyle({ constructions: ['CRANIOM_AB_PRIME_V1'] }, 'ab_prime');
            return <line data-r19-construction="com-ab-prime" x1={aPrime.x} y1={aPrime.y} x2={bPrime.x} y2={bPrime.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && l1i && overjetEnd && (() => {
            const style = comStyle({}, 'overjet');
            return <line data-r19-construction="com-overjet" x1={l1i.x} y1={l1i.y} x2={overjetEnd.x} y2={overjetEnd.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && u1i && overjetEnd && (() => {
            const style = comStyle({}, 'overbite');
            return <line data-r19-construction="com-overbite" x1={overjetEnd.x} y1={overjetEnd.y} x2={u1i.x} y2={u1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}

          {layerVisible('landmarks') && showCom && [po, orPoint, n, s, a, b, go, me, u1i, u1a, l1i, l1a].filter(Boolean).map(point => {
            const p = point as Landmark;
            const overlayOnly = !baseLandmarks.some(base => base.id.toLowerCase() === p.id.toLowerCase());
            // Label-only separation from the main SVG reticles. Never move the COM marker or geometry.
            const desktopOffset = p.id.toLowerCase() === 'a' ? { x: 62, y: -38 }
              : p.id.toLowerCase() === 'b' ? { x: 60, y: 40 }
              : { x: 15, y: -18 };
            const offsetPx = comLabelOffsets[p.id.toLowerCase()] ?? { x: desktopOffset.x/3, y: desktopOffset.y/3 };
            const labelOffset = props.compactLabels && overlayOnly
              ? { x: offsetPx.x * labelUnit, y: offsetPx.y * labelUnit }
              : { x: 8, y: -8 };
            return (
              <g key={`com-${p.id}`} data-r19-point={p.id} opacity={(hasCanonicalFocus ? 0.82 : 0.92) * layerOpacity('landmarks')}>
                {overlayOnly && <title>{p.id}</title>}
                <circle cx={p.x} cy={p.y} r="3.2" fill={P.bgInput} stroke={P.text} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
                {(!props.compactLabels || overlayOnly) && (
                  <text data-cephalo-overlay-label={p.id} x={p.x + labelOffset.x} y={p.y + labelOffset.y}
                    fill={P.text} fontSize={props.compactLabels ? 14 * labelUnit : 9} fontWeight="800"
                    style={props.compactLabels ? { paintOrder: 'stroke', stroke: P.bgInput, strokeWidth: '4px', strokeLinejoin: 'round' } : undefined}
                  >{p.id}</text>
                )}
              </g>
            );
          })}
          {layerVisible('measurements') && showCom && aPrime && <text opacity={layerOpacity('measurements')} data-r19-construction="com-a-prime-label" x={aPrime.x + 7} y={aPrime.y - 7} fill={CEPHALO_SCIENTIFIC_COLORS.skeletal} fontSize="9" fontWeight="800">A′</text>}
          {layerVisible('measurements') && showCom && bPrime && <text opacity={layerOpacity('measurements')} data-r19-construction="com-b-prime-label" x={bPrime.x + 7} y={bPrime.y + 13} fill={CEPHALO_SCIENTIFIC_COLORS.skeletal} fontSize="9" fontWeight="800">B′</text>}
        </svg>
      )}

      <div className="pointer-events-none absolute inset-x-0 top-36 z-40 flex justify-center px-3 sm:top-16">
        <div
          aria-label="Analyse du tracé"
          className="pointer-events-auto flex max-w-full items-center gap-0.5 overflow-x-auto rounded-2xl border p-1 shadow-2xl backdrop-blur-xl sm:gap-1"
          style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}
        >
          <span className="hidden shrink-0 px-2 text-[9px] font-black uppercase tracking-[0.18em] 2xl:inline" style={{ color: P.textDim }}>Tracé</span>
          {ANALYSIS_OPTIONS.map(option => {
            const selected = mode === option.id;
            return (
              <button
                key={option.id}
                type="button"
                data-analysis={option.id}
                aria-pressed={selected}
                onClick={() => setMode(option.id)}
                className="shrink-0 rounded-xl border px-2 py-1.5 text-[8px] font-black uppercase tracking-[0.04em] transition-all sm:px-2 sm:text-[9px] sm:tracking-[0.04em] 2xl:px-3 2xl:text-[10px]"
                style={{
                  background: selected ? `${P.accent}18` : 'transparent',
                  borderColor: selected ? P.borderFocus : 'transparent',
                  color: selected ? P.text : P.textMuted,
                  boxShadow: selected ? `0 0 0 1px ${P.accent}14` : 'none',
                }}
              >
                {option.shortLabel ? (
                  <>
                    <span className="sm:hidden">{option.shortLabel}</span>
                    <span className="hidden sm:inline">{option.label}</span>
                  </>
                ) : option.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};