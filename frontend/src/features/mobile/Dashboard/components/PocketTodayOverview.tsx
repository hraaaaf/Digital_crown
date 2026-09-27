import { Bell, CalendarDays, CheckCircle2, ChevronRight, Clock3, UsersRound } from 'lucide-react';
import type { Appointment, Snapshot } from '../types';

function nextOperationalAppointment(appointments: Appointment[]): Appointment | null {
  return appointments
    .filter((appointment) => appointment.status !== 'TERMINE' && appointment.status !== 'ANNULE')
    .slice()
    .sort((a, b) => a.time.localeCompare(b.time))[0] ?? null;
}

export function PocketTodayOverview({
  snapshot,
  selectedDate,
  onOpenPatient,
  onOpenWaitingRoom,
  onOpenFrontdesk,
  onOpenAlerts,
}: {
  snapshot: Snapshot | null;
  selectedDate: string;
  onOpenPatient: (patientId: number) => void;
  onOpenWaitingRoom: () => void;
  onOpenFrontdesk: () => void;
  onOpenAlerts: () => void;
}) {
  const appointments = snapshot?.appointments ?? [];
  const role = snapshot?.role ?? 'DENTISTE';
  const isAssistant = role === 'SECRETAIRE';
  const waitingCount = appointments.filter((appointment) => appointment.status === 'EN_ATTENTE').length;
  const completedCount = appointments.filter((appointment) => appointment.status === 'TERMINE').length;
  const nextAppointment = nextOperationalAppointment(appointments);
  const remainingCount = appointments.filter(
    (appointment) => appointment.status !== 'TERMINE' && appointment.status !== 'ANNULE',
  ).length;
  const today = new Date();
  const localToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const isToday = selectedDate === localToday;
  const selectedDateLabel = (() => {
    const parsed = new Date(`${selectedDate}T12:00:00`);
    if (Number.isNaN(parsed.getTime())) return 'Journée sélectionnée';
    return `Journée du ${parsed.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}`;
  })();

  return (
    <section
      data-dc-pocket-today
      data-dc-pocket-role={isAssistant ? 'assistant' : 'practitioner'}
      className="mb-5 space-y-3"
    >
      <div className="rounded-[28px] border border-glass-border bg-glass-bg p-5 shadow-elite backdrop-blur-md">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Digital Crown Pocket</p>
            <h1 className="mt-1 font-outfit text-[27px] font-black tracking-tight text-text-main">
              {isToday ? 'Aujourd’hui' : selectedDateLabel}
            </h1>
            <p className="mt-1 text-[11px] font-bold text-text-muted">
              {isAssistant ? 'Vue assistante · flux cabinet' : 'Vue praticien · priorité clinique'}
            </p>
          </div>
          <div className="grid h-12 w-12 shrink-0 place-items-center rounded-[17px] border border-primary/10 bg-primary/5 text-primary">
            {isAssistant ? <UsersRound size={21} /> : <Clock3 size={21} />}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-[17px] border border-border-main bg-background px-3 py-3">
            <CalendarDays size={14} className="text-primary" />
            <p className="mt-2 text-[18px] font-black text-text-main">{appointments.length}</p>
            <p className="text-[9px] font-black uppercase tracking-wider text-text-muted">RDV</p>
          </div>
          <button
            type="button"
            onClick={onOpenWaitingRoom}
            data-dc-pocket-waiting-count={waitingCount}
            className="rounded-[17px] border border-amber-500/20 bg-amber-500/5 px-3 py-3 text-left active:scale-[0.98]"
          >
            <UsersRound size={14} className="text-amber-700" />
            <p className="mt-2 text-[18px] font-black text-text-main">{waitingCount}</p>
            <p className="text-[9px] font-black uppercase tracking-wider text-text-muted">Attente</p>
          </button>
          <div
            data-dc-pocket-progress-count={isAssistant ? remainingCount : completedCount}
            className="rounded-[17px] border border-emerald-500/20 bg-emerald-500/5 px-3 py-3"
          >
            <CheckCircle2 size={14} className="text-emerald-600" />
            <p className="mt-2 text-[18px] font-black text-text-main">{isAssistant ? remainingCount : completedCount}</p>
            <p className="text-[9px] font-black uppercase tracking-wider text-text-muted">
              {isAssistant ? 'À gérer' : 'Terminés'}
            </p>
          </div>
        </div>
      </div>

      {!isAssistant && nextAppointment && (
        <article className="rounded-[24px] border border-primary/15 bg-card p-4 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
          <div className="flex items-start gap-3">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-[16px] bg-primary/10 text-primary">
              <span className="text-[12px] font-black">{nextAppointment.time}</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Prochain patient</p>
              <h2 className="mt-1 truncate text-[16px] font-black text-text-main">{nextAppointment.patient_name}</h2>
              <p className="mt-0.5 truncate text-[10px] font-bold uppercase tracking-wider text-text-muted">
                {nextAppointment.motif} · {nextAppointment.duration_minutes} min
              </p>
            </div>
          </div>
          <button
            type="button"
            disabled={!nextAppointment.patient_id}
            onClick={() => nextAppointment.patient_id && onOpenPatient(nextAppointment.patient_id)}
            className="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-[16px] bg-primary px-4 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ouvrir le dossier <ChevronRight size={15} />
          </button>
        </article>
      )}

      <div className={`grid gap-2 ${isAssistant ? 'grid-cols-3' : 'grid-cols-2'}`}>
        <button
          type="button"
          onClick={onOpenWaitingRoom}
          className="min-h-12 rounded-[16px] border border-glass-border bg-card px-3 text-[10px] font-black text-text-main shadow-sm active:scale-[0.98]"
        >
          Salle d’attente
        </button>
        {isAssistant && (
          <button
            type="button"
            onClick={onOpenFrontdesk}
            className="min-h-12 rounded-[16px] border border-glass-border bg-card px-3 text-[10px] font-black text-text-main shadow-sm active:scale-[0.98]"
          >
            Accueil
          </button>
        )}
        <button
          type="button"
          onClick={onOpenAlerts}
          className="flex min-h-12 items-center justify-center gap-1.5 rounded-[16px] border border-glass-border bg-card px-3 text-[10px] font-black text-text-main shadow-sm active:scale-[0.98]"
        >
          <Bell size={13} /> Alertes
        </button>
      </div>
    </section>
  );
}
