import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Users } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';
import '../../styles/agendaA3Theme.css';
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
          <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded border border-indigo-300 bg-indigo-50" /> RDV non assigné</span>
        </div>
        <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">
          {selectedDate.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' })}
        </div>
      </div>

      {hasFlexible && (
        <div className="border-b border-slate-100 bg-slate-50/60 px-4 py-3 sm:px-5">
          <div className="mb-2 text-[10px] font-black uppercase tracking-wider text-slate-400">Rendez-vous flexibles</div>
          <div className="flex flex-wrap gap-2">
            {appointmentsForDay
              .filter(({ appointment }) => !isExact(appointment))
              .map(({ appointment, dentist }) => (
                <button
                  key={`flex-${appointment.id}`}
                  type="button"
                  onClick={() => openEdit(appointment, dentist)}
                  className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs font-bold text-slate-700 hover:border-indigo-300"
                >
                  {schedulingLabel(appointment)} · {appointment.patient_name || 'Patient'} · {dentist.dentist_name}
                </button>
              ))}
            {flexibleLegacy.map((appointment) => (
              <button
                key={`legacy-flex-${appointment.id}`}
                type="button"
                onClick={() => openEdit(appointment)}
                className="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-left text-xs font-bold text-indigo-700"
              >
                {schedulingLabel(appointment)} · {appointment.patient_name || 'Patient'} · Non assigné
              </button>
            ))}
          </div>
        </div>
      )}

      <div data-testid="multi-practitioner-scroll" className="overflow-x-auto overscroll-x-contain">
        <div style={{ minWidth: gridMinWidth }}>
          <div
            className="sticky top-0 z-30 grid border-b border-slate-200 bg-white/95 backdrop-blur-xl"
            style={{ gridTemplateColumns: gridColumns }}
          >
            <div className="border-r border-slate-200 px-2 py-3 text-center text-[9px] font-black uppercase tracking-wider text-slate-400">
              Heure
            </div>
            {dentists.map((dentist) => (
              <div key={dentist.dentist_id} className="border-r border-slate-100 px-3 py-3 text-center last:border-r-0">
                <div className="truncate text-xs font-black text-slate-800">{dentist.dentist_name}</div>
                <div className={cn(
                  'mt-0.5 text-[9px] font-bold uppercase tracking-wide',
                  dentist.availability?.inherits_cabinet !== false ? 'text-emerald-600' : 'text-indigo-500',
                )}>
                  {dentist.availability?.inherits_cabinet !== false ? 'Horaires cabinet' : 'Horaires personnalisés'}
                </div>
              </div>
            ))}
          </div>

          <div className="relative grid" style={{ gridTemplateColumns: gridColumns, height: timelineHeight }}>
            <div className="relative border-r border-slate-200 bg-slate-50/80">
              {Array.from({ length: totalHours + 1 }, (_, index) => {
                const hour = timelineBounds.startHour + index;
                return (
                  <div
                    key={hour}
                    className="absolute right-2 -translate-y-1/2 text-[10px] font-black text-slate-400"
                    style={{ top: index * HOUR_HEIGHT }}
                  >
                    {String(hour).padStart(2, '0')}:00
                  </div>
                );
              })}
            </div>

            {dentists.map((dentist) => (
              <div key={dentist.dentist_id} className="relative border-r border-slate-100 last:border-r-0">
                <div className="absolute inset-0 grid" style={{ gridTemplateRows: `repeat(${totalSlots}, ${HOUR_HEIGHT / SLOTS_PER_HOUR}px)` }}>
                  {Array.from({ length: totalSlots }, (_, slotIndex) => {
                    const minutes = timelineBounds.startHour * 60 + slotIndex * SLOT_MINUTES;
                    const hour = Math.floor(minutes / 60);
                    const minute = minutes % 60;
                    const time = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
                    const globalAvailable = dayOpen && isTimeWithinSchedule(time, daySchedule);
                    const availability = getPractitionerSlotAvailability(dentist, selectedDate, time, globalAvailable);
                    return (
                      <button
                        key={`${dentist.dentist_id}-${time}`}
                        type="button"
                        disabled={!availability.available}
                        onClick={() => openCreate(dentist, time)}
                        className={cn(
                          'border-b border-slate-100/90 transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-400',
                          SLOT_STATE_CLASSES[availability.state],
                        )}
                        title={availability.label}
                        aria-label={availability.available
                          ? `Créer un rendez-vous avec ${dentist.dentist_name} à ${time}`
                          : `${dentist.dentist_name} indisponible à ${time} : ${availability.label}`}
                      />
                    );
                  })}
                </div>

                {(dentist.appointments || [])
                  .filter((appointment) => isExact(appointment) && isSameLocalDay(appointment.datetime_start, selectedDate))
                  .map((appointment) => {
                    const start = new Date(appointment.datetime_start);
                    const startMinutes = start.getHours() * 60 + start.getMinutes();
                    const offsetMinutes = startMinutes - timelineBounds.startHour * 60;
                    const duration = Math.max(15, appointment.duration_minutes || 30);
                    const top = (offsetMinutes / 60) * HOUR_HEIGHT;
                    const height = Math.max(22, (duration / 60) * HOUR_HEIGHT);
                    return (
                      <button
                        key={appointment.id}
                        type="button"
                        onClick={() => openEdit(appointment, dentist)}
                        className={cn(
                          'absolute left-1.5 right-1.5 z-20 overflow-hidden rounded-xl border px-2 py-1 text-left shadow-sm transition hover:z-30 hover:shadow-md',
                          STATUS_COLORS[appointment.status] || 'bg-white text-slate-700 border-slate-200',
                        )}
                        style={{ top, height }}
                      >
                        <div className="truncate text-[10px] font-black">{formatClock(start)} · {appointment.patient_name || 'Patient'}</div>
                        <div className="truncate text-[9px] font-bold opacity-75">{appointment.duration_minutes || 0} min</div>
                      </button>
                    );
                  })}
              </div>
            ))}

            {exactLegacy.map((appointment) => {
              const start = new Date(appointment.datetime_start);
              const startMinutes = start.getHours() * 60 + start.getMinutes();
              const top = ((startMinutes - timelineBounds.startHour * 60) / 60) * HOUR_HEIGHT;
              const duration = Math.max(15, appointment.duration_minutes || 30);
              const height = Math.max(22, (duration / 60) * HOUR_HEIGHT);
              return (
                <button
                  key={`legacy-${appointment.id}`}
                  type="button"
                  onClick={() => openEdit(appointment)}
                  className="absolute z-40 overflow-hidden rounded-xl border-2 border-dashed border-indigo-400 bg-indigo-50/95 px-3 py-1 text-left text-indigo-800 shadow-sm"
                  style={{
                    top,
                    height,
                    left: TIME_AXIS_WIDTH + 6,
                    right: 6,
                  }}
                >
                  <div className="flex items-center gap-1 truncate text-[10px] font-black">
                    <AlertTriangle size={11} /> Non assigné · {formatClock(start)} · {appointment.patient_name || 'Patient'}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <AgendaModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSaved={() => {
          closeModal();
          onSaved();
        }}
        initialDate={selectedDate}
        initialTime={initialTime}
        appointment={editingAppointment}
        selectedPractitioner={modalPractitioner}
      />
    </div>
  );
};
