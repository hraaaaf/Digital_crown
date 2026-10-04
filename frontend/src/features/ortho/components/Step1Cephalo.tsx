import React from 'react';
import { Step1Cephalo as Step1CephaloBase } from './Step1CephaloBase';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_ANALYSIS_CHANGE_EVENT,
  type CephaloAnalysisMode,
} from '../cephaloAnalysisBridge';
import { CEPHALO_SCIENTIFIC_COLORS } from '../cephaloVisualSemantics';
import { ORTHO_LAYER_REGISTRY, type OrthoLayerId } from '../orthoLayerRegistry';
import { landmarkSnapshotsEqual } from '../orthoLandmarkEditHistory';

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
  const layerVisibility = useOrthoStore(state => state.layerVisibility);
  const layerOpacity = useOrthoStore(state => state.layerOpacity);
  const setLayerVisible = useOrthoStore(state => state.setLayerVisible);
  const setLayerOpacity = useOrthoStore(state => state.setLayerOpacity);
  const resetLayers = useOrthoStore(state => state.resetLayers);
  const localLandmarks = useOrthoStore(state => state.local.landmarks);
  const landmarkEditTimeline = useOrthoStore(state => state.landmarkEditTimeline);
  const undoLandmarkEdit = useOrthoStore(state => state.undoLandmarkEdit);
  const redoLandmarkEdit = useOrthoStore(state => state.redoLandmarkEdit);
  const resetLandmarkEdits = useOrthoStore(state => state.resetLandmarkEdits);
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
      className="grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-[208px_minmax(0,1fr)_minmax(332px,0.72fr)] xl:items-stretch"
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
            <h3 className="mt-1 break-words text-sm font-black leading-tight" style={{ color: props.P.text }}>{ANALYSIS_LABELS[analysis]}</h3>
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
          <p className="mb-2 hidden text-[9px] font-black uppercase tracking-[0.16em] xl:block" style={{ color: props.P.textDim }}>Outils</p>
          <div className="flex min-w-0 gap-2 overflow-x-auto pb-1 xl:grid xl:grid-cols-1 xl:overflow-visible">
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
              aria-pressed={vtoSettings.showGhostFace}
              onClick={() => setVtoSettings(value => ({ ...value, showGhostFace: !value.showGhostFace }))}
              className={toggleClass(vtoSettings.showGhostFace)}
              style={toggleStyle(vtoSettings.showGhostFace)}
            >
              Face 3D
            </button>
          </div>
        </div>

        <section
          data-ortho-edit-history
          aria-label="Historique des corrections"
          className="mt-2 border-t pt-2 xl:mt-3 xl:pt-3"
          style={{ borderColor: props.P.border }}
        >
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-[9px] font-black uppercase tracking-[0.16em]" style={{ color: props.P.textDim }}>Corrections</p>
            <span className="text-[9px] font-bold" style={{ color: props.P.textMuted }}>
              {landmarkEditTimeline.undoStack.length} modif.
            </span>
          </div>
          <div className="grid grid-cols-3 gap-1.5 xl:grid-cols-1">
            <button
              type="button"
              aria-label="Annuler dernière correction"
              disabled={landmarkEditTimeline.undoStack.length === 0}
              onClick={undoLandmarkEdit}
              className="min-h-9 rounded-xl border px-2 py-2 text-[10px] font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              Annuler
            </button>
            <button
              type="button"
              aria-label="Rétablir correction"
              disabled={landmarkEditTimeline.redoStack.length === 0}
              onClick={redoLandmarkEdit}
              className="min-h-9 rounded-xl border px-2 py-2 text-[10px] font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              Rétablir
            </button>
            <button
              type="button"
              aria-label="Réinitialiser les corrections de session"
              disabled={
                landmarkEditTimeline.baseline.length === 0
                || landmarkSnapshotsEqual(localLandmarks, landmarkEditTimeline.baseline)
              }
              onClick={resetLandmarkEdits}
              className="min-h-9 rounded-xl border px-2 py-2 text-[10px] font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              État chargé
            </button>
          </div>
        </section>

        <section
          data-ortho-layer-manager
          aria-label="Gestionnaire de couches"
          className="mt-2 border-t pt-2 xl:mt-3 xl:pt-3"
          style={{ borderColor: props.P.border }}
        >
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-[9px] font-black uppercase tracking-[0.16em]" style={{ color: props.P.textDim }}>Couches</p>
            <button
              type="button"
              onClick={resetLayers}
              className="rounded-lg px-2 py-1 text-[9px] font-bold"
              style={{ color: props.P.textMuted }}
            >
              Réinitialiser
            </button>
          </div>
          <div className="flex min-w-0 flex-wrap gap-2 pb-1 xl:grid xl:grid-cols-1 xl:overflow-visible">
            {ORTHO_LAYER_REGISTRY.map(layer => {
              const available = layer.availability === 'available';
              const active = layerVisibility[layer.id];
              const handleToggle = () => {
                if (!available) return;
                const next = !active;
                setLayerVisible(layer.id as OrthoLayerId, next);
                if (layer.id === 'soft_tissue') {
                  setVtoSettings(value => ({ ...value, showSoftTissue: next }));
                }
              };
              return (
                <div
                  key={layer.id}
                  data-ortho-layer-control={layer.id}
                  className="min-w-[118px] rounded-xl border p-1.5 xl:min-w-0"
                  style={{ borderColor: props.P.border, background: props.P.bgInput }}
                >
                  <button
                    type="button"
                    disabled={!available}
                    aria-pressed={available ? active : undefined}
                    aria-label={available ? layer.label : `${layer.label} — en construction`}
                    title={available ? layer.label : layer.unavailableReason}
                    onClick={handleToggle}
                    className="flex min-h-8 w-full items-center justify-between gap-2 rounded-lg px-2 text-left text-[10px] font-bold disabled:cursor-not-allowed disabled:opacity-50"
                    style={{ color: active && available ? props.P.text : props.P.textMuted }}
                  >
                    <span>{layer.shortLabel}</span>
                    <span aria-hidden="true">{available ? (active ? '●' : '○') : '—'}</span>
                  </button>
                  {available && active && layer.opacityAdjustable && (
                    <input
                      aria-label={`Opacité ${layer.label}`}
                      type="range"
                      min={10}
                      max={100}
                      step={5}
                      value={Math.round(layerOpacity[layer.id] * 100)}
                      onChange={event => setLayerOpacity(layer.id as OrthoLayerId, Number(event.target.value) / 100)}
                      className="mt-1 h-1 w-full cursor-pointer"
                      style={{ accentColor: props.P.accent }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </section>
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
