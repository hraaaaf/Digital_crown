import type { ReactNode } from 'react';

/**
 * G1 theme-only proof: a presentational, inactive frame for a future authorized ViewSlot.
 *
 * No routing, clinical state, patient selection, permission grant or persistence lives here.
 * This frame inherits the cabinet's existing semantic theme tokens through index.css.
 * The caller must enforce authorization, patient isolation and draft safety BEFORE
 * mounting clinical content. Do not mount this proof into Cabinet navigation.
 */
export interface ViewSlotThemeFrameProps {
  title: string;
  description?: string;
  children: ReactNode;
  onExchange?: () => void;
  onEnlarge?: () => void;
  fillHeight?: boolean;
}

export function ViewSlotThemeFrame({
  title,
  description,
  children,
  onExchange,
  onEnlarge,
  fillHeight = false,
}: ViewSlotThemeFrameProps) {
  return (
    <section
      data-v15-07-theme-slot
      aria-label={title}
      className={`flex min-h-0 min-w-0 flex-col overflow-hidden rounded-elite-sm border border-border-main bg-card text-text-main ${fillHeight ? 'h-full' : ''}`}
    >
      <header className="flex min-w-0 flex-wrap items-center justify-between gap-2 border-b border-border-main bg-card p-3">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-bold text-text-main">{title}</h2>
          {description ? (
            <p className="truncate text-xs text-text-muted">{description}</p>
          ) : null}
        </div>
        {(onExchange || onEnlarge) && (
          <div className="flex flex-wrap gap-2">
            {onExchange && (
              <button
                type="button"
                className="rounded-elite-sm border border-border-main bg-input-field px-3 py-2 text-xs font-semibold text-text-main hover:bg-medical-pearl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={onExchange}
              >
                Échanger les vues
              </button>
            )}
            {onEnlarge && (
              <button
                type="button"
                className="rounded-elite-sm bg-primary px-3 py-2 text-xs font-semibold text-on-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={onEnlarge}
              >
                Agrandir cette vue
              </button>
            )}
          </div>
        )}
      </header>
      <div data-v15-07-theme-slot-content className="min-h-0 min-w-0 flex-1 overflow-auto bg-card p-3 text-text-main">
        {children}
      </div>
    </section>
  );
}
