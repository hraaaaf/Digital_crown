import { WifiOff } from 'lucide-react';
import { MobilePatientsView } from './MobilePatientsView';

export function MobilePatientsGate({
  isOnline,
  onClose,
}: {
  isOnline: boolean;
  onClose: () => void;
}) {
  if (isOnline) {
    return <MobilePatientsView onClose={onClose} />;
  }

  return (
    <section data-mobile-patient-offline className="pb-10">
      <div
        className="rounded-[24px] border border-amber-500/25 bg-card p-5 shadow-elite"
        style={{ backgroundColor: 'var(--glass-bg)' }}
      >
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-[14px] bg-amber-500/10 text-amber-600">
            <WifiOff size={19} aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-amber-600">
              Cabinet hors réseau
            </p>
            <h2 className="mt-1 text-lg font-black text-text-main">Recherche patient indisponible hors ligne</h2>
            <p className="mt-2 text-xs font-bold leading-relaxed text-text-muted">
              Les données patient ne sont pas recherchées ni mises en cache par ce cockpit. Reconnectez-vous au réseau du cabinet pour ouvrir un dossier.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-5 min-h-12 w-full rounded-[16px] border border-primary/20 bg-primary/10 px-4 text-xs font-black text-primary active:scale-[0.99] transition-transform"
        >
          Retour à l’Agenda
        </button>
      </div>
    </section>
  );
}
