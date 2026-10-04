import { useEffect, useMemo, useState } from 'react';
import { CalendarCheck2, CheckCircle2, Clock3, RefreshCw, Users } from 'lucide-react';
import {
  stationPatientSessionService,
  type StationAppointmentSummary,
  type StationTodayAppointments,
} from '../../services/stationPatientSession';

const appointmentLabel = (appointment: StationAppointmentSummary) => {
  const date = new Date(appointment.datetimeStart);
  const time = Number.isNaN(date.getTime())
    ? appointment.datetimeStart
    : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return `${time} · ${appointment.durationMinutes} min`;
};

export const StationAppointmentArrival = ({
  sessionId, displayName, onLeave, backLabel,
}: {
  sessionId: string;
  displayName: string;
  onLeave: () => Promise<void>;
  backLabel: string;
}) => {
  const [result, setResult] = useState<StationTodayAppointments | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'arriving' | 'arrived' | 'error'>('loading');
  const [error, setError] = useState('');

  const load = async () => {
    setState('loading'); setError('');
    try {
      const next = await stationPatientSessionService.todayAppointments(sessionId);
      setResult(next);
      setSelectedId(next.status === 'single' ? next.appointments[0]?.appointmentId ?? null : null);
      setState('ready');
    } catch {
      setResult(null); setSelectedId(null);
      setError('Impossible de vérifier les rendez-vous. Prévenez l’équipe d’accueil.');
      setState('error');
    }
  };

  useEffect(() => { void load(); }, [sessionId]);

  const selected = useMemo(
    () => result?.appointments.find((item) => item.appointmentId === selectedId) ?? null,
    [result, selectedId],
  );

  const confirmArrival = async () => {
    if (!selectedId) return;
    setState('arriving'); setError('');
    try {
      const response = await stationPatientSessionService.arrive(sessionId, selectedId);
      if (response.status !== 'ARRIVED' || response.appointmentId !== selectedId) throw new Error('Unexpected arrival response');
      setState('arrived');
    } catch {
      setState('ready');
      setError('Arrivée non confirmée. Prévenez l’équipe d’accueil.');
    }
  };

  if (state === 'arrived') {
    return (
      <section data-station-arrival-confirmed className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-emerald-200 bg-card-bg p-6 text-center shadow-elite sm:p-8">
        <CheckCircle2 className="mx-auto text-emerald-600" size={42} aria-hidden="true" />
        <h2 className="mt-4 text-2xl font-black">Arrivée confirmée</h2>
        <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
        <p className="mt-3 text-sm font-semibold text-text-muted">Le cabinet sait que vous êtes arrivé(e). Aucun numéro de file ni ordre de passage n’a été attribué.</p>
        <button type="button" onClick={() => void onLeave()} className="mt-6 min-h-12 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg">{backLabel}</button>
      </section>
    );
  }

  return (
    <section data-station-arrival-bridge className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
      <CheckCircle2 className="mx-auto text-emerald-600" size={38} aria-hidden="true" />
      <h2 className="mt-3 text-2xl font-black">Identité confirmée</h2>
      <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
      {state === 'loading' && <p className="mt-6 font-black">Recherche de votre rendez-vous aujourd’hui…</p>}
      {state === 'error' && (
        <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4">
          <p role="alert" className="font-black text-rose-700">{error}</p>
          <button type="button" onClick={() => void load()} className="mt-4 inline-flex min-h-12 items-center gap-2 rounded-xl border border-rose-200 bg-white px-4 text-sm font-black text-rose-700">
            <RefreshCw size={16} aria-hidden="true" /> Réessayer
          </button>
        </div>
      )}
      {state !== 'loading' && result?.status === 'none' && (
        <div data-station-no-appointment className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-start">
          <div className="flex items-start gap-3">
            <Users className="mt-0.5 shrink-0 text-amber-700" size={20} aria-hidden="true" />
            <div>
              <p className="font-black text-amber-900">Aucun rendez-vous retrouvé aujourd’hui</p>
              <p className="mt-2 text-sm font-semibold leading-relaxed text-amber-800">Veuillez prévenir l’équipe d’accueil. La station ne crée pas automatiquement de rendez-vous.</p>
            </div>
          </div>
        </div>
      )}
      {state !== 'loading' && result && result.appointments.length > 0 && (
        <div className="mt-6 text-start">
          <p className="text-xs font-black uppercase tracking-wider text-primary">{result.status === 'multiple' ? 'Choisissez votre rendez-vous' : 'Votre rendez-vous'}</p>
          <div className="mt-3 grid gap-3">
            {result.appointments.map((appointment) => {
              const active = appointment.appointmentId === selectedId;
              return (
                <button key={appointment.appointmentId} type="button" data-station-appointment-id={appointment.appointmentId} aria-pressed={active}
                  onClick={() => setSelectedId(appointment.appointmentId)}
                  className={`min-h-16 rounded-2xl border p-4 text-start transition-elite ${active ? 'border-primary bg-primary/5' : 'border-border-main bg-main-bg'}`}>
                  <span className="flex items-center gap-2 font-black text-main"><Clock3 size={17} className="text-primary" aria-hidden="true" />{appointmentLabel(appointment)}</span>
                  <span className="mt-1 block text-xs font-semibold text-text-muted">Statut : {appointment.status}</span>
                </button>
              );
            })}
          </div>
          <button type="button" disabled={!selected || state === 'arriving'} onClick={() => void confirmArrival()}
            className="mt-5 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg disabled:opacity-50">
            <CalendarCheck2 size={18} aria-hidden="true" />{state === 'arriving' ? 'Confirmation…' : 'Confirmer mon arrivée'}
          </button>
          {error && <p role="alert" className="mt-3 font-black text-rose-700">{error}</p>}
        </div>
      )}
      <button type="button" onClick={() => void onLeave()} className="mt-5 min-h-12 w-full rounded-elite-sm border border-border-main px-5 text-sm font-black">{backLabel}</button>
    </section>
  );
};
