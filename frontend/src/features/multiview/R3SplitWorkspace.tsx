import { useId, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react';
import { authorizeLayout, type Layout, type Slot, type WorkspaceContext } from './studioLayouts';

/**
 * LOT07 R3-1: opt-in two-pane splitter, isolated from the certified R2 frame.
 * Clinical modules are rendered only after the existing exact-context R-only gate.
 * This component is presentation, NEVER a substitute for server RBAC or patient-fetch guards.
 */
export type SplitSizing = 'strict' | 'content-fit';
const MIN_RATIO = 37;
const MAX_RATIO = 63;
const GUTTER_PX = 12;

export function clampSplitRatio(value: number): number {
  return Number.isFinite(value) ? Math.max(MIN_RATIO, Math.min(MAX_RATIO, Math.round(value))) : 50;
}

export function splitTracks(geometry: Layout['geometry'], ratio: number, mode: SplitSizing): string {
  const r = clampSplitRatio(ratio);
  if (geometry === 'two-columns') return 'minmax(0,' + r + 'fr) ' + GUTTER_PX + 'px minmax(0,' + (100-r) + 'fr)';
  if (geometry === 'two-rows' && mode === 'content-fit') return 'max-content ' + GUTTER_PX + 'px minmax(360px,auto)';
  if (geometry === 'two-rows') return 'minmax(0,' + r + 'fr) ' + GUTTER_PX + 'px minmax(0,' + (100-r) + 'fr)';
  throw new Error('R3-1 only supports two-pane geometries');
}

export function R3SplitWorkspace({ layout, context, renderSlot, initialRatio = 50 }: {
  layout: Layout;
  context: WorkspaceContext;
  renderSlot: (slot: Slot) => ReactNode;
  initialRatio?: number;
}) {
  const isColumns = layout.geometry === 'two-columns';
  const isRows = layout.geometry === 'two-rows';
  const [ratio, setRatio] = useState(() => clampSplitRatio(initialRatio));
  const [mode, setMode] = useState<SplitSizing>('strict');
  const gridRef = useRef<HTMLDivElement>(null);
  const pointerId = useRef<number | null>(null);
  const uid = useId();
  const panelA = uid + '-pane-a';
  const panelB = uid + '-pane-b';
  // Critically, a denied context must never invoke renderSlot or mount cached patient data.
  const permitted = (isColumns || isRows) && authorizeLayout(layout, context, ratio).ok;

  const updateRatio = (value: number) => {
    const next = clampSplitRatio(value);
    if ((isColumns || isRows) && authorizeLayout(layout, context, next).ok) setRatio(next);
  };

  const onSeparatorKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!permitted || mode !== 'strict') return;
    let next: number | null = null;
    if (event.key === 'Home') next = MIN_RATIO;
    if (event.key === 'End') next = MAX_RATIO;
    if ((isColumns && event.key === 'ArrowLeft') || (isRows && event.key === 'ArrowUp')) next = ratio - 5;
    if ((isColumns && event.key === 'ArrowRight') || (isRows && event.key === 'ArrowDown')) next = ratio + 5;
    if (next !== null) {
      event.preventDefault();
      updateRatio(next);
    }
  };

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (!permitted || mode !== 'strict' || event.button !== 0) return;
    pointerId.current = event.pointerId;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  };
  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (pointerId.current !== event.pointerId || !permitted || mode !== 'strict') return;
    const bounds = gridRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const length = isColumns ? bounds.width : bounds.height;
    if (!Number.isFinite(length) || length <= GUTTER_PX) return;
    const offset = (isColumns ? event.clientX - bounds.left : event.clientY - bounds.top) - GUTTER_PX / 2;
    updateRatio(offset / (length - GUTTER_PX) * 100);
  };
  const finishPointer = () => { pointerId.current = null; };
  if (!permitted) {
    return <p role="alert" data-testid="r3-1-split-denied">
      Vues partagées indisponibles : session, droits, modules ou lisibilité non vérifiés.
    </p>;
  }

  const strict = mode === 'strict';
  const gridStyle: CSSProperties = {
    display: 'grid', width: '100%', minWidth: 0, gap: 0,
    gridTemplateColumns: isColumns ? splitTracks(layout.geometry, ratio, mode) : 'minmax(0,1fr)',
    gridTemplateRows: isRows ? splitTracks(layout.geometry, ratio, mode) : undefined,
    // Two-row previews should show BOTH independent read-only panes inside 1080p.
    // Content-fit never allocates the entire height to an unbounded dossier.
    height: strict ? (isRows ? 'min(54vh,560px)' : 'min(70vh,760px)') : 'auto',
    minHeight: strict ? (isRows ? 460 : 520) : 0,
  };
  const paneClass = 'min-w-0 min-h-0 overflow-auto overscroll-contain rounded-lg border border-border-main bg-card';
  return <section aria-label={'R3-1 — ' + layout.label}
    data-r3-1-split={layout.geometry} data-r3-1-mode={mode}
    className="relative isolate min-w-0 rounded-xl border border-border-main bg-medical-pearl p-2.5 text-text-main sm:p-3">
    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-sm font-semibold">{layout.label} · R3-1</h2>
      <div className="flex items-center gap-2">
        {isRows && <button type="button" onClick={() => { finishPointer(); setMode(strict ? 'content-fit' : 'strict'); }}
          aria-pressed={!strict} className="rounded-md border border-border-main bg-card px-3 py-2 text-xs text-text-main focus-visible:outline-2 focus-visible:outline-primary">
          {strict ? 'Ajuster au contenu' : 'Revenir au partage strict'}
        </button>}
        <button type="button" onClick={() => { finishPointer(); setMode('strict'); updateRatio(50); }}
          className="rounded-md border border-border-main bg-card px-3 py-2 text-xs text-text-main focus-visible:outline-2 focus-visible:outline-primary">
          Égaliser 50/50
        </button>
      </div>
    </div>
    <div ref={gridRef} data-testid="r3-1-grid" style={gridStyle}>
      <section id={panelA} aria-label="Panneau 1" data-v15-071-viewslot={layout.slots[0].module}
        style={isRows && !strict ? {maxHeight:'min(32vh,340px)'} : undefined}
        className={paneClass}>{renderSlot(layout.slots[0])}</section>
      {strict
        ? <div role="separator" tabIndex={0}
            aria-label={isColumns ? 'Séparateur vertical des panneaux' : 'Séparateur horizontal des panneaux'}
            aria-orientation={isColumns ? 'vertical' : 'horizontal'}
            aria-valuemin={MIN_RATIO} aria-valuemax={MAX_RATIO} aria-valuenow={ratio}
            aria-valuetext={ratio + ' % pour le premier panneau'} aria-controls={panelA + ' ' + panelB}
            data-testid="r3-1-separator" onKeyDown={onSeparatorKey}
            onPointerDown={onPointerDown} onPointerMove={onPointerMove}
            onPointerUp={finishPointer} onPointerCancel={finishPointer}
            onLostPointerCapture={finishPointer}
            style={{touchAction:'none',cursor:isColumns?'col-resize':'row-resize'}}
            className="group relative flex items-center justify-center rounded-sm bg-border-main/70 transition-colors hover:bg-primary/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            <span aria-hidden="true" className={
              'pointer-events-none flex items-center justify-center rounded-full border border-border-hover bg-card shadow-sm transition-colors group-hover:border-primary group-focus-visible:border-primary ' +
              (isColumns ? 'h-14 w-2.5' : 'h-2.5 w-14')
            }>
              <span className={'rounded-full bg-primary/70 ' + (isColumns ? 'h-7 w-1' : 'h-1 w-7')} />
            </span>
          </div>
        : <div aria-hidden="true" className="bg-border-main" />}
      <section id={panelB} aria-label="Panneau 2" data-v15-071-viewslot={layout.slots[1].module}
        style={isRows && !strict ? {minHeight:220} : undefined}
        className={paneClass}>{renderSlot(layout.slots[1])}</section>
    </div>
    <p className="mt-2 text-xs text-text-muted">
      {strict ? 'Partage ajustable : flèches, Début/Fin ou glisser le séparateur.' : 'Hauteur du premier panneau adaptée à son contenu.'}
      {' '}Lecture seule · sans enregistrement.
    </p>
  </section>;
}
