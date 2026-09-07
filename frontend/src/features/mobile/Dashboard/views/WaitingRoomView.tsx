import { Armchair, Clock3, Ticket, UsersRound } from 'lucide-react';
import type { ApptStatus, Snapshot } from '../types';

export function WaitingRoomView({
  snapshot,
  onStatusChange,
}: {
  snapshot: Snapshot | null;
  onStatusChange: (id: number, status: ApptStatus) => void;
}) {
  const waiting = (snapshot?.appointments ?? [])
    .filter(appointment => appointment.status === 'EN_ATTENTE')
    .slice()
    .sort((a, b) => a.time.localeCompare(b.time));

  return (
    <section data-mob5i-waiting-room className="space-y-4 pb-8">
      <div className="rounded-[28px] border border-glass-border bg-glass-bg p-5 shadow-elite backdrop-blur-md">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-text-muted">Flux clinique</p>
            <h2 className="mt-1 font-outfit text-[25px] font-black tracking-tight text-text-main">Salle d’attente</h2>
            <p className="mt-1 text-[11px] font-semibold text-text-muted">Patients actuellement présents</p>
          </div>
          <div
            data-mob5i-waiting-count={waiting.length}
            className="grid min-h-12 min-w-12 place-items-center rounded-[18px] border border-amber-500/20 bg-amber-500/10 px-3 text-[18px] font-black text-amber-700"
            aria-label={`${waiting.length} patient${waiting.length > 1 ? 's' : ''} en salle d’attente`}
          >
            {waiting.length}
          </div>
        </div>
      </div>

      {waiting.length === 0 ? (
        <div className="rounded-[28px] border border-border-main bg-card px-5 py-14 text-center shadow-elite">
          <div className="mx-auto grid h-16 w-16 place-items-center rounded-[22px] border border-primary/10 bg-primary/5 text-primary">
            <UsersRound size={28} />
          </div>
          <h3 className="mt-4 font-outfit text-[17px] font-black text-text-main">Aucun patient en salle d’attente</h3>
          <p className="mx-auto mt-1 max-w-[280px] text-[11px] font-semibold text-text-muted">
            Les patients marqués « En salle d’attente » depuis l’Agenda apparaîtront ici.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {waiting.map(appointment => (
            <article
              key={appointment.id}
              data-mob5i-waiting-patient={appointment.id}
              className="rounded-[24px] border border-glass-border bg-glass-bg p-4 shadow-elite backdrop-blur-md"
            >
              <div className="flex items-start gap-3">
                <div className="grid h-12 w-12 shrink-0 place-items-center rounded-[16px] border border-primary/10 bg-primary/5 text-primary">
                  <Clock3 size={19} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex min-w-0 items-center gap-2">
                    {appointment.ticket_number != null && (
                      <span className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-[9px] font-black text-amber-700">
                        <Ticket size={10} /> #{appointment.ticket_number}
                      </span>
                    )}
                    <span className="text-[11px] font-black text-primary">{appointment.time}</span>
                  </div>
                  <h3 className="mt-1 truncate font-outfit text-[16px] font-black text-text-main">{appointment.patient_name}</h3>
                  <p className="mt-0.5 truncate text-[10px] font-bold uppercase tracking-wider text-text-muted">{appointment.motif}</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onStatusChange(appointment.id, 'EN_COURS')}
                className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-[16px] border border-primary/20 bg-primary text-[10px] font-black uppercase tracking-widest text-white shadow-sm active:scale-[0.99]"
              >
                <Armchair size={15} /> Au fauteuil
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
