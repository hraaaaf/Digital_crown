import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Users } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import { AgendaModal } from './AgendaModal';
import type { Appointment } from './DailyView';
import {
  getDayBounds,
  getDaySchedule,
  isDateOpen,
  isTimeWithinSchedule,
  timeToMinutes,
  type AgendaExceptionLike,
  type AgendaSettingsLike,
} from './agendaSchedule';

const HOUR_HEIGHT = 80;
const SLOT_MINUTES = 15;
const SLOTS_PER_HOUR = 60 / SLOT_MINUTES;
const TIME_AXIS_WIDTH = 68;
const LANE_MIN_WIDTH = 220;

type MultiAppointment = Appointment & { praticien_id?: number | null };

type PractitionerInterval = { start: string; end: string };
type PractitionerException = { id: number; start_date: string; end_date: string; reason?: string | null };
type PractitionerAvailability = {
  date: string;
  inherits_cabinet: boolean;
  config_error?: boolean;
  intervals: PractitionerInterval[];
  exceptions: PractitionerException[];
};

type PractitionerLane = {
  dentist_id: number;
  dentist_name: string;
  appointments: MultiAppointment[];
  availability?: PractitionerAvailability;
};

type MultiPractitionerData = {
  error?: string;
  dentists?: PractitionerLane[];
  legacy_unassigned?: MultiAppointment[];
  total_appointments?: number;
};

interface MultiPractitionerTimelineViewProps {
  data: MultiPractitionerData | null;
  loading: boolean;
  selectedDate: Date;
  agendaSettings?: AgendaSettingsLike | null;
  exceptions?: AgendaExceptionLike[] | null;
  onSaved: () => void;
}

type SlotState = 'AVAILABLE' | 'GLOBAL_CLOSED' | 'PRACTITIONER_HOURS' | 'PAUSE' | 'LEAVE';

type SlotAvailability = {
  available: boolean;
  state: SlotState;
  label: string;
};

const STATUS_COLORS: Record<string, string> = {
  PRÉVU: 'bg-blue-100 text-blue-700 border-blue-200',
  EN_S_ATTENTE: 'bg-amber-100 text-amber-700 border-amber-200',
  EN_FAUTEUIL: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  TERMINÉ: 'bg-slate-100 text-slate-400 border-slate-200 opacity-70',
  ANNULÉ: 'bg-rose-50 text-rose-400 border-rose-200 line-through opacity-70',
  EN_ATTENTE_DEMANDE: 'bg-orange-100 text-orange-700 border-orange-200',
  EN_ATTENTE_CONFIRM: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  CONFIRMÉ: 'bg-blue-100 text-blue-700 border-blue-200',
  REFUSÉ: 'bg-red-100 text-red-500 border-red-200 line-through opacity-70',
  EXPIRÉ: 'bg-gray-100 text-gray-400 border-gray-200 opacity-60',
  ABSENT: 'bg-rose-100 text-rose-600 border-rose-200',
};

const SLOT_STATE_CLASSES: Record<SlotState, string> = {
  AVAILABLE: 'cursor-crosshair bg-white hover:bg-indigo-50',
  GLOBAL_CLOSED: 'cursor-not-allowed bg-slate-200/80',
  PRACTITIONER_HOURS: 'cursor-not-allowed bg-slate-50',
  PAUSE: 'cursor-not-allowed bg-amber-50/90',
  LEAVE: 'cursor-not-allowed bg-rose-50/90',
};

const isExact = (appointment: MultiAppointment) =>
  !appointment.scheduling_type || appointment.scheduling_type === 'EXACT_TIME';

const isSameLocalDay = (value: string, selectedDate: Date) => {
  const date = new Date(value);
  return date.getFullYear() === selectedDate.getFullYear()
    && date.getMonth() === selectedDate.getMonth()
    && date.getDate() === selectedDate.getDate();
};

const formatClock = (date: Date) =>
  date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

const schedulingLabel = (appointment: MultiAppointment) => {
  if (appointment.scheduling_type === 'MORNING') return 'Matin';
  if (appointment.scheduling_type === 'AFTERNOON') return 'Après-midi';
  if (appointment.scheduling_type === 'FULL_DAY') return 'Toute la journée';
  return 'Flexible';
};

const addPractitionerToPayload = (payload: unknown, practitionerId: number) => {
  if (!payload) return { praticien_id: practitionerId };
  if (typeof payload === 'string') {
    try {
      const parsed = JSON.parse(payload);
      return JSON.stringify({ ...parsed, praticien_id: parsed.praticien_id ?? practitionerId });
    } catch {
      return payload;
    }
  }
  if (typeof payload === 'object' && !Array.isArray(payload)) {
    const objectPayload = payload as Record<string, unknown>;
    return { ...objectPayload, praticien_id: objectPayload.praticien_id ?? practitionerId };
  }
  return payload;
};

const slotDate = (selectedDate: Date, time: string) => {
  const [hours, minutes] = time.split(':').map(Number);
  const value = new Date(selectedDate);
  value.setHours(hours, minutes, 0, 0);
  return value;
};

const getPractitionerSlotAvailability = (
  dentist: PractitionerLane,
  selectedDate: Date,
  time: string,
  globalAvailable: boolean,
): SlotAvailability => {
  if (!globalAvailable) {
    return { available: false, state: 'GLOBAL_CLOSED', label: 'Cabinet fermé ou hors horaires du cabinet' };
  }

  const availability = dentist.availability;
  if (!availability || availability.inherits_cabinet) {
    return { available: true, state: 'AVAILABLE', label: 'Disponible' };
  }
  if (availability.config_error) {
    return { available: false, state: 'PRACTITIONER_HOURS', label: 'Configuration praticien invalide' };
  }

  const start = slotDate(selectedDate, time);
  const end = new Date(start.getTime() + SLOT_MINUTES * 60_000);
  const exception = (availability.exceptions || []).find((item) => {
    const exceptionStart = new Date(item.start_date);
    const exceptionEnd = new Date(item.end_date);
    return start < exceptionEnd && end > exceptionStart;
  });
  if (exception) {
    return {
      available: false,
      state: 'LEAVE',
      label: exception.reason ? `Absence : ${exception.reason}` : 'Absence du praticien',
    };
  }

  const startMinutes = timeToMinutes(time);
  const endMinutes = startMinutes + SLOT_MINUTES;
  const intervals = [...(availability.intervals || [])]
    .filter((interval) => /^\d{2}:\d{2}$/.test(interval.start) && /^\d{2}:\d{2}$/.test(interval.end))
    .sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));

  if (intervals.some((interval) => startMinutes >= timeToMinutes(interval.start) && endMinutes <= timeToMinutes(interval.end))) {
    return { available: true, state: 'AVAILABLE', label: 'Disponible' };
  }
  if (intervals.length === 0) {
    return { available: false, state: 'PRACTITIONER_HOURS', label: 'Praticien absent ce jour' };
  }

  const firstStart = timeToMinutes(intervals[0].start);
  const lastEnd = timeToMinutes(intervals[intervals.length - 1].end);
  if (startMinutes >= firstStart && endMinutes <= lastEnd) {
    return { available: false, state: 'PAUSE', label: 'Pause du praticien' };
  }
  return { available: false, state: 'PRACTITIONER_HOURS', label: 'Hors horaires du praticien' };
};

export const MultiPractitionerTimelineView: React.FC<MultiPractitionerTimelineViewProps> = ({
  data,
  loading,
  selectedDate,
  agendaSettings,
  exceptions,
  onSaved,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [initialTime, setInitialTime] = useState('09:00');
  const [editingAppointment, setEditingAppointment] = useState<MultiAppointment | null>(null);
  const [modalPractitioner, setModalPractitioner] = useState<{ id?: number; name: string } | null>(null);
  const createInterceptorId = useRef<number | null>(null);

  const dentists = useMemo(() => data?.dentists || [], [data]);
  const legacy = useMemo(
    () => (data?.legacy_unassigned || []).filter((appointment) => isSameLocalDay(appointment.datetime_start, selectedDate)),
    [data, selectedDate],
  );
  const daySchedule = getDaySchedule(selectedDate, agendaSettings);
  const dayOpen = isDateOpen(selectedDate, agendaSettings, exceptions);

  const appointmentsForDay = useMemo(
    () => dentists.flatMap((dentist) =>
      (dentist.appointments || [])
        .filter((appointment) => isSameLocalDay(appointment.datetime_start, selectedDate))
        .map((appointment) => ({ appointment, dentist })),
    ),
    [dentists, selectedDate],
  );

  const exactEntries = useMemo(
    () => appointmentsForDay.filter(({ appointment }) => isExact(appointment)),
    [appointmentsForDay],
  );
  const exactLegacy = useMemo(() => legacy.filter(isExact), [legacy]);
  const flexibleLegacy = useMemo(() => legacy.filter((appointment) => !isExact(appointment)), [legacy]);
  const hasFlexible = appointmentsForDay.some(({ appointment }) => !isExact(appointment)) || flexibleLegacy.length > 0;

  const timelineBounds = useMemo(() => {
    const base = getDayBounds(daySchedule);
    let startHour = base.startHour;
    let endHour = base.endHour;
    const exactAppointments = [
      ...exactEntries.map(({ appointment }) => appointment),
      ...exactLegacy,
    ];

    for (const appointment of exactAppointments) {
      const start = new Date(appointment.datetime_start);
      const startMinutes = start.getHours() * 60 + start.getMinutes();
      const endMinutes = startMinutes + Math.max(1, appointment.duration_minutes || 0);
      startHour = Math.min(startHour, Math.floor(startMinutes / 60));
      endHour = Math.max(endHour, Math.ceil(endMinutes / 60));
    }

    startHour = Math.max(0, startHour);
    endHour = Math.min(24, Math.max(startHour + 1, endHour));
    return { startHour, endHour };
  }, [daySchedule, exactEntries, exactLegacy]);

  const totalHours = timelineBounds.endHour - timelineBounds.startHour;
  const totalSlots = totalHours * SLOTS_PER_HOUR;
  const timelineHeight = totalHours * HOUR_HEIGHT;
  const gridMinWidth = TIME_AXIS_WIDTH + Math.max(1, dentists.length) * LANE_MIN_WIDTH;

  const clearCreateInterceptor = () => {
    if (createInterceptorId.current === null) return;
    api.interceptors.request.eject(createInterceptorId.current);
    createInterceptorId.current = null;
  };

  const installCreateInterceptor = (practitionerId: number) => {
    clearCreateInterceptor();
    createInterceptorId.current = api.interceptors.request.use((config) => {
      const method = (config.method || 'get').toLowerCase();
      const url = (config.url || '').split('?')[0];

      if (method === 'get' && url === '/appointments/check-conflicts') {
        config.params = {
          ...(config.params || {}),
          praticien_id: config.params?.praticien_id ?? practitionerId,
        };
      }

      if (method === 'post' && url === '/appointments/') {
        config.data = addPractitionerToPayload(config.data, practitionerId);
      }

      return config;
    });
  };

  useEffect(() => () => {
    if (createInterceptorId.current !== null) {
      api.interceptors.request.eject(createInterceptorId.current);
      createInterceptorId.current = null;
    }
  }, []);

  const openCreate = (dentist: PractitionerLane, time: string) => {
    installCreateInterceptor(dentist.dentist_id);
    setEditingAppointment(null);
    setInitialTime(time);
    setModalPractitioner({ id: dentist.dentist_id, name: dentist.dentist_name });
    setIsModalOpen(true);
  };

  const openEdit = (appointment: MultiAppointment, practitioner?: PractitionerLane) => {
    clearCreateInterceptor();
    setEditingAppointment(appointment);
    setModalPractitioner(practitioner
      ? { id: practitioner.dentist_id, name: practitioner.dentist_name }
      : { name: 'Non assigné (historique)' });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    clearCreateInterceptor();
    setIsModalOpen(false);
    setEditingAppointment(null);
    setModalPractitioner(null);
  };

  if (loading) {
    return <div className="py-20 text-center text-slate-400 font-bold animate-pulse">Chargement…</div>;
  }
  if (!data) return null;
  if (data.error === 'PREMIUM') {
    return (
      <div className="py-20 flex flex-col items-center gap-4">
        <div className="w-16 h-16 bg-indigo-50 rounded-3xl flex items-center justify-center">
          <Users size={32} className="text-indigo-400" />
        </div>
        <h3 className="text-xl font-black text-slate-700">Vue multi-praticien</h3>
        <p className="text-slate-400 font-medium text-center max-w-sm">
          Cette vue est disponible à partir du plan <strong>PREMIUM</strong> (2 dentistes et plus).
        </p>
      </div>
    );
  }
  if (dentists.length === 0) {
    return (
      <div className="rounded-[2rem] border border-slate-200 bg-white p-10 text-center text-sm font-bold text-slate-400">
        Aucun praticien assignable actif pour cette vue.
      </div>
    );
  }

  const gridColumns = `${TIME_AXIS_WIDTH}px repeat(${dentists.length}, minmax(${LANE_MIN_WIDTH}px, 1fr))`;

  return (
    <div className="bg-white/70 backdrop-blur-2xl border border-white rounded-[2rem] sm:rounded-[2.5rem] shadow-2xl overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-3 sm:px-5">
        <div className="flex flex-wrap items-center gap-3 text-[10px] font-black uppercase tracking-wider text-slate-500">
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded border border-slate-300 bg-white" /> Libre</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded border border-slate-300 bg-slate-200" /> Cabinet fermé</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded border border-slate-200 bg-slate-50" /> Hors horaires praticien</span>
          <span className="inline-flex items-center gap-1.5 text-amber-700"><span className="h-2.5 w-2.5 rounded border border-amber-200 bg-amber-50" /> Pause</span>
          <span className="inline-flex items-center gap-1.5 text-rose-700"><span className="h-2.5 w-2.5 rounded border border-rose-200 bg-rose-50" /> Absence</span>
          <span className="inline-flex items-center gap-1.5 text-orange-700"><span className="h-2.5 w-2.5 rounded border border-orange-400 bg-orange-50" /> RDV non assigné</span>
        </div>
        <span className="text-[10px] font-bold text-slate-400">Créneaux de 15 min · défilement horizontal sur petit écran</span>
      </div>

      {flexibleLegacy.length > 0 && (
        <div className="flex items-start gap-2 border-b border-orange-200 bg-orange-50 px-4 py-3 text-xs font-bold text-orange-800">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-black">Rendez-vous flexibles non assignés</p>
            <p className="mt-0.5 font-medium text-orange-700">
              {flexibleLegacy.map((appointment) => `${schedulingLabel(appointment)} · ${appointment.patient_name || 'Patient'}`).join(' · ')}
            </p>
          </div>
        </div>
      )}

      <div data-testid="multi-practitioner-scroll" className="max-h-[680px] overflow-auto overscroll-contain">
        <div style={{ minWidth: `${gridMinWidth}px` }}>
          <div
            className="sticky top-0 z-40 grid border-b border-slate-200 bg-slate-50/95 backdrop-blur-xl"
            style={{ gridTemplateColumns: gridColumns }}
          >
            <div className="sticky left-0 z-50 flex items-center justify-center border-r border-slate-200 bg-slate-50 px-2 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
              Heure
            </div>
            {dentists.map((dentist) => {
              const count = (dentist.appointments || []).filter((appointment) => isSameLocalDay(appointment.datetime_start, selectedDate)).length;
              return (
                <div key={dentist.dentist_id} className="min-w-0 border-r border-slate-100 px-3 py-3 text-center last:border-r-0">
                  <p className="truncate text-sm font-black text-slate-800">{dentist.dentist_name}</p>
                  <p className="mt-0.5 text-[9px] font-bold text-slate-400">{count} RDV aujourd'hui · {dentist.availability?.inherits_cabinet === false ? 'horaires perso' : 'horaires cabinet'}</p>
                </div>
              );
            })}
          </div>

          {hasFlexible && (
            <div className="grid border-b border-slate-200 bg-slate-50/50" style={{ gridTemplateColumns: gridColumns }}>
              <div className="sticky left-0 z-30 flex items-center justify-center border-r border-slate-200 bg-slate-50 px-2 py-2 text-[9px] font-black uppercase tracking-wider text-slate-400">
                Flexible
              </div>
              {dentists.map((dentist) => {
                const flexible = (dentist.appointments || []).filter(
                  (appointment) => isSameLocalDay(appointment.datetime_start, selectedDate) && !isExact(appointment),
                );
                return (
                  <div key={dentist.dentist_id} className="min-h-12 border-r border-slate-100 p-1.5 last:border-r-0">
                    <div className="flex flex-wrap gap-1">
                      {flexible.map((appointment) => (
                        <button
                          key={appointment.id}
                          type="button"
                          onClick={() => openEdit(appointment, dentist)}
                          className={cn(
                            'rounded-lg border px-2 py-1 text-left text-[9px] font-bold',
                            STATUS_COLORS[appointment.status] || 'bg-slate-50 text-slate-600 border-slate-200',
                          )}
                        >
                          {schedulingLabel(appointment)} · {appointment.patient_name || 'Patient'}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="grid" style={{ gridTemplateColumns: `${TIME_AXIS_WIDTH}px 1fr` }}>
            <div className="sticky left-0 z-30 border-r border-slate-200 bg-slate-50" style={{ height: `${timelineHeight}px` }}>
              {Array.from({ length: totalHours }).map((_, index) => (
                <div key={index} className="relative h-20 border-b border-slate-200">
                  <span className="absolute left-2 top-1 text-[10px] font-black text-slate-500">
                    {String(timelineBounds.startHour + index).padStart(2, '0')}:00
                  </span>
                </div>
              ))}
            </div>

            <div className="relative" style={{ height: `${timelineHeight}px` }}>
              <div className="grid h-full" style={{ gridTemplateColumns: `repeat(${dentists.length}, minmax(${LANE_MIN_WIDTH}px, 1fr))` }}>
                {dentists.map((dentist) => {
                  const exactAppointments = (dentist.appointments || []).filter(
                    (appointment) => isSameLocalDay(appointment.datetime_start, selectedDate) && isExact(appointment),
                  );
                  return (
                    <div key={dentist.dentist_id} className="relative border-r border-slate-100 last:border-r-0">
                      <div className="absolute inset-0 flex flex-col">
                        {Array.from({ length: totalSlots }).map((_, slotIndex) => {
                          const totalMinutes = timelineBounds.startHour * 60 + slotIndex * SLOT_MINUTES;
                          const hours = Math.floor(totalMinutes / 60);
                          const minutes = totalMinutes % 60;
                          const time = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                          const globalAvailable = dayOpen && isTimeWithinSchedule(time, daySchedule);
                          const slot = getPractitionerSlotAvailability(dentist, selectedDate, time, globalAvailable);
                          return (
                            <button
                              key={slotIndex}
                              type="button"
                              disabled={!slot.available}
                              aria-label={slot.available
                                ? `Créer un rendez-vous avec ${dentist.dentist_name} à ${time}`
                                : `${dentist.dentist_name} indisponible à ${time} : ${slot.label}`}
                              title={slot.available ? undefined : slot.label}
                              onClick={() => openCreate(dentist, time)}
                              className={cn(
                                'h-5 shrink-0 border-b border-slate-100/80 transition-colors',
                                slotIndex % SLOTS_PER_HOUR === SLOTS_PER_HOUR - 1 && 'border-b-slate-200',
                                SLOT_STATE_CLASSES[slot.state],
                              )}
                            />
                          );
                        })}
                      </div>

                      {exactAppointments.map((appointment) => {
                        const start = new Date(appointment.datetime_start);
                        const startMinutes = start.getHours() * 60 + start.getMinutes();
                        const top = ((startMinutes - timelineBounds.startHour * 60) / 60) * HOUR_HEIGHT;
                        const height = Math.max(18, (appointment.duration_minutes / 60) * HOUR_HEIGHT - 2);
                        return (
                          <button
                            key={appointment.id}
                            type="button"
                            onClick={() => openEdit(appointment, dentist)}
                            className={cn(
                              'absolute left-1 right-1 z-20 overflow-hidden rounded-lg border px-2 py-1 text-left text-[10px] font-bold shadow-sm transition-transform hover:scale-[1.01]',
                              STATUS_COLORS[appointment.status] || 'bg-slate-50 text-slate-600 border-slate-200',
                            )}
                            style={{ top: `${top}px`, height: `${height}px` }}
                          >
                            <span className="block truncate font-black">{formatClock(start)} · {appointment.patient_name || 'Patient'}</span>
                            {height >= 34 && (
                              <span className="block truncate text-[9px] opacity-70">
                                {appointment.motif || 'Rendez-vous'} · {appointment.duration_minutes} min
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>

              {exactLegacy.map((appointment) => {
                const start = new Date(appointment.datetime_start);
                const startMinutes = start.getHours() * 60 + start.getMinutes();
                const top = ((startMinutes - timelineBounds.startHour * 60) / 60) * HOUR_HEIGHT;
                const height = Math.max(20, (appointment.duration_minutes / 60) * HOUR_HEIGHT - 2);
                return (
                  <button
                    key={appointment.id}
                    type="button"
                    onClick={() => openEdit(appointment)}
                    className="absolute left-0 right-0 z-30 overflow-hidden border-y-2 border-orange-400 bg-orange-50/95 px-3 text-left text-[10px] font-black text-orange-800 shadow-sm"
                    style={{ top: `${top}px`, height: `${height}px` }}
                    aria-label={`Rendez-vous non assigné à ${formatClock(start)}, bloque tous les praticiens`}
                  >
                    <span className="sticky left-2 inline-flex h-full items-center whitespace-nowrap">
                      Non assigné · {formatClock(start)} · {appointment.patient_name || 'Patient'} · bloque tous les praticiens
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {isModalOpen && modalPractitioner && (
        <div className="pointer-events-none fixed left-1/2 top-24 z-[130] -translate-x-1/2 rounded-full bg-indigo-700 px-4 py-2 text-xs font-black text-white shadow-xl">
          Praticien : {modalPractitioner.name}
        </div>
      )}

      <AgendaModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSaved={() => {
          onSaved();
          closeModal();
        }}
        selectedDate={selectedDate}
        initialTime={initialTime}
        editingAppointment={editingAppointment}
      />
    </div>
  );
};