import { CalendarDays, ChevronRight, Clock3, WifiOff } from 'lucide-react';
import type { Appointment, Snapshot } from '../types';
import { STATUS_META } from '../types';

/**
 * Pocket's day agenda is deliberately read-only and uses the paired-device
 * /api/mobile/snapshot contract. Never mount the desktop drag-and-drop AgendaView:
 * it mutates /api/appointments with desktop auth semantics.
 */
export function PocketAgendaDay({
  snapshot,
  selectedDate,
  isOnline,
  onOpenPatient,
}: {
  snapshot: Snapshot | null;
  selectedDate: string;
  isOnline: boolean;
  onOpenPatient: (id: number) => void;
}) {
  const appointments = (snapshot?.appointments ?? [])
    .filter(item => !item.date || item.date === selectedDate)
    .slice()
    .sort((a, b) => a.time.localeCompare(b.time) || a.id - b.id);
  const label = new Date(`${selectedDate}T12:00:00`);
  const dateLabel = Number.isNaN(label.getTime())
    ? 'Journée sélectionnée'
    : label.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <section data-dc-pocket-agenda className="space-y-3 pb-8">
      <header className="rounded-[24px] border border-glass-border bg-card p-5 shadow-elite">
        <div className="flex items-center gap-2 text-primary">
          <CalendarDays size={18} aria-hidden="true" />
          <h2 className="text-[20px] font-black">Agenda</h2>
        </div>
        <p className="mt-2 text-[12px] font-bold capitalize text-text-main">{dateLabel}</p>
        <p className="mt-1 text-[11px] font-semibold text-text-muted">
          {appointments.length} rendez-vous · vue rapide en lecture seule
        </p>
      </header>

      {!isOnline && (
        <p role="status" className="flex items-start gap-2 rounded-[16px] border border-amber-500/20 bg-amber-500/5 p-3 text-[11px] font-bold text-amber-700">
          <WifiOff size={16} className="shrink-0" aria-hidden="true" />
          Hors ligne : agenda éventuellement en cache. Vérifiez les changements au cabinet avant toute action.
        </p>
      )}

      {!snapshot ? (
        <div className="rounded-[20px] border border-glass-border bg-card p-6 text-center text-[12px] font-bold text-text-muted">
          Agenda non chargé. Synchronisez votre Pocket avec le cabinet.
        </div>
      ) : appointments.length === 0 ? (
        <div className="rounded-[20px] border border-glass-border bg-card p-6 text-center text-[12px] font-bold text-text-muted">
          Aucun rendez-vous pour cette journée.
        </div>
      ) : (
        <div className="space-y-2">
          {appointments.map((appointment: Appointment) => {
            const meta = appointment.status ? STATUS_META[appointment.status] : null;
            const content = (
              <>
                <div className="grid h-11 w-14 shrink-0 place-items-center rounded-[14px] bg-primary/10 text-[12px] font-black text-primary">
                  {appointment.time}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-black text-text-main">{appointment.patient_name}</p>
                  <p className="mt-0.5 truncate text-[10px] font-semibold text-text-muted">{appointment.motif || 'Rendez-vous'}</p>
                  {meta && (
                    <span className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-[9px] font-black ${meta.className}`}>
                      {meta.label}
                    </span>
                  )}
                </div>
                {appointment.patient_id && <ChevronRight size={17} className="shrink-0 text-primary" aria-hidden="true" />}
              </>
            );
            return appointment.patient_id ? (
              <button
                type="button"
                key={appointment.id}
                aria-label={`Ouvrir le dossier de ${appointment.patient_name}`}
                onClick={() => onOpenPatient(appointment.patient_id as number)}
                className="flex min-h-[76px] w-full items-center gap-3 rounded-[20px] border border-glass-border bg-card px-3 py-2 text-left shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              >
                {content}
              </button>
            ) : (
              <div key={appointment.id} className="flex min-h-[76px] items-center gap-3 rounded-[20px] border border-glass-border bg-card px-3 py-2 shadow-sm">
                {content}
              </div>
            );
          })}
        </div>
      )}
      <p className="flex items-center justify-center gap-1.5 text-[10px] font-bold text-text-muted">
        <Clock3 size={13} aria-hidden="true" /> La planification complète reste sur le poste de travail.
      </p>
    </section>
  );
}
