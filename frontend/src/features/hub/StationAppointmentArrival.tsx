import { useCallback, useEffect, useMemo, useState } from 'react';
import { CalendarCheck2, CheckCircle2, Clock3, RefreshCw, Users } from 'lucide-react';
import {
  stationPatientSessionService,
  type StationAppointmentSummary,
  type StationTodayAppointments,
} from '../../services/stationPatientSession';

export type StationFlowLanguage = 'fr' | 'ar' | 'en';

const COPY = {
  fr: {
    loadError: 'Impossible de vérifier les rendez-vous. Prévenez l’équipe d’accueil.',
    arrivalError: 'Arrivée non confirmée. Prévenez l’équipe d’accueil.',
    arrived: 'Arrivée confirmée',
    arrivedHint: 'Le cabinet sait que vous êtes arrivé(e). Aucun numéro de file ni ordre de passage n’a été attribué.',
    identified: 'Identité confirmée',
    searching: 'Recherche de votre rendez-vous aujourd’hui…',
    retry: 'Réessayer',
    none: 'Aucun rendez-vous retrouvé aujourd’hui',
    notifying: 'Prévenance de l’équipe d’accueil…',
    notified: 'L’équipe d’accueil a été prévenue. La station ne crée pas automatiquement de rendez-vous.',
    notifyFailed: 'Le signal n’a pas pu être transmis. Veuillez prévenir directement l’équipe d’accueil.',
    choose: 'Choisissez votre rendez-vous',
    yours: 'Votre rendez-vous',
    status: 'Statut',
    statusScheduled: 'Prévu', statusConfirmed: 'Confirmé', statusWaiting: 'En salle d’attente',
    confirming: 'Confirmation…',
    confirm: 'Confirmer mon arrivée',
  },
  en: {
    loadError: 'Unable to check appointments. Please notify the reception team.',
    arrivalError: 'Arrival not confirmed. Please notify the reception team.',
    arrived: 'Arrival confirmed',
    arrivedHint: 'The clinic knows you have arrived. No queue number or order of passage has been assigned.',
    identified: 'Identity confirmed',
    searching: 'Looking for your appointment today…',
    retry: 'Try again',
    none: 'No appointment found today',
    notifying: 'Notifying the reception team…',
    notified: 'The reception team has been notified. The station does not create an appointment automatically.',
    notifyFailed: 'The notification could not be sent. Please notify the reception team directly.',
    choose: 'Choose your appointment',
    yours: 'Your appointment',
    status: 'Status',
    statusScheduled: 'Scheduled', statusConfirmed: 'Confirmed', statusWaiting: 'Waiting',
    confirming: 'Confirming…',
    confirm: 'Confirm my arrival',
  },
  ar: {
    loadError: 'تعذر التحقق من المواعيد. يرجى إبلاغ فريق الاستقبال.',
    arrivalError: 'لم يتم تأكيد الوصول. يرجى إبلاغ فريق الاستقبال.',
    arrived: 'تم تأكيد الوصول',
    arrivedHint: 'تم إبلاغ العيادة بوصولكم. لم يتم تعيين رقم انتظار أو ترتيب مرور.',
    identified: 'تم تأكيد الهوية',
    searching: 'جارٍ البحث عن موعدكم اليوم…',
    retry: 'إعادة المحاولة',
    none: 'لم يتم العثور على موعد اليوم',
    notifying: 'جارٍ إبلاغ فريق الاستقبال…',
    notified: 'تم إبلاغ فريق الاستقبال. لا تنشئ المحطة موعداً تلقائياً.',
    notifyFailed: 'تعذر إرسال الإشعار. يرجى إبلاغ فريق الاستقبال مباشرةً.',
    choose: 'اختاروا موعدكم',
    yours: 'موعدكم',
    status: 'الحالة',
    statusScheduled: 'مجدول', statusConfirmed: 'مؤكد', statusWaiting: 'في قاعة الانتظار',
    confirming: 'جارٍ التأكيد…',
    confirm: 'تأكيد وصولي',
  },
} as const;

const LOCALE: Record<StationFlowLanguage, string> = { fr: 'fr-FR', en: 'en-GB', ar: 'ar-MA' };

const normalizeStatus = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[\s-]+/g, '_');

const appointmentStatusLabel = (status: string, language: StationFlowLanguage) => {
  const normalized = normalizeStatus(status);
  const copy = COPY[language];
  if (normalized === 'PREVU') return copy.statusScheduled;
  if (normalized === 'CONFIRME') return copy.statusConfirmed;
  if (normalized === 'EN_SALLE_ATTENTE') return copy.statusWaiting;
  return null;
};

const appointmentLabel = (appointment: StationAppointmentSummary, language: StationFlowLanguage) => {
  const date = new Date(appointment.datetimeStart);
  const time = Number.isNaN(date.getTime())
    ? appointment.datetimeStart
    : date.toLocaleTimeString(LOCALE[language], { hour: '2-digit', minute: '2-digit' });
  return `${time} · ${appointment.durationMinutes} min`;
};

export const StationAppointmentArrival = ({
  sessionId, displayName, onLeave, backLabel, language = 'fr',
}: {
  sessionId: string;
  displayName: string;
  onLeave: () => Promise<void>;
  backLabel: string;
  language?: StationFlowLanguage;
}) => {
  const copy = COPY[language];
  const [result, setResult] = useState<StationTodayAppointments | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'arriving' | 'arrived' | 'error'>('loading');
  const [error, setError] = useState('');
  const [staffSignal, setStaffSignal] = useState<'idle' | 'sending' | 'sent' | 'failed'>('idle');

  const load = useCallback(async () => {
    setState('loading'); setError('');
    try {
      const next = await stationPatientSessionService.todayAppointments(sessionId);
      setResult(next);
      setSelectedId(next.status === 'single' ? next.appointments[0]?.appointmentId ?? null : null);
      if (next.status === 'none' && next.staffActionRequired) {
        setStaffSignal('sending');
        try {
          const signal = await stationPatientSessionService.requestStaffAssistance(sessionId);
          setStaffSignal(signal.status === 'STAFF_NOTIFIED' ? 'sent' : 'failed');
        } catch {
          setStaffSignal('failed');
        }
      } else {
        setStaffSignal('idle');
      }
      setState('ready');
    } catch {
      setResult(null); setSelectedId(null);
      setError(copy.loadError);
      setStaffSignal('failed');
      setState('error');
    }
  }, [copy.loadError, sessionId]);

  useEffect(() => { void load(); }, [load]);

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
      setError(copy.arrivalError);
    }
  };

  if (state === 'arrived') {
    return (
      <section data-station-arrival-confirmed className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-emerald-200 bg-card-bg p-6 text-center shadow-elite sm:p-8">
        <CheckCircle2 className="mx-auto text-emerald-600" size={42} aria-hidden="true" />
        <h2 className="mt-4 text-2xl font-black">{copy.arrived}</h2>
        <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
        <p className="mt-3 text-sm font-semibold text-text-muted">{copy.arrivedHint}</p>
        <button type="button" onClick={() => void onLeave()} className="mt-6 min-h-12 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg">{backLabel}</button>
      </section>
    );
  }

  return (
    <section data-station-arrival-bridge className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
      <CheckCircle2 className="mx-auto text-emerald-600" size={38} aria-hidden="true" />
      <h2 className="mt-3 text-2xl font-black">{copy.identified}</h2>
      <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
      {state === 'loading' && <p className="mt-6 font-black">{copy.searching}</p>}
      {state === 'error' && (
        <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4">
          <p role="alert" className="font-black text-rose-700">{error}</p>
          <button type="button" onClick={() => void load()} className="mt-4 inline-flex min-h-12 items-center gap-2 rounded-xl border border-rose-200 bg-white px-4 text-sm font-black text-rose-700">
            <RefreshCw size={16} aria-hidden="true" /> {copy.retry}
          </button>
        </div>
      )}
      {state !== 'loading' && result?.status === 'none' && (
        <div data-station-no-appointment className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-start">
          <div className="flex items-start gap-3">
            <Users className="mt-0.5 shrink-0 text-amber-700" size={20} aria-hidden="true" />
            <div>
              <p className="font-black text-amber-900">{copy.none}</p>
              {staffSignal === 'sending' && <p className="mt-2 text-sm font-semibold leading-relaxed text-amber-800">{copy.notifying}</p>}
              {staffSignal === 'sent' && <p data-station-staff-notified className="mt-2 text-sm font-semibold leading-relaxed text-amber-800">{copy.notified}</p>}
              {staffSignal === 'failed' && <p role="alert" className="mt-2 text-sm font-semibold leading-relaxed text-rose-700">{copy.notifyFailed}</p>}
            </div>
          </div>
        </div>
      )}
      {state !== 'loading' && result && result.appointments.length > 0 && (
        <div className="mt-6 text-start">
          <p className="text-xs font-black uppercase tracking-wider text-primary">{result.status === 'multiple' ? copy.choose : copy.yours}</p>
          <div className="mt-3 grid gap-3">
            {result.appointments.map((appointment) => {
              const active = appointment.appointmentId === selectedId;
              return (
                <button key={appointment.appointmentId} type="button" data-station-appointment-id={appointment.appointmentId} aria-pressed={active}
                  onClick={() => setSelectedId(appointment.appointmentId)}
                  className={`min-h-16 rounded-2xl border p-4 text-start transition-elite ${active ? 'border-primary bg-primary/5' : 'border-border-main bg-main-bg'}`}>
                  <span className="flex items-center gap-2 font-black text-main"><Clock3 size={17} className="text-primary" aria-hidden="true" />{appointmentLabel(appointment, language)}</span>
                  {appointmentStatusLabel(appointment.status, language) && <span className="mt-1 block text-xs font-semibold text-text-muted">{copy.status} : {appointmentStatusLabel(appointment.status, language)}</span>}
                </button>
              );
            })}
          </div>
          <button type="button" disabled={!selected || state === 'arriving'} onClick={() => void confirmArrival()}
            className="mt-5 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg disabled:opacity-50">
            <CalendarCheck2 size={18} aria-hidden="true" />{state === 'arriving' ? copy.confirming : copy.confirm}
          </button>
          {error && <p role="alert" className="mt-3 font-black text-rose-700">{error}</p>}
        </div>
      )}
      <button type="button" onClick={() => void onLeave()} className="mt-5 min-h-12 w-full rounded-elite-sm border border-border-main px-5 text-sm font-black">{backLabel}</button>
    </section>
  );
};
