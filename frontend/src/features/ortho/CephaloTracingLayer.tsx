import React from 'react';
import { CephaloTracingLayer as BaseCephaloTracingLayer } from './CephaloTracingLayerBase';
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
  ]),
  tweed: new Set([
    'po', 'or', 'go', 'me',
    'u1_incisal', 'u1i', 'u1_apex', 'u1a',
    'l1_incisal', 'l1i', 'l1_apex', 'l1a',
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
  const [mode, setMode] = React.useState<AnalysisMode>(() => normalizeMode(props.activeAnalysis));
  const [metricFocus, setMetricFocus] = React.useState<CephaloMetricFocus | null>(props.hoveredMetric ?? null);

  React.useEffect(() => {
    if (props.activeAnalysis) setMode(normalizeMode(props.activeAnalysis));
  }, [props.activeAnalysis]);

  React.useEffect(() => {
    publishCephaloAnalysis(mode);
  }, [mode]);

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
  const focusedKey = showCom ? metricFocus?.key ?? null : null;
  const comStyle = (keys: string[], geometryKey: string) => {
    const active = !focusedKey || keys.includes(focusedKey);
    return {
      stroke: cephaloGeometryColor(geometryKey),
      opacity: active ? 0.96 : 0.16,
      strokeWidth: active && focusedKey ? 2.6 : 1.7,
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

      {(showRickettsHard || showCom) && props.imageWidth > 0 && props.imageHeight > 0 && (
        <svg
          viewBox={`0 0 ${props.imageWidth} ${props.imageHeight}`}
          preserveAspectRatio="xMidYMid meet"
          className="pointer-events-none absolute inset-0 z-[28] h-full w-full"
          aria-hidden="true"
        >
          {showRickettsHard && po && orPoint && (
            <line
              data-r18-construction="ricketts-frankfort"
              x1={po.x} y1={po.y} x2={orPoint.x} y2={orPoint.y}
              stroke={cephaloGeometryColor('fh')} strokeWidth="1.6" strokeDasharray="8,4"
              opacity="0.9" vectorEffect="non-scaling-stroke"
            />
          )}
          {showRickettsHard && n && pog && (
            <line
              data-r18-construction="ricketts-n-pog"
              x1={n.x} y1={n.y} x2={pog.x} y2={pog.y}
              stroke={cephaloGeometryColor('npog')} strokeWidth="1.8"
              opacity="0.92" vectorEffect="non-scaling-stroke"
            />
          )}
          {showRickettsHard && a && aOnNPog && (
            <line
              data-r18-construction="ricketts-convexity"
              x1={a.x} y1={a.y} x2={aOnNPog.x} y2={aOnNPog.y}
              stroke={cephaloGeometryColor('convexity')} strokeWidth="1.6" strokeDasharray="3,3"
              opacity="0.95" vectorEffect="non-scaling-stroke"
            />
          )}
          {showRickettsMarkers && [po, orPoint, n, pog, a].filter(Boolean).map(point => {
            const p = point as Landmark;
            return (
              <g key={`ricketts-${p.id}`} data-r18-point={p.id}>
                <circle cx={p.x} cy={p.y} r="3.4" fill={P.bgInput} stroke={CEPHALO_SCIENTIFIC_COLORS.skeletal} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
                <text x={p.x + 10} y={p.y - 10} fill={P.text} fontSize="10" fontWeight="800">{p.id}</text>
              </g>
            );
          })}

          {showCom && po && orPoint && (() => {
            const style = comStyle(['I_Francfort','Angle_de_Tweed','Situation_A','Situation_B','Profondeur_Faciale','Decalage_A_B','Surplomb','Recouvrement'], 'fh');
            return <line data-r19-construction="com-frankfort" x1={po.x} y1={po.y} x2={orPoint.x} y2={orPoint.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && go && me && (() => {
            const style = comStyle(['IMPA','Angle_de_Tweed'], 'mp');
            return <line data-r19-construction="com-mandibular" x1={go.x} y1={go.y} x2={me.x} y2={me.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && u1a && u1i && (() => {
            const style = comStyle(['I_Francfort','Inter_Incisif'], 'u1');
            return <line data-r19-construction="com-u1-axis" x1={u1a.x} y1={u1a.y} x2={u1i.x} y2={u1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && l1a && l1i && (() => {
            const style = comStyle(['IMPA','Inter_Incisif'], 'l1');
            return <line data-r19-construction="com-l1-axis" x1={l1a.x} y1={l1a.y} x2={l1i.x} y2={l1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && nVerticalStart && nVerticalEnd && (() => {
            const style = comStyle(['Situation_A','Situation_B','Profondeur_Faciale'], 'mcnamara_perp');
            return <line data-r19-construction="com-nasion-vertical" x1={nVerticalStart.x} y1={nVerticalStart.y} x2={nVerticalEnd.x} y2={nVerticalEnd.y} strokeDasharray="7,5" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && a && aOnNVertical && (() => {
            const style = comStyle(['Situation_A'], 'situation_a');
            return <line data-r19-construction="com-situation-a" x1={a.x} y1={a.y} x2={aOnNVertical.x} y2={aOnNVertical.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && b && bOnNVertical && (() => {
            const style = comStyle(['Situation_B'], 'situation_b');
            return <line data-r19-construction="com-situation-b" x1={b.x} y1={b.y} x2={bOnNVertical.x} y2={bOnNVertical.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && s && sOnNVertical && (() => {
            const style = comStyle(['Profondeur_Faciale'], 'facial_depth');
            return <line data-r19-construction="com-facial-depth" x1={s.x} y1={s.y} x2={sOnNVertical.x} y2={sOnNVertical.y} strokeDasharray="4,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && a && aPrime && (() => {
            const style = comStyle(['Decalage_A_B'], 'a_prime');
            return <line data-r19-construction="com-a-prime-drop" x1={a.x} y1={a.y} x2={aPrime.x} y2={aPrime.y} strokeDasharray="3,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && b && bPrime && (() => {
            const style = comStyle(['Decalage_A_B'], 'b_prime');
            return <line data-r19-construction="com-b-prime-drop" x1={b.x} y1={b.y} x2={bPrime.x} y2={bPrime.y} strokeDasharray="3,3" {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && aPrime && bPrime && (() => {
            const style = comStyle(['Decalage_A_B'], 'ab_prime');
            return <line data-r19-construction="com-ab-prime" x1={aPrime.x} y1={aPrime.y} x2={bPrime.x} y2={bPrime.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && l1i && overjetEnd && (() => {
            const style = comStyle(['Surplomb'], 'overjet');
            return <line data-r19-construction="com-overjet" x1={l1i.x} y1={l1i.y} x2={overjetEnd.x} y2={overjetEnd.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}
          {showCom && u1i && overjetEnd && (() => {
            const style = comStyle(['Recouvrement'], 'overbite');
            return <line data-r19-construction="com-overbite" x1={overjetEnd.x} y1={overjetEnd.y} x2={u1i.x} y2={u1i.y} {...style} vectorEffect="non-scaling-stroke" />;
          })()}

          {showCom && [po, orPoint, n, s, a, b, go, me, u1i, u1a, l1i, l1a].filter(Boolean).map(point => {
            const p = point as Landmark;
            return (
              <g key={`com-${p.id}`} data-r19-point={p.id} opacity={focusedKey ? 0.82 : 0.92}>
                <circle cx={p.x} cy={p.y} r="3.2" fill={P.bgInput} stroke={P.text} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
                <text x={p.x + 8} y={p.y - 8} fill={P.text} fontSize="9" fontWeight="800">{p.id}</text>
              </g>
            );
          })}
          {showCom && aPrime && <text data-r19-construction="com-a-prime-label" x={aPrime.x + 7} y={aPrime.y - 7} fill={CEPHALO_SCIENTIFIC_COLORS.skeletal} fontSize="9" fontWeight="800">A′</text>}
          {showCom && bPrime && <text data-r19-construction="com-b-prime-label" x={bPrime.x + 7} y={bPrime.y + 13} fill={CEPHALO_SCIENTIFIC_COLORS.skeletal} fontSize="9" fontWeight="800">B′</text>}
        </svg>
      )}

      <div className="pointer-events-none absolute inset-x-0 top-36 z-40 flex justify-center px-3 sm:top-16">
        <div
          aria-label="Analyse du tracé"
          className="pointer-events-auto flex max-w-full items-center gap-0.5 overflow-x-auto rounded-2xl border p-1 shadow-2xl backdrop-blur-xl sm:gap-1"
          style={{ background: P.bgPanel, borderColor: P.border, boxShadow: P.shadowLg }}
        >
          <span className="hidden shrink-0 px-2 text-[9px] font-black uppercase tracking-[0.18em] sm:inline" style={{ color: P.textDim }}>Tracé</span>
          {ANALYSIS_OPTIONS.map(option => {
            const selected = mode === option.id;
            return (
              <button
                key={option.id}
                type="button"
                data-analysis={option.id}
                aria-pressed={selected}
                onClick={() => setMode(option.id)}
                className="shrink-0 rounded-xl border px-2 py-1.5 text-[8px] font-black uppercase tracking-[0.04em] transition-all sm:px-3 sm:text-[10px] sm:tracking-[0.08em]"
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