import { useState, type ReactNode } from 'react';
import { Maximize2, RotateCcw } from 'lucide-react';
import { authorizeLayout, type Layout, type Slot, type WorkspaceContext } from './studioLayouts';
import { StudioLayoutFrame } from './StudioLayoutFrame';

/**
 * LOT07 R3-2 — isolated DEV-only, three REAL read-only clinical modules.
 * Focus replaces the entire three-pane subtree rather than hiding two live
 * patient viewers; never keep stale media, duplicated editors or hidden mounts.
 * Backend RBAC and session/workstation/tenant guards remain authoritative.
 */
export function R3ThreePaneWorkspace({layout, context, renderSlot}: {
  layout: Layout;
  context: WorkspaceContext;
  renderSlot: (slot: Slot) => ReactNode;
}) {
  const [focusId, setFocusId] = useState<string | null>(null);
  const supported = layout.geometry === 'three-columns' || layout.geometry === 'hero-two';
  const originalGate = supported ? authorizeLayout(layout,context) : {ok:false} as const;
  const focusedSlot = layout.slots.find(slot => slot.id === focusId);
  const focusLayout: Layout | null = focusedSlot
    ? {id:'r3-focus-' + focusedSlot.id,label:layout.label + ' · ' + focusedSlot.module,
      geometry:'single',slots:[focusedSlot]} : null;
  const focusPermitted = focusLayout && authorizeLayout(focusLayout,context).ok;
  if (!originalGate.ok || (focusLayout && !focusPermitted)) {
    return <p role="alert" data-testid="r3-2-denied">
      Trois vues indisponibles : vérification clinique, poste ou lisibilité refusée.
    </p>;
  }
  return <section data-r3-2-focus-workspace className="min-w-0 rounded-xl border border-border-main bg-medical-pearl p-2.5 text-text-main sm:p-3"
      aria-label="R3-2 — trois panneaux et focus temporaire">
    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-sm font-semibold">{focusedSlot ? 'Focus' : '3 vues'}</h2>
      {focusedSlot
        ? <button type="button" data-testid="r3-2-restore" onClick={()=>setFocusId(null)}
            aria-label="Restaurer les trois panneaux" title="Restaurer les trois panneaux"
            className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-border-main bg-card px-3 py-2 text-xs font-semibold text-text-main focus-visible:outline-2 focus-visible:outline-primary">
            <RotateCcw size={15} aria-hidden="true" /> 3 vues
          </button>
        : <div role="group" aria-label="Agrandir un panneau" className="flex flex-wrap gap-1.5">
            {layout.slots.map((slot,index)=><button key={slot.id} type="button"
              onClick={()=>setFocusId(slot.id)}
              aria-label={'Agrandir le panneau ' + (index+1) + ' : ' + slot.module}
              title={'Agrandir : ' + slot.module}
              className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-border-main bg-card px-2.5 py-2 text-xs font-medium text-text-main hover:bg-medical-pearl focus-visible:outline-2 focus-visible:outline-primary">
              <Maximize2 size={14} aria-hidden="true" />
              {slot.module==='dossier'?'Dossier':slot.module==='imagerie'?'Médias':'Suivi'}
            </button>)}
          </div>}
    </div>
    <div data-testid={focusedSlot ? 'r3-2-single-focus' : 'r3-2-three-real-panes'}
      className="min-w-0 [&_[data-v15-071-viewslot]]:overscroll-contain [&_[data-v15-071-multiview-scaffold]>h2]:hidden">
      <StudioLayoutFrame
        layout={focusLayout ?? layout}
        context={context}
        renderSlot={renderSlot}/>
    </div>
  </section>;
}
