import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { RefreshCw, Plus } from 'lucide-react';
import { cn } from '../../utils/cn';
import { AgendaModal } from './AgendaModal';
import { clinicCalendarDay, clinicAppointmentFormFields } from './agendaClinicLocalDate';
import type { Appointment } from './DailyView';
import { PatientAvatar } from '../patients/components/PatientAvatar';

interface MonthlyViewProps {
  selectedDate: Date;
}

export const MonthlyView: React.FC<MonthlyViewProps> = ({ selectedDate }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState<Date | null>(null);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);

  const handleDayClick = (day: Date) => {
    setEditingAppointment(null);
    // A calendar day is a *local* clinic date, not a UTC midnight instant.
    // Preserve the selected civil day for the modal in every browser timezone.
    const localCalendarDate = new Date(day);
    localCalendarDate.setHours(12, 0, 0, 0);
    setModalDate(localCalendarDate);
    setIsModalOpen(true);
  };

  const handleAppointmentClick = (event: React.MouseEvent, appointment: Appointment) => {
    event.stopPropagation();
    setEditingAppointment(appointment);
    setModalDate(new Date(appointment.datetime_start));
    setIsModalOpen(true);
  };

  // Calculer les jours du mois
  const getMonthDays = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDayOfMonth = new Date(year, month, 1);

    // Debut de la grille (lundi de la semaine du 1er)
    const startOffset = (firstDayOfMonth.getDay() + 6) % 7;
    const startDate = new Date(firstDayOfMonth);
    startDate.setDate(firstDayOfMonth.getDate() - startOffset);

    return Array.from({ length: 42 }).map((_, i) => {
      const d = new Date(startDate);
      d.setDate(startDate.getDate() + i);
      return d;
    });
  };

  const days = getMonthDays(selectedDate);
  // The seven-column calendar is useful on desktop but too narrow to show
  // patient names at 390px. A mobile-only chronological list uses exactly
  // the same fetched appointments, dates and existing edit flow.
  const monthDaysWithAppointments = days.filter(day =>
    day.getMonth() === selectedDate.getMonth() &&
    appointments.some(a => clinicAppointmentFormFields(a.datetime_start).date === clinicCalendarDay(day))
  );
  const chosenDate = [
    selectedDate.getFullYear(),
    String(selectedDate.getMonth()+1).padStart(2,'0'),
    String(selectedDate.getDate()).padStart(2,'0')
  ].join('-');

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const firstDay = clinicCalendarDay(days[0]);
      const lastDay = clinicCalendarDay(days[41]);

      const res = await api.get('/appointments/', {
        params: {
          start_date: `${firstDay}T00:00:00`,
          end_date: `${lastDay}T23:59:59.999999`
        }
      });
      setAppointments(res.data);
    } catch (e) {
      console.error("Erreur mensuelle:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  return (
    <div data-testid="agenda-month-view" className="w-full space-y-6">
      <div className="flex justify-end gap-3 px-2">
        <button aria-label="Actualiser le mois" onClick={fetchAppointments} className="p-3 bg-white/50 border border-white hover:bg-white text-slate-500 rounded-2xl transition-all shadow-sm">
          <RefreshCw size={18} className={cn(loading && "animate-spin text-blue-500")} />
        </button>
        <button onClick={() => { setEditingAppointment(null); setModalDate(selectedDate); setIsModalOpen(true); }} className="px-6 py-3 bg-[#003380] text-white font-bold rounded-2xl shadow-xl shadow-blue-900/10 hover:bg-blue-900 transition-all flex items-center gap-2">
          <Plus size={18} /> Nouveau RV
        </button>
      </div>

      <div data-p2-mobile-month-list className="sm:hidden space-y-3">
        <h2 className="px-1 text-base font-bold text-text-main">Rendez-vous du mois</h2>
        {/* The desktop grid allows picking any date (including an empty day)
            to create a visit. Keep that exact operation accessible on mobile. */}
        <div className="p2-agenda-surface flex flex-wrap items-center gap-2 rounded-xl border border-border-main bg-card p-3">
          <label htmlFor="p2-month-choose-day" className="flex-1 text-sm font-semibold text-text-main">Créer un RDV à une date</label>
          <input id="p2-month-choose-day" data-p2-month-date-picker type="date"
            value={chosenDate}
            onChange={e=>{
              if(!e.target.value)return;
              const date=new Date(e.target.value+'T12:00:00');
              if(!Number.isNaN(date.getTime()))handleDayClick(date);
            }}
            className="min-h-11 max-w-full rounded-lg border border-border-main bg-card px-2 text-sm font-semibold text-text-main focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            aria-label="Choisir un jour pour créer un rendez-vous"
          />
        </div>
        {loading && appointments.length === 0 && <p role="status" className="p-4 text-text-muted">Chargement des rendez-vous…</p>}
        {!loading && monthDaysWithAppointments.length === 0 && (
          <p className="p-4 rounded-xl border border-border-main bg-card text-text-muted">Aucun rendez-vous pour ce mois.</p>
        )}
        {monthDaysWithAppointments.map(day => {
          const dayAppointments=appointments
            .filter(a=>clinicAppointmentFormFields(a.datetime_start).date === clinicCalendarDay(day))
            .sort((a,b)=>a.datetime_start.localeCompare(b.datetime_start)||a.id-b.id);
          return (
            <section key={day.toISOString()} data-p2-month-day className="p2-agenda-surface rounded-2xl border border-border-main bg-card p-3 shadow-sm">
              <h3 className="mb-2 px-1 text-sm font-bold text-text-main capitalize">
                {day.toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long'})}
                <span className="ml-2 text-xs font-semibold text-text-muted">{dayAppointments.length} RDV</span>
              </h3>
              <div className="space-y-2">
                {dayAppointments.map(a=>{
                  const when=clinicAppointmentFormFields(a.datetime_start).time;
                  const timeLabel=a.scheduling_type==='FULL_DAY'?'Journée'
                    :a.scheduling_type==='MORNING'?'Matin'
                    :a.scheduling_type==='AFTERNOON'?'Après-midi':when;
                  return (
                    <button key={a.id} type="button" data-m4d-month-appointment data-p2-month-appointment
                      onClick={e=>handleAppointmentClick(e,a)}
                      aria-label={`Modifier le rendez-vous de ${a.patient_name || 'patient'} à ${timeLabel}`}
                      className="flex min-h-12 w-full items-center gap-3 rounded-xl border border-border-main bg-card p-3 text-left text-text-main shadow-sm hover:border-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                      <span className="w-14 shrink-0 text-sm font-bold text-text-main">{timeLabel}</span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-semibold">{a.patient_name || 'Patient'}</span>
                        {a.motif && <span className="block truncate text-xs text-text-muted">{a.motif}</span>}
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
      <div data-p2-month-grid className="p2-agenda-surface hidden sm:block bg-white/60 backdrop-blur-2xl border border-white rounded-[2.5rem] shadow-2xl overflow-hidden min-h-[700px]">
        <div className="grid grid-cols-7 border-b border-slate-100 bg-slate-50/50">
          {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map(d => (
            <div key={d} className="p-4 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest border-r border-slate-100 last:border-0">{d}</div>
          ))}
        </div>

        <div className="grid grid-cols-7 grid-rows-6 flex-1">
          {days.map((day, i) => {
            const isToday = day.toDateString() === new Date().toDateString();
            const isCurrentMonth = day.getMonth() === selectedDate.getMonth();
            const dayAppts = appointments.filter(a => clinicAppointmentFormFields(a.datetime_start).date === clinicCalendarDay(day));

            return (
              <div
                key={i}
                onClick={() => handleDayClick(day)}
                className={cn(
                  "min-h-[120px] p-2 border-r border-b border-slate-100/60 last:border-r-0 transition-all cursor-pointer",
                  !isCurrentMonth ? "bg-slate-50/30 opacity-40 shadow-inner" : "hover:bg-blue-50/40 hover:shadow-md",
                  isToday ? "bg-blue-50/40" : ""
                )}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className={cn(
                    "inline-flex items-center justify-center w-7 h-7 text-xs font-black rounded-lg",
                    isToday ? "bg-[#003380] text-white" : "text-slate-600"
                  )}>
                    {day.getDate()}
                  </span>
                  {dayAppts.length > 0 && <span className="text-[10px] font-bold text-blue-500 bg-blue-100 px-1.5 py-0.5 rounded-md">{dayAppts.length} RDV</span>}
                </div>

                <div className="space-y-1 overflow-hidden">
                  {dayAppts.slice(0, 3).map(a => {
                    let timeLabel = clinicAppointmentFormFields(a.datetime_start).time;
                    if (a.scheduling_type === 'FULL_DAY') timeLabel = 'JOUR';
                    if (a.scheduling_type === 'MORNING') timeLabel = 'MATIN';
                    if (a.scheduling_type === 'AFTERNOON') timeLabel = 'APREM';
                    return (
                      <button
                        key={a.id}
                        type="button"
                        data-m4d-month-appointment
                        onClick={(event) => handleAppointmentClick(event, a)}
                        className="w-full min-h-11 text-left text-[9px] font-bold bg-white border border-slate-100 px-2 py-1 rounded-md text-slate-700 truncate shadow-sm hover:border-blue-300 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400/40"
                        aria-label={`Modifier le rendez-vous de ${a.patient_name || 'patient'} à ${timeLabel}`}
                      >
                        <span className="flex min-w-0 items-center gap-1.5">
                          {a.patient_id ? (
                            <PatientAvatar patientId={a.patient_id} fullName={a.patient_name} resolveFromDirectory className="w-6 h-6 rounded-md text-[8px]" />
                          ) : null}
                          <span className="truncate">{timeLabel} - {a.patient_name}</span>
                        </span>
                      </button>
                    );
                  })}
                  {dayAppts.length > 3 && <div className="text-[9px] font-bold text-slate-400 pl-1">+{dayAppts.length - 3} autres...</div>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <AgendaModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingAppointment(null); }}
        onSaved={fetchAppointments}
        selectedDate={modalDate || selectedDate}
        editingAppointment={editingAppointment}
      />
    </div>
  );
};
