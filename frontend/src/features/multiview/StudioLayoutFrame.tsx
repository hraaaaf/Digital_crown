import type { ReactNode } from 'react';
import { authorizeLayout, type Layout, type Slot, type WorkspaceContext } from './studioLayouts';
import { geometryGridStyle, geometrySlotStyle } from './studioGeometry';

/**
 * Dormant composition primitive, NOT imported by Cabinet routes.
 * A future trusted adapter must supply patient-scoped and server-authorized
 * real modules, cancel stale async work on patient switch, and isolate stores.
 * Denied layouts never invoke renderSlot and never mount clinical content.
 */
export function StudioLayoutFrame({
  layout, context, renderSlot, primaryRatio = 50,
}: {
  layout: Layout;
  context: WorkspaceContext;
  renderSlot: (slot: Slot) => ReactNode;
  primaryRatio?: number;
}) {
  const decision = authorizeLayout(layout, context);
  if (!decision.ok) {
    return (
      <p role="alert" data-testid="multiview-denied">
        Vues multiples indisponibles : le contexte, les droits ou la lisibilité ne sont pas vérifiés.
      </p>
    );
  }

  return (
    <section aria-label={'Vues multiples — ' + decision.layout.label}
      data-v15-071-multiview-scaffold
      className="min-w-0 rounded-xl border border-border-main bg-card-bg p-3 text-text-main">
      <h2 className="mb-3 text-sm font-semibold">{decision.layout.label}</h2>
      <div data-v15-071-multiview-grid
        style={geometryGridStyle(decision.layout.geometry, primaryRatio)}
        className="min-w-0">
        {decision.layout.slots.map((slot, index) => (
          <section key={slot.id} aria-label={'Panneau ' + (index + 1)}
            data-v15-071-viewslot={slot.module}
            style={geometrySlotStyle(decision.layout.geometry, index)}
            className="min-w-0 overflow-auto rounded-lg border border-border-main bg-card">
            {renderSlot(slot)}
          </section>
        ))}
      </div>
    </section>
  );
}
