import { useEffect, useState } from 'react';
import { CalendarPlus, Camera, CircleDollarSign, ScanLine, UserPlus, X, Plus } from 'lucide-react';
import type { MobileQuickActionCapabilities } from '../hooks/useMobileQuickActionCapabilities';

export type MobileQuickPatientAction = 'photo' | 'scan' | 'payment';

export function MobileQuickActionHub({
  capabilities,
  capabilitiesLoaded = true,
  isOnline,
  defaultOpen = false,
  onNewAppointment,
  onNewPatient,
  onPatientAction,
}: {
  capabilities: MobileQuickActionCapabilities;
  capabilitiesLoaded?: boolean;
  isOnline: boolean;
  defaultOpen?: boolean;
  onNewAppointment: () => void;
  onNewPatient: () => void;
  onPatientAction: (action: MobileQuickPatientAction) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const hasAnyAction = capabilities.can_create_appointment
    || capabilities.can_create_patient
    || capabilities.can_open_clinical_context
    || capabilities.can_pay;

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  useEffect(() => {
    if (capabilitiesLoaded && !hasAnyAction) setOpen(false);
  }, [capabilitiesLoaded, hasAnyAction]);

  const run = (action: () => void) => {
    if (!isOnline) return;
    setOpen(false);
    action();
  };

  if (!capabilitiesLoaded || !hasAnyAction) return null;

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-[70]" data-mobile-quick-action-hub>
          <button
            type="button"
            aria-label="Fermer le fond des actions rapides"
            className="absolute inset-0 bg-slate-950/20 backdrop-blur-[1px]"
            onClick={() => setOpen(false)}
          />

          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="mobile-quick-action-title"
            className="absolute left-4 right-4 bottom-[178px] mx-auto max-w-[720px] rounded-[30px] border border-glass-border bg-card p-4 shadow-elite-hover"
            style={{
              backgroundColor: 'var(--glass-bg)',
              fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
            }}
          >
            <div className="mx-auto mb-3 h-1.5 w-16 rounded-full bg-border-main" aria-hidden="true" />
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h2 id="mobile-quick-action-title" className="text-lg font-black text-text-main">Action rapide</h2>
                <p className="mt-1 text-[11px] font-bold text-text-muted">Que voulez-vous faire ?</p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Fermer"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[15px] border border-glass-border bg-background text-text-muted active:scale-95"
              >
                <X size={18} />
              </button>
            </div>

            {!isOnline && (
              <div className="mb-3 rounded-[16px] border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-[10px] font-black text-amber-600">
                Connexion cabinet requise pour créer ou enregistrer une action.
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              {capabilities.can_create_appointment && (
                <button
                  type="button"
                  disabled={!isOnline}
                  onClick={() => run(onNewAppointment)}
                  className="min-h-[72px] rounded-[20px] border border-primary/20 bg-primary/10 p-3 text-left text-primary active:scale-[0.98] disabled:opacity-40"
                >
                  <CalendarPlus size={19} />
                  <span className="mt-3 block text-xs font-black">Nouveau RDV</span>
                </button>
              )}
              {capabilities.can_create_patient && (
                <button
                  type="button"
                  disabled={!isOnline}
                  onClick={() => run(onNewPatient)}
                  className="min-h-[72px] rounded-[20px] border border-primary/20 bg-primary/10 p-3 text-left text-primary active:scale-[0.98] disabled:opacity-40"
                >
                  <UserPlus size={19} />
                  <span className="mt-3 block text-xs font-black">Nouveau patient</span>
                </button>
              )}
              {capabilities.can_open_clinical_context && (
                <>
                  <button
                    type="button"
                    disabled={!isOnline}
                    onClick={() => run(() => onPatientAction('photo'))}
                    className="min-h-[72px] rounded-[20px] border border-glass-border bg-background p-3 text-left text-text-main active:scale-[0.98] disabled:opacity-40"
                  >
                    <Camera size={19} className="text-primary" />
                    <span className="mt-3 block text-xs font-black">Photo clinique</span>
                  </button>
                  <button
                    type="button"
                    disabled={!isOnline}
                    onClick={() => run(() => onPatientAction('scan'))}
                    className="min-h-[72px] rounded-[20px] border border-glass-border bg-background p-3 text-left text-text-main active:scale-[0.98] disabled:opacity-40"
                  >
                    <ScanLine size={19} className="text-primary" />
                    <span className="mt-3 block text-xs font-black">Scanner document</span>
                  </button>
                </>
              )}
            </div>

            {capabilities.can_pay && (
              <button
                type="button"
                disabled={!isOnline}
                onClick={() => run(() => onPatientAction('payment'))}
                className="mt-2.5 flex min-h-[58px] w-full items-center gap-3 rounded-[20px] bg-primary px-4 text-left text-white shadow-sm active:scale-[0.99] disabled:opacity-40"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-[13px] bg-white/10">
                  <CircleDollarSign size={19} />
                </span>
                <span>
                  <span className="block text-xs font-black">Encaisser rapidement</span>
                  <span className="mt-0.5 block text-[9px] font-bold text-white/70">Accès financier requis</span>
                </span>
              </button>
            )}
          </section>
        </div>
      )}

      <div className="fixed bottom-32 right-6 z-[80]">
        <button
          type="button"
          aria-label={open ? 'Fermer les actions rapides' : 'Ouvrir les actions rapides'}
          aria-expanded={open}
          onClick={() => setOpen(value => !value)}
          className="flex h-14 w-14 items-center justify-center rounded-full border border-white/20 bg-primary text-white shadow-[0_8px_30px_rgba(var(--primary-rgb),0.4)] transition-transform hover:scale-105 active:scale-95"
        >
          {open ? <X size={24} /> : <Plus size={24} />}
        </button>
      </div>
    </>
  );
}
