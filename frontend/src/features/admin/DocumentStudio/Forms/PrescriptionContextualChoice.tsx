import React from 'react';
import { Check, ChevronDown, Pencil } from 'lucide-react';
import { cn } from '../../../../utils/cn';

export type ContextualChoiceOption = {
  value: string;
  label: string;
  secondary?: string;
};

export function PrescriptionContextualChoice({
  ariaLabel,
  value,
  placeholder,
  options,
  onSelect,
  onManual,
  icon,
  disabled = false,
}: {
  ariaLabel: string;
  value: string;
  placeholder: string;
  options: ContextualChoiceOption[];
  onSelect: (value: string) => void;
  onManual: (value: string) => void;
  icon?: React.ReactNode;
  disabled?: boolean;
}) {
  const [open, setOpen] = React.useState(false);
  const [manual, setManual] = React.useState(false);
  const [draft, setDraft] = React.useState(value);
  const rootRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) {
      setManual(false);
      setDraft(value);
    }
  }, [open, value]);

  React.useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [open]);

  const submitManual = () => {
    const next = draft.trim();
    if (!next) return;
    onManual(next);
    setOpen(false);
  };

  return (
    <div ref={rootRef} className="relative min-w-0">
      <button
        type="button"
        aria-label={ariaLabel}
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen(current => !current)}
        className={cn(
          'inline-flex min-h-11 w-full min-w-0 items-center gap-2 rounded-xl border border-border-main bg-input-field/80 px-3 py-2 text-left transition-all',
          'hover:border-primary/30 hover:bg-card focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/20',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      >
        {icon}
        <span className="min-w-0 flex-1 truncate text-[10px] font-black text-text-main">
          {value || placeholder}
        </span>
        <ChevronDown size={13} className="shrink-0 text-text-muted" />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute left-0 top-full z-[130] mt-1.5 min-w-[13rem] overflow-hidden rounded-xl border border-border-main bg-card py-1.5 shadow-2xl"
        >
          {!manual ? (
            <>
              {options.length ? options.map(option => (
                <button
                  key={`${option.value}-${option.label}`}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    onSelect(option.value);
                    setOpen(false);
                  }}
                  className="flex min-h-10 w-full items-center gap-2 px-3 py-2 text-left hover:bg-primary/5"
                >
                  <span className="flex h-4 w-4 shrink-0 items-center justify-center text-primary">
                    {option.value === value ? <Check size={13} /> : null}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[10px] font-black text-text-main">{option.label}</span>
                    {option.secondary && (
                      <span className="block truncate text-[8px] font-semibold text-text-muted">{option.secondary}</span>
                    )}
                  </span>
                </button>
              )) : (
                <div className="px-3 py-2 text-[10px] font-semibold text-text-muted">Aucune alternative disponible.</div>
              )}

              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setDraft(value);
                  setManual(true);
                }}
                className="flex min-h-10 w-full items-center gap-2 border-t border-border-main px-3 py-2 text-left text-[10px] font-black text-primary hover:bg-primary/5"
              >
                <Pencil size={13} /> Modifier manuellement…
              </button>
            </>
          ) : (
            <div className="p-2.5">
              <label className="block text-[9px] font-black uppercase tracking-wide text-text-muted">
                Valeur personnalisée
              </label>
              <input
                autoFocus
                aria-label="Valeur personnalisée"
                value={draft}
                onChange={event => setDraft(event.target.value)}
                onKeyDown={event => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    submitManual();
                  } else if (event.key === 'Escape') {
                    setManual(false);
                  }
                }}
                className="mt-1.5 min-h-10 w-full rounded-lg border border-border-main bg-background px-2.5 text-xs font-bold text-text-main outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
              />
              <div className="mt-2 flex justify-end gap-1.5">
                <button
                  type="button"
                  onClick={() => setManual(false)}
                  className="min-h-9 rounded-lg px-2.5 text-[10px] font-bold text-text-muted hover:bg-background"
                >
                  Retour
                </button>
                <button
                  type="button"
                  onClick={submitManual}
                  disabled={!draft.trim()}
                  className="min-h-9 rounded-lg bg-primary px-3 text-[10px] font-black text-white disabled:opacity-40"
                >
                  Appliquer
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
