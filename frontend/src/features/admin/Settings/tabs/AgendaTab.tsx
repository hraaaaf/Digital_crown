import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Calendar,
  CalendarDays,
  Check,
  Clock3,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import { api } from '../../../../services/api';
import { toast } from 'react-hot-toast';
import { SettingsReadError } from '../components/SharedUI';
import { cn } from '../../../../utils/cn';

type WeekdayKey = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

type DaySchedule = {
  is_open: boolean;
  is_continuous: boolean;
  morning_start: string;
  morning_end: string;
  afternoon_start: string;
  afternoon_end: string;
};

type WeeklySchedule = Record<WeekdayKey, DaySchedule>;

type AgendaSettings = {
  id?: number;
  opening_time_morning: string;
  closing_time_morning: string;
  opening_time_afternoon: string;
  closing_time_afternoon: string;
  is_continuous: boolean;
  agenda_mode: 'EXACT' | 'BLOCK';
  use_tickets: boolean;
  weekly_schedule: WeeklySchedule;
};

type AgendaException = {
  id: number;
  start_date: string;
  end_date: string;
  reason: string;
  is_holiday: boolean;
  created_at: string;
};

const WEEKDAYS: Array<{ key: WeekdayKey; label: string; short: string }> = [
  { key: 'monday', label: 'Lundi', short: 'Lun' },
  { key: 'tuesday', label: 'Mardi', short: 'Mar' },
  { key: 'wednesday', label: 'Mercredi', short: 'Mer' },
  { key: 'thursday', label: 'Jeudi', short: 'Jeu' },
  { key: 'friday', label: 'Vendredi', short: 'Ven' },
  { key: 'saturday', label: 'Samedi', short: 'Sam' },
  { key: 'sunday', label: 'Dimanche', short: 'Dim' },
];

const makeLegacyWeek = (raw: Partial<AgendaSettings>): WeeklySchedule => {
  const day: DaySchedule = {
    is_open: true,
    is_continuous: Boolean(raw.is_continuous),
    morning_start: raw.opening_time_morning || '09:00',
    morning_end: raw.closing_time_morning || '13:00',
    afternoon_start: raw.opening_time_afternoon || '14:00',
    afternoon_end: raw.closing_time_afternoon || '18:00',
  };
  return Object.fromEntries(WEEKDAYS.map(({ key }) => [key, { ...day }])) as WeeklySchedule;
};

const normalizeSettings = (raw: Partial<AgendaSettings>): AgendaSettings => ({
  opening_time_morning: raw.opening_time_morning || '09:00',
  closing_time_morning: raw.closing_time_morning || '13:00',
  opening_time_afternoon: raw.opening_time_afternoon || '14:00',
  closing_time_afternoon: raw.closing_time_afternoon || '18:00',
  is_continuous: Boolean(raw.is_continuous),
  agenda_mode: raw.agenda_mode === 'BLOCK' ? 'BLOCK' : 'EXACT',
  use_tickets: Boolean(raw.use_tickets),
  weekly_schedule: raw.weekly_schedule || makeLegacyWeek(raw),
});

const timeToMinutes = (value: string) => {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
};

const validateWeek = (week: WeeklySchedule): string | null => {
  for (const { key, label } of WEEKDAYS) {
    const day = week[key];
    if (!day.is_open) continue;
    if (timeToMinutes(day.morning_start) >= timeToMinutes(day.morning_end)) {
      return `${label} : l'heure de fin doit être après l'ouverture.`;
    }
    if (!day.is_continuous) {
      if (timeToMinutes(day.afternoon_start) >= timeToMinutes(day.afternoon_end)) {
        return `${label} : la fin d'après-midi doit être après son ouverture.`;
      }
      if (timeToMinutes(day.morning_end) > timeToMinutes(day.afternoon_start)) {
        return `${label} : les plages matin et après-midi se chevauchent.`;
      }
    }
  }
  return null;
};

const formatDate = (value: string) => new Intl.DateTimeFormat('fr-FR', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
}).format(new Date(value));

const ExceptionModal: React.FC<{
  onClose: () => void;
  onCreated: (exception: AgendaException) => void;
}> = ({ onClose, onCreated }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!startDate || !endDate) {
      setError('Les dates de début et de fin sont obligatoires.');
      return;
    }
    if (endDate < startDate) {
      setError('La date de fin doit être postérieure ou égale à la date de début.');
      return;
    }
    setSaving(true);
    try {
      const response = await api.post('/agenda/exceptions', {
        start_date: `${startDate}T00:00:00`,
        end_date: `${endDate}T23:59:59`,
        reason: reason.trim() || 'Fermeture du cabinet',
        is_holiday: false,
      });
      onCreated(response.data);
      toast.success('Fermeture ajoutée');
      onClose();
    } catch (err) {
      console.error(err);
      setError("Impossible d'ajouter cette fermeture.");
      toast.error("Erreur lors de l'ajout de la fermeture");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-950/40 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) onClose();
      }}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="agenda-exception-title" className="w-full max-w-lg rounded-t-[2rem] bg-white p-6 shadow-2xl sm:rounded-[2rem] sm:p-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">Agenda du cabinet</p>
            <h3 id="agenda-exception-title" className="mt-1 text-2xl font-black tracking-tight text-slate-900">Ajouter une fermeture</h3>
          </div>
          <button type="button" onClick={onClose} disabled={saving} aria-label="Fermer" className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-50 disabled:opacity-40">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="block text-xs font-black uppercase tracking-wider text-slate-500">Début *</span>
              <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 font-semibold text-slate-800 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100" />
            </label>
            <label className="space-y-2">
              <span className="block text-xs font-black uppercase tracking-wider text-slate-500">Fin *</span>
              <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="w-full rounded-2xl border border-slate-200 px-4 py-3 font-semibold text-slate-800 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100" />
            </label>
          </div>
          <label className="block space-y-2">
            <span className="block text-xs font-black uppercase tracking-wider text-slate-500">Motif</span>
            <input value={reason} onChange={(event) => setReason(event.target.value)} maxLength={255} placeholder="Ex. Congés annuels" className="w-full rounded-2xl border border-slate-200 px-4 py-3 font-semibold text-slate-800 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100" />
          </label>
          {error && <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}
          <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
            <button type="button" onClick={onClose} disabled={saving} className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-40">Annuler</button>
            <button type="submit" disabled={saving} className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white hover:bg-black disabled:opacity-60">{saving ? 'Ajout…' : 'Ajouter'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const AgendaTab: React.FC = () => {
  const [settings, setSettings] = useState<AgendaSettings | null>(null);
  const [exceptions, setExceptions] = useState<AgendaException[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [readError, setReadError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [showExceptionModal, setShowExceptionModal] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setReadError(null);
    try {
      const [settingsResponse, exceptionsResponse] = await Promise.all([
        api.get('/agenda/settings'),
        api.get('/agenda/exceptions'),
      ]);
      setSettings(normalizeSettings(settingsResponse.data));
      setExceptions(exceptionsResponse.data);
      setDirty(false);
    } catch (err) {
      console.error(err);
      setReadError("Impossible de charger les horaires et fermetures réels du cabinet. Aucune configuration ne peut être modifiée tant que la lecture n'a pas réussi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSettings();
  }, [fetchSettings]);

  const updateDay = (dayKey: WeekdayKey, patch: Partial<DaySchedule>) => {
    setSettings((previous) => previous ? {
      ...previous,
      weekly_schedule: {
        ...previous.weekly_schedule,
        [dayKey]: { ...previous.weekly_schedule[dayKey], ...patch },
      },
    } : previous);
    setDirty(true);
    setFormError(null);
  };

  const handleSave = async () => {
    if (!settings || readError) return;
    const validationError = validateWeek(settings.weekly_schedule);
    if (validationError) {
      setFormError(validationError);
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const response = await api.put('/agenda/settings', settings);
      setSettings(normalizeSettings(response.data));
      setDirty(false);
      toast.success('Horaires sauvegardés');
    } catch (err) {
      console.error(err);
      setFormError("Impossible d'enregistrer ces horaires.");
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const deleteException = async (id: number) => {
    setDeletingId(id);
    try {
      await api.delete(`/agenda/exceptions/${id}`);
      setExceptions((current) => current.filter((item) => item.id !== id));
      setConfirmDeleteId(null);
      toast.success('Fermeture retirée');
    } catch (err) {
      console.error(err);
      toast.error('Impossible de retirer cette fermeture');
    } finally {
      setDeletingId(null);
    }
  };

  const openDays = useMemo(() => settings ? WEEKDAYS.filter(({ key }) => settings.weekly_schedule[key].is_open).length : 0, [settings]);

  if (loading) return <div className="p-8 text-center text-slate-500">Chargement...</div>;
  if (readError) return <SettingsReadError title="Horaires indisponibles" message={readError} onRetry={fetchSettings} />;
  if (!settings) return null;

  const timeInputClass = 'min-w-0 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-bold text-slate-700 outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100';

  return (
    <div className="min-w-0 space-y-7 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="flex items-center gap-3 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl"><CalendarDays className="shrink-0 text-primary" size={30} />Horaires & Agenda</h2>
          <p className="mt-2 max-w-2xl text-sm font-medium text-slate-500">Définissez les heures réellement utilisées par l'agenda et les fermetures du cabinet.</p>
        </div>
        {dirty && <span className="w-fit rounded-full bg-amber-50 px-3 py-1.5 text-[11px] font-black uppercase tracking-wide text-amber-700">Modifications non enregistrées</span>}
      </div>

      <section className="min-w-0 rounded-[2rem] border border-slate-100 bg-white p-5 shadow-sm sm:p-7">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="flex items-center gap-3 text-xl font-black text-slate-900"><Clock3 className="text-blue-500" />Semaine d'ouverture</h3>
            <p className="mt-1 text-sm font-medium text-slate-500">{openDays} jour{openDays > 1 ? 's' : ''} ouvert{openDays > 1 ? 's' : ''} sur 7.</p>
          </div>
          <p className="text-xs font-semibold text-slate-400">Chaque jour peut avoir sa propre amplitude.</p>
        </div>

        <div className="space-y-3">
          {WEEKDAYS.map(({ key, label, short }) => {
            const day = settings.weekly_schedule[key];
            return (
              <article key={key} className={cn('rounded-2xl border p-4 transition-colors sm:p-5', day.is_open ? 'border-slate-200 bg-white' : 'border-slate-100 bg-slate-50/80')}>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className={cn('flex h-10 w-10 items-center justify-center rounded-xl text-xs font-black uppercase', day.is_open ? 'bg-blue-50 text-blue-700' : 'bg-slate-200 text-slate-500')}>{short}</span>
                    <div>
                      <p className={cn('font-black', day.is_open ? 'text-slate-800' : 'text-slate-500')}>{label}</p>
                      <p className="text-xs font-medium text-slate-400">{day.is_open ? (day.is_continuous ? 'Journée continue' : 'Avec pause') : 'Cabinet fermé'}</p>
                    </div>
                  </div>
                  <label className="flex cursor-pointer items-center gap-2 text-sm font-bold text-slate-600">
                    <span className="hidden sm:inline">{day.is_open ? 'Ouvert' : 'Fermé'}</span>
                    <input type="checkbox" checked={day.is_open} onChange={(event) => updateDay(key, { is_open: event.target.checked })} className="h-5 w-5 accent-slate-900" aria-label={`${label} ouvert`} />
                  </label>
                </div>

                {day.is_open && (
                  <div className="mt-4 grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] xl:items-end">
                    <div className="min-w-0">
                      <p className="mb-2 text-[10px] font-black uppercase tracking-wider text-slate-400">{day.is_continuous ? 'Ouverture' : 'Matin'}</p>
                      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
                        <input type="time" value={day.morning_start} onChange={(event) => updateDay(key, { morning_start: event.target.value })} className={timeInputClass} aria-label={`${label} ouverture matin`} />
                        <span className="text-center text-xs font-black text-slate-400">→</span>
                        <input type="time" value={day.morning_end} onChange={(event) => updateDay(key, { morning_end: event.target.value })} className={timeInputClass} aria-label={`${label} fermeture matin`} />
                      </div>
                    </div>

                    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5 text-xs font-bold text-slate-600 xl:mb-0">
                      <span>Journée continue</span>
                      <input type="checkbox" checked={day.is_continuous} onChange={(event) => updateDay(key, { is_continuous: event.target.checked })} className="h-4 w-4 accent-slate-900" aria-label={`${label} journée continue`} />
                    </label>

                    {!day.is_continuous && (
                      <div className="min-w-0">
                        <p className="mb-2 text-[10px] font-black uppercase tracking-wider text-slate-400">Après-midi</p>
                        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
                          <input type="time" value={day.afternoon_start} onChange={(event) => updateDay(key, { afternoon_start: event.target.value })} className={timeInputClass} aria-label={`${label} ouverture après-midi`} />
                          <span className="text-center text-xs font-black text-slate-400">→</span>
                          <input type="time" value={day.afternoon_end} onChange={(event) => updateDay(key, { afternoon_end: event.target.value })} className={timeInputClass} aria-label={`${label} fermeture après-midi`} />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <section className="min-w-0 rounded-[2rem] border border-slate-100 bg-white p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 className="flex items-center gap-3 text-xl font-black text-slate-900"><Calendar className="text-violet-500" />Fermetures & exceptions</h3>
            <p className="mt-1 text-sm font-medium text-slate-500">Congés, fermeture ponctuelle ou indisponibilité du cabinet.</p>
          </div>
          <button type="button" onClick={() => setShowExceptionModal(true)} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-violet-50 px-4 py-2.5 text-sm font-black text-violet-700 hover:bg-violet-100 sm:w-auto">
            <Plus size={16} /> Ajouter une fermeture
          </button>
        </div>

        {exceptions.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/60 p-8 text-center">
            <p className="font-bold text-slate-600">Aucune fermeture enregistrée</p>
            <p className="mt-1 text-sm text-slate-400">L'agenda suit actuellement uniquement votre semaine d'ouverture.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {exceptions.map((exception) => (
              <article key={exception.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="font-black text-slate-800">{exception.reason || 'Fermeture du cabinet'}</p>
                  <p className="mt-1 text-sm font-medium text-slate-500">
                    {formatDate(exception.start_date)}{exception.start_date.slice(0, 10) !== exception.end_date.slice(0, 10) ? ` → ${formatDate(exception.end_date)}` : ''}
                  </p>
                </div>
                {confirmDeleteId === exception.id ? (
                  <div className="flex shrink-0 gap-2">
                    <button type="button" onClick={() => setConfirmDeleteId(null)} disabled={deletingId === exception.id} className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600">Annuler</button>
                    <button type="button" onClick={() => void deleteException(exception.id)} disabled={deletingId === exception.id} className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3 py-2 text-xs font-black text-white disabled:opacity-50">
                      <Trash2 size={14} /> {deletingId === exception.id ? 'Retrait…' : 'Confirmer'}
                    </button>
                  </div>
                ) : (
                  <button type="button" onClick={() => setConfirmDeleteId(exception.id)} className="shrink-0 rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-500 hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700">Retirer</button>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      {formError && <p role="alert" className="rounded-2xl bg-rose-50 px-5 py-4 text-sm font-bold text-rose-700">{formError}</p>}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
        {!dirty && <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700"><Check size={15} />Horaires enregistrés</span>}
        <button type="button" onClick={() => void handleSave()} disabled={saving || !dirty} className="w-full rounded-2xl bg-primary px-8 py-4 font-black text-white shadow-xl shadow-primary/20 transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto">
          {saving ? 'Sauvegarde…' : 'Enregistrer les horaires'}
        </button>
      </div>

      {showExceptionModal && (
        <ExceptionModal
          onClose={() => setShowExceptionModal(false)}
          onCreated={(exception) => setExceptions((current) => [...current, exception].sort((a, b) => a.start_date.localeCompare(b.start_date)))}
        />
      )}
    </div>
  );
};
