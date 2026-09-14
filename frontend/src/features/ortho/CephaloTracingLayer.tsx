import React from 'react';
import { CephaloTracingLayer as BaseCephaloTracingLayer } from './CephaloTracingLayerBase';
import type { CephaloTracingLayerProps, GhostData, TracingUIMode } from './CephaloTracingLayerBase';
import type { Landmark } from './cephaloShared';
import { projectPointOnLine } from './cephaloMath';

export type { CephaloTracingLayerProps, GhostData, TracingUIMode };

type AnalysisMode = 'all' | 'steiner' | 'tweed' | 'mcnamara' | 'ricketts';

const ANALYSIS_OPTIONS: Array<{ id: AnalysisMode; label: string }> = [
  { id: 'all', label: 'Tous' },
  { id: 'steiner', label: 'Steiner' },
  { id: 'tweed', label: 'Tweed' },
  { id: 'mcnamara', label: 'McNamara / COM' },
  { id: 'ricketts', label: 'Ricketts' },
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
    'occ_ant', 'occ_post',
  ]),
  ricketts: new Set([
    'g_soft', 'g-soft', 'n_soft', 'n-soft', 'prn', 'nose_tip', 'cm',
    'sn_soft', 'sn', 'a_soft', 'ls_soft', 'ls', 'ls2', 'ul', 'upper_lip',
    'st', 'stomion', 'li2', 'li_soft', 'li', 'll', 'lower_lip',
    'b_soft', 'pog_soft', 'stpog', 'soft_pogonion', 'me_soft', 'soft_menton',
  ]),
};

const normalizeMode = (value?: string): AnalysisMode => {
  const normalized = (value || 'all').trim().toLowerCase();
  if (normalized === 'steiner') return 'steiner';
  if (normalized === 'tweed') return 'tweed';
  if (normalized === 'mcnamara' || normalized === 'com') return 'mcnamara';
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

/**
 * R18 scientific tracing controller.
 *
 * The historical tracing engine is preserved byte-for-byte in
 * CephaloTracingLayerBase.tsx. This controller constrains the landmarks given
 * to that engine so each selected analysis can only materialize its own
 * constructions. Ricketts hard-tissue constructions are drawn here because
 * the legacy engine only contained its soft-tissue profile/E-line surface.
 */
export const CephaloTracingLayer: React.FC<CephaloTracingLayerProps> = (props) => {
  const [mode, setMode] = React.useState<AnalysisMode>(() => normalizeMode(props.activeAnalysis));

  React.useEffect(() => {
    if (props.activeAnalysis) setMode(normalizeMode(props.activeAnalysis));
  }, [props.activeAnalysis]);

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

  const baseAnalysis = mode === 'ricketts' ? 'esthetique' : mode;

  const po = findPoint(props.landmarks, 'Po');
  const orPoint = findPoint(props.landmarks, 'Or');
  const n = findPoint(props.landmarks, 'N');
  const pog = findPoint(props.landmarks, 'Pog');
  const a = findPoint(props.landmarks, 'A');
  const occAnt = findPoint(props.landmarks, 'Occ_Ant');
  const occPost = findPoint(props.landmarks, 'Occ_Post');

  const aOnNPog = a && n && pog
    ? projectPointOnLine(a.x, a.y, n.x, n.y, pog.x, pog.y)
    : null;

  const showRickettsHard = mode === 'ricketts' || mode === 'all';
  const showRickettsMarkers = mode === 'ricketts';
  const showComWits = mode === 'mcnamara';

  return (
    <div className="absolute inset-0 z-20 h-full w-full" data-cephalo-analysis={mode}>
      <BaseCephaloTracingLayer
        {...props}
        landmarks={filteredLandmarks}
        ghosts={filteredGhosts}
        onUpdateLandmarks={mergeLandmarkUpdate}
        activeAnalysis={baseAnalysis}
      />

      {(showRickettsHard || showComWits) && props.imageWidth > 0 && props.imageHeight > 0 && (
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
              stroke="#67e8f9" strokeWidth="1.6" strokeDasharray="8,4"
              opacity="0.9" vectorEffect="non-scaling-stroke"
            />
          )}
          {showRickettsHard && n && pog && (
            <line
              data-r18-construction="ricketts-n-pog"
              x1={n.x} y1={n.y} x2={pog.x} y2={pog.y}
              stroke="#f472b6" strokeWidth="1.8"
              opacity="0.92" vectorEffect="non-scaling-stroke"
            />
          )}
          {showRickettsHard && a && aOnNPog && (
            <line
              data-r18-construction="ricketts-convexity"
              x1={a.x} y1={a.y} x2={aOnNPog.x} y2={aOnNPog.y}
              stroke="#f472b6" strokeWidth="1.6" strokeDasharray="3,3"
              opacity="0.95" vectorEffect="non-scaling-stroke"
            />
          )}

          {showRickettsMarkers && [po, orPoint, n, pog, a].filter(Boolean).map(point => {
            const p = point as Landmark;
            return (
              <g key={`ricketts-${p.id}`} data-r18-point={p.id}>
                <circle cx={p.x} cy={p.y} r="3.4" fill="#ffffff" stroke="#f472b6" strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
                <text x={p.x + 10} y={p.y - 10} fill="#fbcfe8" fontSize="10" fontWeight="800">{p.id}</text>
              </g>
            );
          })}

          {showComWits && occPost && occAnt && (
            <g data-r18-construction="com-wits-occlusal">
              <line
                x1={occPost.x} y1={occPost.y} x2={occAnt.x} y2={occAnt.y}
                stroke="#facc15" strokeWidth="1.7" strokeDasharray="5,4"
                opacity="0.92" vectorEffect="non-scaling-stroke"
              />
              <text
                x={(occPost.x + occAnt.x) / 2 + 10}
                y={(occPost.y + occAnt.y) / 2 - 10}
                fill="#fde68a" fontSize="10" fontWeight="800"
              >Wits</text>
            </g>
          )}
        </svg>
      )}

      <div className="pointer-events-none absolute inset-x-0 top-36 z-40 flex justify-center px-3 sm:top-16">
        <div
          aria-label="Analyse du tracé"
          className="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-2xl border border-slate-700/70 bg-slate-950/80 p-1 shadow-2xl backdrop-blur-xl"
        >
          <span className="hidden shrink-0 px-2 text-[9px] font-black uppercase tracking-[0.18em] text-slate-500 sm:inline">Tracé</span>
          {ANALYSIS_OPTIONS.map(option => {
            const selected = mode === option.id;
            return (
              <button
                key={option.id}
                type="button"
                data-analysis={option.id}
                aria-pressed={selected}
                onClick={() => setMode(option.id)}
                className={`shrink-0 rounded-xl px-2.5 py-1.5 text-[9px] font-black uppercase tracking-[0.08em] transition-all sm:px-3 sm:text-[10px] ${selected
                  ? 'border border-cyan-400/45 bg-cyan-400/15 text-cyan-100 shadow-[0_0_18px_rgba(34,211,238,0.12)]'
                  : 'border border-transparent text-slate-400 hover:bg-slate-800/80 hover:text-slate-100'}`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
