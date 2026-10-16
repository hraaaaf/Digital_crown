import React from 'react';
import { Ruler, DraftingCompass, ZoomIn, SlidersHorizontal, ScanFace, Wand2, Layers3, Maximize2 } from 'lucide-react';
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


// Read-only display priority per analysis, using anatomical IDs already present
// in the two real 38-point source films. This is not an interpretation/diagnosis.
const MAJOR_LANDMARK_IDS: Record<CephaloAnalysisMode, readonly string[]> = {
  all: ['S', 'N', 'A', 'B', 'Po', 'Or', 'Go', 'Me', 'U1_incisal', 'L1_incisal'],
  steiner: ['S', 'N', 'A', 'B', 'U1_incisal', 'U1_apex', 'L1_incisal', 'L1_apex', 'Gn_anatomic', 'D_Steiner_1959'],
  tweed: ['Po', 'Po_anatomic', 'Or', 'Go', 'Me', 'L1_incisal', 'L1_apex', 'Pog_soft', 'Ls_soft', 'Li_soft'],
  mcnamara: ['N', 'A', 'B', 'Po', 'Or', 'Co', 'Gn', 'Me', 'ANS'],
  com: ['S', 'N', 'A', 'B', 'Po', 'Or', 'Go', 'Me', 'U1_incisal', 'L1_incisal'],
  ricketts: ['G_soft', 'N_soft', 'Prn', 'Cm', 'Sn_soft', 'Ls_soft', 'Li_soft', 'Pog_soft', 'Me_soft'],
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
  const setIsStep1Fullscreen = useOrthoStore(state => state.setIsStep1Fullscreen);
  // Browsing names must never arm the clinical point repositioning mode.
  const [inspectedPointId, setInspectedPointId] = React.useState<string | null>(null);
  const disarmPointPlacement = useOrthoStore(state => state.setActivePointId);
  const pointMenuRef = React.useRef<HTMLDetailsElement>(null);
  const [analysis, setAnalysis] = React.useState<CephaloAnalysisMode>('all');
  // R23-A: prioritize the image on desktop. Mobile retains its existing
  // stacked utility tools; no settings or analysis controls are removed.
  const [desktopToolsOpen, setDesktopToolsOpen] = React.useState(false);
  const [measuresOpen, setMeasuresOpen] = React.useState(true);
  const [showAllLandmarkNames, setShowAllLandmarkNames] = React.useState(false);

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
    `min-h-9 shrink-0 whitespace-nowrap rounded-xl border px-3 py-2 text-[10px] font-bold transition-all xl:min-h-10 xl:w-full xl:text-left xl:text-xs ${active ? 'shadow-sm' : ''}`;

  const toggleStyle = (active: boolean): React.CSSProperties => ({
    background: active ? props.P.bgCard : props.P.bgInput,
    borderColor: active ? props.P.borderFocus : props.P.border,
    color: active ? props.P.text : props.P.textMuted,
  });

  const desktopColumns = desktopToolsOpen
    ? (measuresOpen
      ? 'xl:grid-cols-[200px_minmax(0,1fr)_350px] 2xl:grid-cols-[208px_minmax(0,1fr)_380px]'
      : 'xl:grid-cols-[200px_minmax(0,1fr)] 2xl:grid-cols-[208px_minmax(0,1fr)]')
    : (measuresOpen
      ? 'xl:grid-cols-[minmax(0,1fr)_350px] 2xl:grid-cols-[minmax(0,1fr)_380px]'
      : 'xl:grid-cols-[minmax(0,1fr)]');

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
      className={`grid min-w-0 grid-cols-1 gap-3 xl:items-stretch ${desktopColumns}`}
      data-r23-image-first={desktopToolsOpen ? 'tools-open' : 'tools-collapsed'}
    >
      <div data-r23-studio-toolbar className="relative z-50 flex min-w-0 flex-wrap items-center gap-1.5 rounded-2xl border px-2 py-1.5 sm:gap-2 sm:px-3 sm:py-2 xl:col-span-full"
        style={{ background: props.P.bgPanel, borderColor: props.P.border }}>
        <label htmlFor="cephalo-ready-analysis" className="sr-only shrink-0 text-xs font-bold xl:not-sr-only" style={{ color: props.P.text }}>Analyse clé en main</label>
        <select
          id="cephalo-ready-analysis"
          value={analysis}
          onChange={(event) => publishCephaloAnalysis(event.target.value as CephaloAnalysisMode)}
          className="min-h-10 min-w-[142px] flex-1 rounded-xl border px-2 text-[13px] font-semibold sm:min-w-0 sm:max-w-[215px] focus-visible:outline-2 focus-visible:outline-offset-2"
          style={{ borderColor: props.P.borderFocus, background: props.P.bgCard, color: props.P.text }}
        >
          {(Object.keys(ANALYSIS_LABELS) as CephaloAnalysisMode[]).map((mode) => (
            <option key={mode} value={mode}>{ANALYSIS_LABELS[mode]}</option>
          ))}
        </select>
        <button type="button" data-r23-tools-toggle aria-expanded={desktopToolsOpen}
          aria-controls="cephalo-r23-utility-rail"
          onClick={() => setDesktopToolsOpen(value => !value)}
          className="inline-flex min-h-10 items-center justify-center rounded-xl border px-2 text-xs font-bold sm:px-3"
          style={{ background: props.P.bgCard, borderColor: props.P.border, color: props.P.text }}
         aria-label={desktopToolsOpen ? 'Masquer les outils' : 'Afficher les outils'}>
          <SlidersHorizontal size={16} aria-hidden="true" />
          <span className="hidden xl:inline xl:ml-1">{desktopToolsOpen ? 'Masquer les outils' : 'Afficher les outils'}</span>
        </button>
        <button type="button" data-r23-measures-toggle aria-expanded={measuresOpen}
          aria-controls="cephalo-r23-measure-rail"
          onClick={() => setMeasuresOpen(value => !value)}
          className="inline-flex min-h-10 items-center justify-center rounded-xl border px-2 text-xs font-bold sm:px-3"
          style={{ background: props.P.bgCard, borderColor: props.P.border, color: props.P.text }}
         aria-label={measuresOpen ? 'Masquer les mesures' : 'Afficher les mesures'}>
          <ScanFace size={16} aria-hidden="true" />
          <span className="hidden xl:inline xl:ml-1">{measuresOpen ? 'Masquer les mesures' : 'Afficher les mesures'}</span>
        </button>
        <button type="button" data-cephalo-all-names-toggle
          aria-pressed={showAllLandmarkNames}
          aria-label={showAllLandmarkNames ? 'Revenir aux noms majeurs des repères' : 'Afficher tous les noms des repères'}
          title={showAllLandmarkNames ? 'Afficher uniquement les noms majeurs ; autres au survol' : 'Afficher les 38 noms anatomiques'}
          onClick={() => setShowAllLandmarkNames(value => !value)}
          className="hidden min-h-10 items-center justify-center rounded-xl border px-3 text-xs font-bold focus-visible:outline-2 focus-visible:outline-offset-2 xl:inline-flex"
          style={{ background: showAllLandmarkNames ? props.P.bgInput : props.P.bgCard,
            borderColor: showAllLandmarkNames ? props.P.borderFocus : props.P.border, color: props.P.text }}>
          {showAllLandmarkNames ? 'Noms essentiels' : 'Tous les noms'}
        </button>
        <details ref={pointMenuRef} data-r23-mobile-point-directory data-cephalo-desktop-landmark-inspector className="relative">
          <summary aria-label="Parcourir les repères anatomiques" className="flex min-h-10 cursor-pointer list-none items-center justify-center rounded-xl border px-2 text-[11px] font-bold focus-visible:outline-2 focus-visible:outline-offset-2"
            style={{ background: props.P.bgCard, borderColor: props.P.border, color: props.P.text }}>
            Repères <span className="ml-1 tabular-nums">{localLandmarks.length}</span>
          </summary>
          <div className="absolute right-0 top-full z-[70] mt-2 w-[min(86vw,320px)] rounded-xl border p-2 shadow-xl"
            style={{ background: props.P.bgPanel, borderColor: props.P.border }}>
            <p className="px-1 pb-2 text-xs leading-snug" style={{ color: props.P.textMuted }}>Sélectionnez un nom pour l'identifier sur la radiographie. Tous les points restent présents.</p>
            <div role="group" aria-label="Liste des repères anatomiques" className="grid max-h-[40vh] grid-cols-3 gap-1 overflow-y-auto overscroll-contain">
              {[...localLandmarks].sort((a,b)=>a.id.localeCompare(b.id)).map(point => (
                <button key={point.id} type="button" data-r23-point-select={point.id}
                  aria-label={`Inspecter le repère ${point.id}`} aria-pressed={inspectedPointId===point.id}
                  onClick={() => {
                    disarmPointPlacement(null);
                    setInspectedPointId(point.id);
                    pointMenuRef.current?.removeAttribute('open');
                  }}
                  className="min-h-10 break-all rounded-lg border px-1 py-1 text-xs font-bold focus-visible:outline-2 focus-visible:outline-offset-2"
                  style={{ background: inspectedPointId===point.id ? props.P.bgInput : props.P.bgCard, borderColor: inspectedPointId===point.id ? props.P.borderFocus : props.P.border, color: props.P.text }}>
                  {point.id}
                </button>
              ))}
            </div>
          </div>
        </details>
        <button type="button" data-cephalo-focus-entry="desktop"
          aria-label="Activer le mode Focus radiographie"
          title="Examiner la radiographie sans panneaux ; Échap pour revenir"
          onClick={() => setIsStep1Fullscreen(true)}
          className="hidden min-h-10 items-center gap-2 rounded-xl border px-3 text-xs font-bold xl:inline-flex"
          style={{ background: props.P.bgCard, borderColor: props.P.borderFocus, color: props.P.text }}
        ><Maximize2 size={15} aria-hidden="true" />Focus</button>
      </div>
      <aside
        data-r20-workbench-sidebar
        id="cephalo-r23-utility-rail"
        aria-label="Contrôles du workbench céphalométrique"
        className={`min-w-0 rounded-2xl border p-2 xl:h-[82vh] xl:overflow-y-auto xl:p-2.5 ${desktopToolsOpen ? '' : 'hidden'}`}
        style={{ background: props.P.bgPanel, borderColor: props.P.border, boxShadow: props.P.shadow }}
      >
        <div className="hidden xl:block">
          <div className="min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-[0.07em]" style={{ color: props.P.textMuted }}>Workbench</p>
            <h3 className="mt-1 break-words text-sm font-black leading-tight" style={{ color: props.P.text }}>{ANALYSIS_LABELS[analysis]}</h3>
          </div>
          <span className="mt-2 inline-flex rounded-full border px-2 py-1 text-[11px] font-semibold uppercase tracking-wide" style={{ borderColor: props.P.border, color: props.P.textMuted }}>
            Analyse active
          </span>
        </div>

        <section aria-label="Analyses céphalométriques prêtes à l’emploi" className="mt-3 rounded-xl border p-2" style={{ borderColor: props.P.border, background: props.P.bgInput }}>
          <p className="text-xs font-bold" style={{ color: props.P.text }}>Analyse : {ANALYSIS_LABELS[analysis]}</p>
          <p className="mt-2 text-xs leading-snug" style={{ color: props.P.textMuted }}>
            {analysis === 'all'
              ? 'Tous les repères affichés. Choisissez une analyse pour isoler ses tracés.'
              : 'Analyse ciblée : les calculs et les repères source restent inchangés.'}
            {' '}Données manquantes non estimées.
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
            Distance et angle libres : en cours de construction.
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
              <label key={filter.label} className="block text-xs" style={{ color: props.P.textMuted }}>
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
            <button type="button" aria-label="Projection T1" aria-pressed={layerVisibility.t1} onClick={() => { setActiveMorphing('none'); setLayerVisible('t1', !layerVisibility.t1); }}
              className={toggleClass(layerVisibility.t1)} style={toggleStyle(layerVisibility.t1)}>T1</button>
            <button type="button" aria-label="Projection T2" aria-pressed={layerVisibility.t2} onClick={() => { setActiveMorphing('none'); setLayerVisible('t2', !layerVisibility.t2); }}
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

        <p className="mt-2 text-xs leading-snug" style={{ color: props.P.textMuted }}>VTO : aperçu expérimental, sans valeur prédictive clinique validée.</p>

        <details className="mt-2 rounded-xl border p-2" style={{ borderColor: props.P.border }}>
          <summary className="cursor-pointer rounded-lg px-1 py-2 text-xs font-bold focus-visible:outline-2" style={{ color: props.P.text }}>Historique des corrections</summary>
        <section
          data-ortho-edit-history
          aria-label="Historique des corrections"
          className="mt-2 border-t pt-2 xl:mt-3 xl:pt-3"
          style={{ borderColor: props.P.border }}
        >
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-[10px] font-bold uppercase tracking-[0.10em]" style={{ color: props.P.textDim }}>Corrections</p>
            <span className="text-[10px] font-semibold" style={{ color: props.P.textMuted }}>
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
            <p className="text-[10px] font-bold uppercase tracking-[0.10em]" style={{ color: props.P.textDim }}>Couches</p>
            <button
              type="button"
              onClick={resetLayers}
              className="rounded-lg px-2 py-1 text-[10px] font-semibold"
              style={{ color: props.P.textMuted }}
            >
              Réinitialiser
            </button>
          </div>
          <div className="flex min-w-0 flex-wrap gap-2 pb-1 xl:grid xl:grid-cols-1 xl:overflow-visible">
            {ORTHO_LAYER_REGISTRY.filter(layer => layer.id !== 't1' && layer.id !== 't2').map(layer => {
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
                    className="flex min-h-10 w-full items-center justify-between gap-2 rounded-lg px-2 text-left text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                    style={{ color: active && available ? props.P.text : props.P.textMuted }}
                  >
                    <span>{layer.shortLabel}</span>
                    <span aria-hidden="true">{available ? (active ? '●' : '○') : '—'}</span>
                  </button>
                  {available && active && layer.opacityAdjustable && (
                    <div className="px-2 pb-1">
                      <div className="flex items-center justify-between gap-2 text-[10px]" style={{ color: props.P.textMuted }}>
                        <label htmlFor={`ortho-layer-opacity-${layer.id}`}>Opacité</label>
                        <output
                          htmlFor={`ortho-layer-opacity-${layer.id}`}
                          data-ortho-layer-opacity-value={layer.id}
                          className="font-mono font-bold tabular-nums"
                          style={{ color: props.P.text }}
                        >
                          {Math.round(layerOpacity[layer.id] * 100)} %
                        </output>
                      </div>
                      <input
                        id={`ortho-layer-opacity-${layer.id}`}
                        aria-label={`Opacité ${layer.label}`}
                        aria-valuetext={`${Math.round(layerOpacity[layer.id] * 100)} pour cent`}
                        type="range"
                        min={10}
                        max={100}
                        step={5}
                        value={Math.round(layerOpacity[layer.id] * 100)}
                        onChange={event => setLayerOpacity(layer.id as OrthoLayerId, Number(event.target.value) / 100)}
                        className="mt-2 h-1.5 w-full cursor-pointer"
                        style={{ accentColor: props.P.accent }}
                      />
                    </div>
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
        <Step1CephaloBase {...props} embedded activeAnalysis={analysis} inspectedPointId={inspectedPointId}
          prominentPointIds={showAllLandmarkNames ? undefined : MAJOR_LANDMARK_IDS[analysis]} />
      </div>

      <div data-r20-measures-panel id="cephalo-r23-measure-rail" className={`min-w-0 h-[68vh] xl:h-[82vh] ${measuresOpen ? '' : 'hidden'}`}>
        <CephaloAnalysisWorkbenchPanel P={props.P} analysis={analysis} />
      </div>
    </div>
  );
};
