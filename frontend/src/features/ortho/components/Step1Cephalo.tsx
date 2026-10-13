import React from 'react';
import { Ruler, DraftingCompass, ZoomIn, SlidersHorizontal, ScanFace, Wand2, Layers3 } from 'lucide-react';
import { Step1Cephalo as Step1CephaloBase } from './Step1CephaloBase';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CEPHALO_ANALYSIS_CHANGE_EVENT,
  publishCephaloAnalysis,
  type CephaloAnalysisMode,
} from '../cephaloAnalysisBridge';
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
  const imgFilters = useOrthoStore(state => state.imgFilters);
  const setImgFilters = useOrthoStore(state => state.setImgFilters);
  const setActiveMorphing = useOrthoStore(state => state.setActiveMorphing);
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
      onKeyDownCapture={(event) => {
        const target = event.target as HTMLElement;
        if (target.closest('input, textarea, select, [contenteditable="true"], [role="textbox"]')) return;
        if (event.altKey || !(event.ctrlKey || event.metaKey)) return;
        const key = event.key.toLowerCase();
        if (key === 'z' && event.shiftKey && landmarkEditTimeline.redoStack.length > 0) {
          event.preventDefault();
          redoLandmarkEdit();
        } else if (key === 'z' && !event.shiftKey && landmarkEditTimeline.undoStack.length > 0) {
          event.preventDefault();
          undoLandmarkEdit();
        } else if (key === 'y' && !event.shiftKey && landmarkEditTimeline.redoStack.length > 0) {
          event.preventDefault();
          redoLandmarkEdit();
        }
      }}
      data-r19-reference-layout
      data-r20-workbench-layout
      className="grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-[220px_minmax(0,1fr)_minmax(350px,0.76fr)] xl:items-stretch"
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

        <section aria-label="Analyses céphalométriques prêtes à l’emploi" className="mt-3 rounded-xl border p-2" style={{ borderColor: props.P.border, background: props.P.bgInput }}>
          <label htmlFor="cephalo-ready-analysis" className="mb-2 block text-xs font-bold" style={{ color: props.P.text }}>
            Analyse clé en main
          </label>
          <select
            id="cephalo-ready-analysis"
            value={analysis}
            onChange={(event) => publishCephaloAnalysis(event.target.value as CephaloAnalysisMode)}
            className="min-h-11 w-full rounded-lg border px-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2"
            style={{ borderColor: props.P.borderFocus, background: props.P.bgCard, color: props.P.text }}
          >
            {(Object.keys(ANALYSIS_LABELS) as CephaloAnalysisMode[]).map((mode) => (
              <option key={mode} value={mode}>{ANALYSIS_LABELS[mode]}</option>
            ))}
          </select>
          <p className="mt-2 text-[11px] leading-relaxed" style={{ color: props.P.textMuted }}>
            Choisis une méthode. Les mesures manquantes sont signalées sans estimation.
          </p>
        </section>

        <section className="mt-3 rounded-xl border p-2" aria-label="Outils de mesure clinique" style={{ borderColor: props.P.border, background: props.P.bgCard }}>
          <h4 className="mb-2 text-xs font-bold" style={{ color: props.P.text }}>Outils cliniques</h4>
          <div className="grid grid-cols-2 gap-2">
            {([
              { label: 'Distance', Icon: Ruler },
              { label: 'Angle', Icon: DraftingCompass },
            ] as const).map(({ label, Icon }) => (
              <button key={label} type="button" disabled title={`${label} libre — en cours de construction`}
                aria-label={`${label} libre — en cours de construction`}
                className="flex min-h-11 items-center justify-center gap-2 rounded-lg border px-2 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-60"
                style={{ borderColor: props.P.border, color: props.P.textMuted, background: props.P.bgInput }}>
                <Icon size={16} aria-hidden="true" />{label}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs" style={{ color: props.P.textMuted }}>
            Mesures libres en cours de construction. Les analyses calculées restent disponibles à droite.
          </p>
          <div className="mt-2 flex flex-wrap gap-2" aria-label="Accès rapide aux commandes existantes">
            <button type="button" aria-pressed={magnifierEnabled}
              onClick={() => setMagnifierEnabled(!magnifierEnabled)}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg border px-3 text-xs font-bold"
              style={{ borderColor: magnifierEnabled ? props.P.borderFocus : props.P.border, background: magnifierEnabled ? props.P.bgInput : props.P.bgCard, color: props.P.text }}>
              <ZoomIn size={16} aria-hidden="true" />Loupe
            </button>

          </div>
        </section>

        <details className="mt-3 rounded-xl border p-2" style={{ borderColor: props.P.border, background: props.P.bgInput }}>
          <summary className="flex cursor-pointer items-center gap-2 rounded-lg px-1 py-2 text-xs font-bold focus-visible:outline-2 focus-visible:outline-offset-2" style={{ color: props.P.text }}>
            <SlidersHorizontal size={15} aria-hidden="true" /> Réglages image
          </summary>
          <div className="space-y-3 px-1 pb-2 pt-2">
            {([
              { label: 'Luminosité', value: imgFilters.brightness, min: 50, max: 200, update: (value: number) => setImgFilters(filters => ({ ...filters, brightness: value })) },
              { label: 'Contraste', value: imgFilters.contrast, min: 50, max: 300, update: (value: number) => setImgFilters(filters => ({ ...filters, contrast: value })) },
            ] as const).map(filter => (
              <label key={filter.label} className="block text-[11px]" style={{ color: props.P.textMuted }}>
                <span className="mb-1 flex justify-between gap-2"><span>{filter.label}</span><span className="font-mono">{filter.value}%</span></span>
                <input aria-label={filter.label} className="w-full" type="range" min={filter.min} max={filter.max} value={filter.value}
                  onChange={event => filter.update(Number(event.target.value))} style={{ accentColor: props.P.accent }} />
              </label>
            ))}
            <button type="button" aria-pressed={imgFilters.invert} onClick={() => setImgFilters(filters => ({ ...filters, invert: !filters.invert }))}
              className="w-full rounded-lg border px-2 py-2 text-left text-xs font-semibold"
              style={toggleStyle(imgFilters.invert)}>Inverser le contraste</button>
          </div>
        </details>

        <details className="mt-2 rounded-xl border p-2" style={{ borderColor: props.P.border, background: props.P.bgInput }}>
          <summary className="flex cursor-pointer items-center gap-2 rounded-lg px-1 py-2 text-xs font-bold focus-visible:outline-2 focus-visible:outline-offset-2" style={{ color: props.P.text }}>
            <Layers3 size={15} aria-hidden="true" /> Projections et VTO
          </summary>
          <div className="grid grid-cols-2 gap-2 px-1 pb-2 pt-2">
            <button type="button" aria-pressed={layerVisibility.t1} onClick={() => { setActiveMorphing('none'); setLayerVisible('t1', !layerVisibility.t1); }}
              className={toggleClass(layerVisibility.t1)} style={toggleStyle(layerVisibility.t1)}>T1</button>
            <button type="button" aria-pressed={layerVisibility.t2} onClick={() => { setActiveMorphing('none'); setLayerVisible('t2', !layerVisibility.t2); }}
              className={toggleClass(layerVisibility.t2)} style={toggleStyle(layerVisibility.t2)}>T2</button>
            <button type="button" aria-pressed={vtoSettings.showGhostFace} onClick={() => setVtoSettings(value => ({ ...value, showGhostFace: !value.showGhostFace }))}
              className={toggleClass(vtoSettings.showGhostFace)} style={toggleStyle(vtoSettings.showGhostFace)}>
              <span className="inline-flex items-center gap-1"><ScanFace size={14} aria-hidden="true" />Face 3D</span>
            </button>
            <button type="button" aria-pressed={vtoSettings.enabled} onClick={() => setVtoSettings(value => ({ ...value, enabled: !value.enabled }))}
              className={toggleClass(vtoSettings.enabled)} style={toggleStyle(vtoSettings.enabled)}>
              <span className="inline-flex items-center gap-1"><Wand2 size={14} aria-hidden="true" />VTO</span>
            </button>
          </div>
        </details>

        <details className="mt-2 rounded-xl border p-2" style={{ borderColor: props.P.border }}>
          <summary className="cursor-pointer rounded-lg px-1 py-2 text-xs font-bold focus-visible:outline-2" style={{ color: props.P.text }}>Historique des corrections</summary>
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
          <p className="mb-2 text-xs" style={{ color: props.P.textMuted }}>Ctrl/⌘+Z : annuler · Ctrl/⌘+Maj+Z ou Ctrl+Y : rétablir</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-1">
            <button
              type="button"
              aria-label="Annuler dernière correction"
              disabled={landmarkEditTimeline.undoStack.length === 0}
              onClick={undoLandmarkEdit}
              className="min-h-11 rounded-xl border px-2 py-2 text-xs font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              Annuler
            </button>
            <button
              type="button"
              aria-label="Rétablir correction"
              disabled={landmarkEditTimeline.redoStack.length === 0}
              onClick={redoLandmarkEdit}
              className="min-h-11 rounded-xl border px-2 py-2 text-xs font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              Rétablir
            </button>
            <button
              type="button"
              aria-label="Revenir aux repères initialement chargés" title="Revenir aux repères initialement chargés"
              disabled={
                landmarkEditTimeline.baseline.length === 0
                || landmarkSnapshotsEqual(localLandmarks, landmarkEditTimeline.baseline)
              }
              onClick={resetLandmarkEdits}
              className="min-h-11 rounded-xl border px-2 py-2 text-xs font-bold disabled:cursor-not-allowed disabled:opacity-40 xl:text-left"
              style={{ borderColor: props.P.border, background: props.P.bgInput, color: props.P.textMuted }}
            >
              Revenir au départ
            </button>
          </div>
        </section>

        </details>

        <details className="mt-2 rounded-xl border p-2" style={{ borderColor: props.P.border }}>
          <summary className="cursor-pointer rounded-lg px-1 py-2 text-xs font-bold focus-visible:outline-2" style={{ color: props.P.text }}>Gestionnaire de couches</summary>
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
        </details>
      </aside>

      <div
        data-r20-radiograph-stage
        className="min-w-0"
        style={{ '--cephalo-scientific-anchor': props.P.text } as React.CSSProperties}
      >
        <Step1CephaloBase {...props} embedded />
      </div>

      <div data-r20-measures-panel className="min-w-0 h-[68vh] xl:h-[80vh]">
        <CephaloAnalysisWorkbenchPanel P={props.P} analysis={analysis} />
      </div>
    </div>
  );
};
