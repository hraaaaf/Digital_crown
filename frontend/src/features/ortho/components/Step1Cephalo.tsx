import React from 'react';
import { Step1Cephalo as Step1CephaloBase } from './Step1CephaloBase';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_ANALYSIS_CHANGE_EVENT,
  type CephaloAnalysisMode,
} from '../cephaloAnalysisBridge';
import { CEPHALO_SCIENTIFIC_COLORS } from '../cephaloVisualSemantics';

interface ThemePalette {
  bg: string;
  bgPanel: string;
  bgCard: string;
  bgInput: string;
  border: string;
  borderFocus: string;
  text: string;
  textMuted: string;
  textDim: string;
  accent: string;
  accentSuccess: string;
  accentWarning: string;
  accentError: string;
  shadow: string;
  shadowLg: string;
}

interface Step1CephaloProps {
  P: ThemePalette;
  fileRef: React.RefObject<HTMLInputElement | null>;
  step1ContainerRef: React.RefObject<HTMLDivElement | null>;
}

const ANALYSIS_LABELS: Record<CephaloAnalysisMode, string> = {
  all: 'Toutes analyses',
  steiner: 'Steiner',
  tweed: 'Tweed',
  mcnamara: 'McNamara',
  com: 'COM',
  ricketts: 'Ricketts',
};

const FAMILY_LEGEND = [
  ['skeletal', 'Squelettique'],
  ['dental', 'Dentaire'],
  ['soft_tissue', 'Tissus mous'],
  ['reference', 'Références'],
] as const;

/**
 * R20 workbench composition.
 *
 * Scientific/clinical behavior stays in the existing R18/R19 components.
 * This wrapper only reorganizes real controls into a left utility rail,
 * keeps the radiograph as the dominant central surface, and preserves the
 * real measure panel on the right. On narrow screens the rail collapses to a
 * compact horizontal control strip so the radiograph remains immediately
 * visible instead of being pushed down by a desktop-style card.
 */
export const Step1Cephalo: React.FC<Step1CephaloProps> = (props) => {
  const hasImage = useOrthoStore(state => Boolean(state.imageSrc));
  const magnifierEnabled = useOrthoStore(state => state.magnifierEnabled);
  const setMagnifierEnabled = useOrthoStore(state => state.setMagnifierEnabled);
  const vtoSettings = useOrthoStore(state => state.vtoSettings);
  const setVtoSettings = useOrthoStore(state => state.setVtoSettings);
  const activeMorphing = useOrthoStore(state => state.activeMorphing);
  const setActiveMorphing = useOrthoStore(state => state.setActiveMorphing);
  const [analysis, setAnalysis] = React.useState<CephaloAnalysisMode>('all');

  React.useEffect(() => {
    const onAnalysis = (event: Event) => {
      const value = (event as CustomEvent<CephaloAnalysisMode>).detail;
      if (value) setAnalysis(value);
    };
    window.addEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysis as EventListener);
    return () => window.removeEventListener(CEPHALO_ANALYSIS_CHANGE_EVENT, onAnalysis as EventListener);
  }, []);

  if (!hasImage) return <Step1CephaloBase {...props} />;

  const toggleClass = (active: boolean) =>
    `min-h-9 shrink-0 whitespace-nowrap rounded-xl border px-3 py-2 text-[10px] font-bold transition-all xl:min-h-10 xl:w-full xl:text-left xl:text-[11px] ${active ? 'shadow-sm' : ''}`;

  const toggleStyle = (active: boolean): React.CSSProperties => ({
    background: active ? props.P.bgCard : props.P.bgInput,
    borderColor: active ? props.P.borderFocus : props.P.border,
    color: active ? props.P.text : props.P.textMuted,
  });

  return (
    <div
      data-r19-reference-layout
      data-r20-workbench-layout
      className="grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-[168px_minmax(0,1fr)_minmax(332px,0.72fr)] xl:items-stretch"
    >
      <aside
        data-r20-workbench-sidebar
        aria-label="Contrôles du workbench céphalométrique"
        className="min-w-0 rounded-2xl border p-2 xl:h-[80vh] xl:overflow-y-auto xl:p-3"
        style={{ background: props.P.bgPanel, borderColor: props.P.border, boxShadow: props.P.shadow }}
      >
        <div className="hidden xl:block">
          <div className="min-w-0">
            <p className="text-[9px] font-black uppercase tracking-[0.16em]" style={{ color: props.P.textDim }}>Workbench</p>
            <h3 className="mt-1 truncate text-sm font-black" style={{ color: props.P.text }}>{ANALYSIS_LABELS[analysis]}</h3>
          </div>
          <span className="mt-2 inline-flex rounded-full border px-2 py-1 text-[9px] font-black uppercase tracking-wide" style={{ borderColor: props.P.border, color: props.P.textMuted }}>
            Analyse active
          </span>
        </div>

        <div className="mt-3 hidden space-y-2 xl:block" aria-label="Familles scientifiques">
          {FAMILY_LEGEND.map(([family, label]) => (
            <div key={family} className="flex items-center gap-2 text-[10px] font-bold" style={{ color: props.P.textMuted }}>
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: CEPHALO_SCIENTIFIC_COLORS[family] }} />
              <span>{label}</span>
            </div>
          ))}
        </div>

        <div className="xl:mt-3 xl:border-t xl:pt-3" style={{ borderColor: props.P.border }}>
          <p className="mb-2 hidden text-[9px] font-black uppercase tracking-[0.16em] xl:block" style={{ color: props.P.textDim }}>Affichage</p>
          <div className="flex min-w-0 gap-2 overflow-x-auto pb-0.5 xl:grid xl:grid-cols-1 xl:overflow-visible xl:pb-0">
            <button
              type="button"
              aria-pressed={magnifierEnabled}
              onClick={() => setMagnifierEnabled(!magnifierEnabled)}
              className={toggleClass(magnifierEnabled)}
              style={toggleStyle(magnifierEnabled)}
            >
              Loupe
            </button>
            <button
              type="button"
              aria-pressed={vtoSettings.showSoftTissue}
              onClick={() => setVtoSettings(value => ({ ...value, showSoftTissue: !value.showSoftTissue }))}
              className={toggleClass(vtoSettings.showSoftTissue)}
              style={toggleStyle(vtoSettings.showSoftTissue)}
            >
              Tissus mous
            </button>
            <button
              type="button"
              aria-pressed={vtoSettings.showGhostFace}
              onClick={() => setVtoSettings(value => ({ ...value, showGhostFace: !value.showGhostFace }))}
              className={toggleClass(vtoSettings.showGhostFace)}
              style={toggleStyle(vtoSettings.showGhostFace)}
            >
              Face 3D
            </button>
            <button
              type="button"
              aria-pressed={activeMorphing === 'T1'}
              onClick={() => setActiveMorphing(activeMorphing === 'T1' ? 'none' : 'T1')}
              className={toggleClass(activeMorphing === 'T1')}
              style={toggleStyle(activeMorphing === 'T1')}
              aria-label="Projection T1"
            >
              <span className="sm:hidden">T1</span><span className="hidden sm:inline">Projection T1</span>
            </button>
            <button
              type="button"
              aria-pressed={activeMorphing === 'T2'}
              onClick={() => setActiveMorphing(activeMorphing === 'T2' ? 'none' : 'T2')}
              className={toggleClass(activeMorphing === 'T2')}
              style={toggleStyle(activeMorphing === 'T2')}
              aria-label="Projection T2"
            >
              <span className="sm:hidden">T2</span><span className="hidden sm:inline">Projection T2</span>
            </button>
          </div>
        </div>
      </aside>

      <div
        data-r20-radiograph-stage
        className="min-w-0"
        style={{ '--cephalo-scientific-anchor': '#f8fafc' } as React.CSSProperties}
      >
        <Step1CephaloBase {...props} />
      </div>

      <div data-r20-measures-panel className="min-w-0 h-[68vh] xl:h-[80vh]">
        <CephaloAnalysisWorkbenchPanel P={props.P} analysis={analysis} />
      </div>
    </div>
  );
};
