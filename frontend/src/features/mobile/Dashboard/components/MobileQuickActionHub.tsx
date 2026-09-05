import { useEffect, useState } from 'react';
import { CalendarPlus, Camera, CircleDollarSign, ScanLine, UserPlus, X, Plus } from 'lucide-react';
import type { MobileQuickActionCapabilities } from '../hooks/useMobileQuickActionCapabilities';

export type MobileQuickPatientAction = 'photo' | 'scan' | 'payment';

export function MobileQuickActionHub({
  capabilities,
  capabilitiesLoaded = true,
  isOnline,
  defaultOpen = false,
  open: controlledOpen,
  onOpenChange,
  hideLauncher = false,
  onNewAppointment,
  onNewPatient,
  onPatientAction,
}: {
  capabilities: MobileQuickActionCapabilities;
  capabilitiesLoaded?: boolean;
  isOnline: boolean;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  hideLauncher?: boolean;
  onNewAppointment: () => void;
  onNewPatient: () => void;
  onPatientAction: (action: MobileQuickPatientAction) => void;
}) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const open = controlledOpen ?? internalOpen;
  const hasAnyAction = capabilities.can_create_appointment
    || capabilities.can_create_patient
    || capabilities.can_open_clinical_context
    || capabilities.can_pay;

  const setOpen = (next: boolean) => {
    if (controlledOpen === undefined) setInternalOpen(next);
    onOpenChange?.(next);
  };

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  useEffect(() => {
    if (capabilitiesLoaded && !hasAnyAction && open) setOpen(false);
  }, [capabilitiesLoaded, hasAnyAction, open]);

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
            className="absolute left-4 right-4 bottom-[178px] mx-auto max-w-[720px] rounded-[28px] border border-glass-border bg-card p-4 shadow-elite-hover"
            style={{
              backgroundColor: 'var(--glass-bg)',
              fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
            }}
          >
            <div className="mx-auto mb-2 h-[5px] w-[68px] rounded-full bg-border-main" aria-hidden="true" />
            <div className="mb-2.5">
              <h2 id="mobile-quick-action-title" className="text-[19px] leading-[23px] font-black text-text-main">Action rapide</h2>
              <p className="mt-1 text-[10px] leading-[15px] font-bold text-text-muted">Que voulez-vous faire ?</p>
            </div>

            {!isOnline && (
              <div className="mb-2.5 rounded-[16px] border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-[10px] font-black text-amber-600">
                Connexion cabinet requise pour créer ou enregistrer une action.
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              {capabilities.can_create_appointment && (
                <button
                  type="button"
                  disabled={!isOnline}
                  onClick={() => run(onNewAppointment)}
                  className="min-h-[65px] rounded-[18px] border border-primary/20 bg-primary/10 p-2.5 text-left text-primary active:scale-[0.98] disabled:opacity-40"
                >
                  <CalendarPlus size={17} />
                  <span className="mt-2 block text-[10px] leading-[15px] font-black">Nouveau RDV</span>
                </button>
              )}
              {capabilities.can_create_patient && (
                <button
                  type="button"
                  disabled={!isOnline}
                  onClick={() => run(onNewPatient)}
                  className="min-h-[65px] rounded-[18px] border border-primary/20 bg-primary/10 p-2.5 text-left text-primary active:scale-[0.98] disabled:opacity-40"
                >
                  <UserPlus size={17} />
                  <span className="mt-2 block text-[10px] leading-[15px] font-black">Nouveau patient</span>
                </button>
              )}
              {capabilities.can_open_clinical_context && (
                <>
                  <button
                    type="button"
                    disabled={!isOnline}
                    onClick={() => run(() => onPatientAction('photo'))}
                    className="min-h-[65px] rounded-[18px] border border-glass-border bg-background p-2.5 text-left text-text-main active:scale-[0.98] disabled:opacity-40"
                  >
                    <Camera size={17} className="text-primary" />
                    <span className="mt-2 block text-[10px] leading-[15px] font-black">Photo clinique</span>
                  </button>
                  <button
                    type="button"
                    disabled={!isOnline}
                    onClick={() => run(() => onPatientAction('scan'))}
                    className="min-h-[65px] rounded-[18px] border border-glass-border bg-background p-2.5 text-left text-text-main active:scale-[0.98] disabled:opacity-40"
                  >
                    <ScanLine size={17} className="text-primary" />
                    <span className="mt-2 block text-[10px] leading-[15px] font-black">Scanner document</span>
                  </button>
                </>
              )}
            </div>

            {capabilities.can_pay && (
              <button
                type="button"
                disabled={!isOnline}
                onClick={() => run(() => onPatientAction('payment'))}
                className="mt-2.5 flex min-h-[56px] w-full items-center gap-3 rounded-[18px] bg-primary px-4 text-left text-white shadow-sm active:scale-[0.99] disabled:opacity-40"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10">
                  <CircleDollarSign size={17} />
                </span>
                <span>
                  <span className="block text-[11px] leading-[15px] font-black">Encaisser rapidement</span>
                  <span className="mt-0.5 block text-[8px] leading-[12px] font-bold text-white/70">Accès financier requis</span>
                </span>
              </button>
            )}
          </section>
        </div>
      )}

      {!hideLauncher && (
        <div className="fixed bottom-32 right-6 z-[80]">
          <button
            type="button"
            aria-label={open ? 'Fermer les actions rapides' : 'Ouvrir les actions rapides'}
            aria-expanded={open}
            onClick={() => setOpen(!open)}
            className="flex h-14 w-14 items-center justify-center rounded-full border border-white/20 bg-primary text-white shadow-[0_8px_30px_rgba(var(--primary-rgb),0.4)] transition-transform hover:scale-105 active:scale-95"
          >
            {open ? <X size={24} /> : <Plus size={24} />}
          </button>
        </div>
      )}
    </>
  );
}
