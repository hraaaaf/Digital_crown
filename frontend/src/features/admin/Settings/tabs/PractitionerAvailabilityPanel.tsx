import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { CalendarClock, Plus, RotateCcw, Save, Trash2, UserRound } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../../../services/api';
import { cn } from '../../../../utils/cn';

type WeekdayKey = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
type CabinetDay = {
  is_open: boolean;
  is_continuous: boolean;
  morning_start: string;
  morning_end: string;
  afternoon_start: string;
  afternoon_end: string;
};
type CabinetWeek = Record<WeekdayKey, CabinetDay>;
type Interval = { start: string; end: string };
type PractitionerWeek = Record<WeekdayKey, { intervals: Interval[] }>;
type PractitionerSummary = { practitioner_id: number; practitioner_name: string; inherits_cabinet: boolean };
type PractitionerSettings = PractitionerSummary & { weekly_schedule: PractitionerWeek | null; updated_at?: string | null };
type PractitionerException = {
  id: number;
  practitioner_id: number;
  start_date: string;
  end_date: string;
  reason: string;
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

const cabinetToPractitionerWeek = (cabinet: CabinetWeek): PractitionerWeek => Object.fromEntries(
  WEEKDAYS.map(({ key }) => {
    const day = cabinet[key];
    if (!day?.is_open) return [key, { intervals: [] }];
    const intervals = day.is_continuous
      ? [{ start: day.morning_start, end: day.morning_end }]
      : [
        { start: day.morning_start, end: day.morning_end },
        { start: day.afternoon_start, end: day.afternoon_end },
      ];
    return [key, { intervals }];
  }),
) as PractitionerWeek;

const cloneWeek = (week: PractitionerWeek): PractitionerWeek => JSON.parse(JSON.stringify(week));

const formatDateTime = (value: string) => new Intl.DateTimeFormat('fr-FR', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
}).format(new Date(value));

export const PractitionerAvailabilityPanel: React.FC<{ cabinetSchedule: CabinetWeek }> = ({ cabinetSchedule }) => {
  const [practitioners, setPractitioners] = useState<PractitionerSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [settings, setSettings] = useState<PractitionerSettings | null>(null);
  const [draft, setDraft] = useState<PractitionerWeek | null>(null);
  const [exceptions, setExceptions] = useState<PractitionerException[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [absenceStart, setAbsenceStart] = useState('');
  const [absenceEnd, setAbsenceEnd] = useState('');
  const [absenceReason, setAbsenceReason] = useState('');

  const loadPractitioners = useCallback(async () => {
    const response = await api.get('/agenda/practitioners');
    const rows = response.data as PractitionerSummary[];
    setPractitioners(rows);
    setSelectedId((current) => current ?? rows[0]?.practitioner_id ?? null);
  }, []);

  useEffect(() => {
    setLoading(true);
    loadPractitioners()
      .catch((error) => {
        console.error(error);
        setFormError('Impossible de charger les praticiens.');
      })
      .finally(() => setLoading(false));
  }, [loadPractitioners]);

  const loadSelected = useCallback(async (id: number) => {
    setLoading(true);
    setFormError(null);
    try {
      const [settingsResponse, exceptionsResponse] = await Promise.all([
        api.get(`/agenda/practitioners/${id}/settings`),
        api.get(`/agenda/practitioners/${id}/exceptions`),
      ]);
      const loaded = settingsResponse.data as PractitionerSettings;
      setSettings(loaded);
      setDraft(loaded.weekly_schedule ? cloneWeek(loaded.weekly_schedule) : null);
      setExceptions(exceptionsResponse.data as PractitionerException[]);
    } catch (error) {
      console.error(error);
      setFormError('Impossible de charger les disponibilités de ce praticien.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId !== null) void loadSelected(selectedId);
  }, [selectedId, loadSelected]);

  const selected = useMemo(
    () => practitioners.find((item) => item.practitioner_id === selectedId) || null,
    [practitioners, selectedId],
  );

  const beginCustom = () => {
    setDraft(cabinetToPractitionerWeek(cabinetSchedule));
    setFormError(null);
  };

  const updateInterval = (day: WeekdayKey, index: number, field: keyof Interval, value: string) => {
    setDraft((current) => {
      if (!current) return current;
      const next = cloneWeek(current);
      next[day].intervals[index][field] = value;
      return next;
    });
  };

  const addInterval = (day: WeekdayKey) => {
    setDraft((current) => {
      if (!current) return current;
      const next = cloneWeek(current);
      const last = next[day].intervals.at(-1);
      next[day].intervals.push(last ? { start: last.end, end: '18:00' } : { start: '09:00', end: '13:00' });
      return next;
    });
  };

  const removeInterval = (day: WeekdayKey, index: number) => {
    setDraft((current) => {
      if (!current) return current;
      const next = cloneWeek(current);
      next[day].intervals.splice(index, 1);
      return next;
    });
  };

  const saveSchedule = async () => {
    if (!selectedId || !draft) return;
    setSaving(true);
    setFormError(null);
    try {
      const response = await api.put(`/agenda/practitioners/${selectedId}/settings`, { weekly_schedule: draft });
      setSettings(response.data);
      setDraft(cloneWeek(response.data.weekly_schedule));
      setPractitioners((rows) => rows.map((row) => row.practitioner_id === selectedId ? { ...row, inherits_cabinet: false } : row));
      toast.success('Disponibilités praticien enregistrées');
    } catch (error: any) {
      console.error(error);
      setFormError(error?.response?.data?.detail || 'Impossible d’enregistrer ces disponibilités.');
    } finally {
      setSaving(false);
    }
  };

  const resetInheritance = async () => {
    if (!selectedId) return;
    setSaving(true);
    try {
      await api.delete(`/agenda/practitioners/${selectedId}/settings`);
      setSettings((current) => current ? { ...current, inherits_cabinet: true, weekly_schedule: null } : current);
      setDraft(null);
      setPractitioners((rows) => rows.map((row) => row.practitioner_id === selectedId ? { ...row, inherits_cabinet: true } : row));
      toast.success('Héritage des horaires cabinet rétabli');
    } catch (error) {
      console.error(error);
      setFormError('Impossible de rétablir l’héritage cabinet.');
    } finally {
      setSaving(false);
    }
  };

  const addAbsence = async () => {
    if (!selectedId || !absenceStart || !absenceEnd) return;
    setSaving(true);
    setFormError(null);
    try {
      const response = await api.post(`/agenda/practitioners/${selectedId}/exceptions`, {
        start_date: absenceStart,
        end_date: absenceEnd,
        reason: absenceReason.trim() || 'Indisponibilité praticien',
      });
      setExceptions((current) => [...current, response.data].sort((a, b) => a.start_date.localeCompare(b.start_date)));
      setAbsenceStart('');
      setAbsenceEnd('');
      setAbsenceReason('');
      toast.success('Indisponibilité ajoutée');
    } catch (error: any) {
      console.error(error);
      setFormError(error?.response?.data?.detail || 'Impossible d’ajouter cette indisponibilité.');
    } finally {
      setSaving(false);
    }
  };

  const deleteAbsence = async (id: number) => {
    if (!selectedId) return;
    try {
      await api.delete(`/agenda/practitioners/${selectedId}/exceptions/${id}`);
      setExceptions((current) => current.filter((item) => item.id !== id));
      toast.success('Indisponibilité retirée');
    } catch (error) {
      console.error(error);
      toast.error('Impossible de retirer cette indisponibilité');
    }
  };

  return (
    <section className="min-w-0 rounded-[2rem] border border-slate-100 bg-white p-5 shadow-sm sm:p-7" data-testid="practitioner-availability-panel">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="flex items-center gap-3 text-xl font-black text-slate-900"><CalendarClock className="text-indigo-500" />Disponibilités par praticien</h3>
          <p className="mt-1 max-w-2xl text-sm font-medium text-slate-500">Les horaires individuels ne peuvent jamais ouvrir le cabinet : disponibilité effective = cabinet ∩ praticien.</p>
        </div>
        {selected && (
          <span className={cn('w-fit rounded-full px-3 py-1.5 text-[10px] font-black uppercase tracking-wide', settings?.inherits_cabinet !== false ? 'bg-emerald-50 text-emerald-700' : 'bg-indigo-50 text-indigo-700')}>
            {settings?.inherits_cabinet !== false ? 'Hérite du cabinet' : 'Horaires personnalisés'}
          </span>
        )}
      </div>

      {practitioners.length === 0 && !loading ? (
        <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-7 text-center text-sm font-bold text-slate-500">Aucun praticien assignable actif.</div>
      ) : (
        <div className="space-y-5">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {practitioners.map((practitioner) => (
              <button key={practitioner.practitioner_id} type="button" onClick={() => setSelectedId(practitioner.practitioner_id)} className={cn('inline-flex shrink-0 items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-black', selectedId === practitioner.practitioner_id ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50')}>
                <UserRound size={15} /> {practitioner.practitioner_name}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="py-8 text-center text-sm font-bold text-slate-400">Chargement…</div>
          ) : selected && (
            <>
              {!draft ? (
                <div className="flex flex-col gap-4 rounded-2xl border border-emerald-100 bg-emerald-50/60 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-black text-slate-800">{selected.practitioner_name} suit les horaires du cabinet.</p>
                    <p className="mt-1 text-sm font-medium text-slate-500">Aucune configuration individuelle : compatibilité totale avec les cabinets existants.</p>
                  </div>
                  <button type="button" onClick={beginCustom} className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-black text-white">Personnaliser</button>
                </div>
              ) : (
                <div className="space-y-3">
                  {WEEKDAYS.map(({ key, label, short }) => (
                    <article key={key} className="rounded-2xl border border-slate-200 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-[11px] font-black uppercase text-indigo-700">{short}</span>
                          <div><p className="font-black text-slate-800">{label}</p><p className="text-xs font-medium text-slate-400">{draft[key].intervals.length ? `${draft[key].intervals.length} plage${draft[key].intervals.length > 1 ? 's' : ''}` : 'Jour off'}</p></div>
                        </div>
                        <button type="button" onClick={() => addInterval(key)} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-50 px-3 py-2 text-xs font-black text-indigo-700"><Plus size={14} />Plage</button>
                      </div>
                      {draft[key].intervals.length > 0 && (
                        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                          {draft[key].intervals.map((interval, index) => (
                            <div key={`${key}-${index}`} className="grid grid-cols-[1fr_auto_1fr_auto] items-center gap-2 rounded-xl bg-slate-50 p-2">
                              <input type="time" value={interval.start} onChange={(event) => updateInterval(key, index, 'start', event.target.value)} className="min-w-0 rounded-lg border border-slate-200 bg-white px-2 py-2 text-xs font-bold" aria-label={`${label} plage ${index + 1} début`} />
                              <span className="text-xs font-black text-slate-400">→</span>
                              <input type="time" value={interval.end} onChange={(event) => updateInterval(key, index, 'end', event.target.value)} className="min-w-0 rounded-lg border border-slate-200 bg-white px-2 py-2 text-xs font-bold" aria-label={`${label} plage ${index + 1} fin`} />
                              <button type="button" onClick={() => removeInterval(key, index)} aria-label={`Retirer plage ${label} ${index + 1}`} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 size={14} /></button>
                            </div>
                          ))}
                        </div>
                      )}
                    </article>
                  ))}
                  <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                    <button type="button" onClick={() => void resetInheritance()} disabled={saving} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-black text-slate-600 disabled:opacity-40"><RotateCcw size={15} />Hériter du cabinet</button>
                    <button type="button" onClick={() => void saveSchedule()} disabled={saving} className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-700 px-4 py-2.5 text-sm font-black text-white disabled:opacity-40"><Save size={15} />{saving ? 'Sauvegarde…' : 'Enregistrer'}</button>
                  </div>
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 p-4 sm:p-5">
                <div className="mb-4"><p className="font-black text-slate-800">Congés & indisponibilités</p><p className="mt-1 text-xs font-medium text-slate-400">Une absence bloque uniquement ce praticien. Les fermetures cabinet restent prioritaires.</p></div>
                <div className="grid gap-2 lg:grid-cols-[1fr_1fr_1.2fr_auto]">
                  <input type="datetime-local" value={absenceStart} onChange={(event) => setAbsenceStart(event.target.value)} className="min-w-0 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold" aria-label="Début indisponibilité praticien" />
                  <input type="datetime-local" value={absenceEnd} onChange={(event) => setAbsenceEnd(event.target.value)} className="min-w-0 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold" aria-label="Fin indisponibilité praticien" />
                  <input value={absenceReason} onChange={(event) => setAbsenceReason(event.target.value)} placeholder="Motif, ex. Congé" className="min-w-0 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold" />
                  <button type="button" onClick={() => void addAbsence()} disabled={saving || !absenceStart || !absenceEnd} className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-black text-white disabled:opacity-40"><Plus size={15} />Ajouter</button>
                </div>
                <div className="mt-4 space-y-2">
                  {exceptions.length === 0 ? <p className="rounded-xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-400">Aucune indisponibilité individuelle.</p> : exceptions.map((item) => (
                    <div key={item.id} className="flex flex-col gap-2 rounded-xl bg-rose-50/70 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                      <div><p className="text-sm font-black text-slate-800">{item.reason}</p><p className="mt-0.5 text-xs font-semibold text-slate-500">{formatDateTime(item.start_date)} → {formatDateTime(item.end_date)}</p></div>
                      <button type="button" onClick={() => void deleteAbsence(item.id)} className="inline-flex items-center gap-1.5 self-start rounded-lg px-3 py-2 text-xs font-black text-rose-700 hover:bg-rose-100 sm:self-auto"><Trash2 size={13} />Retirer</button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {formError && <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{formError}</p>}
    </section>
  );
};
