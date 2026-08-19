import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { RefreshCw, Plus, Bell, BellOff } from 'lucide-react';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';
import { AgendaModal } from './AgendaModal';
import type { Appointment, AppointmentStatus } from './DailyView';
import { formatScheduleSummary, getDaySchedule, getExceptionForDate, getWeekBounds, isDateOpen, isTimeWithinSchedule, type AgendaExceptionLike, type AgendaSettingsLike } from './agendaSchedule';

interface WeeklyViewProps {
  selectedDate: Date;
  agendaSettings?: AgendaSettingsLike | null;
  exceptions?: AgendaExceptionLike[] | null;
}

export const WeeklyView: React.FC<WeeklyViewProps> = ({ selectedDate, agendaSettings, exceptions }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState<Date | null>(null);
  const [initialTime, setInitialTime] = useState('09:00');
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [sendingReminder, setSendingReminder] = useState<number | null>(null);

  const handleRemind = async (e: React.MouseEvent, apptId: number) => {
    e.stopPropagation();
    setSendingReminder(apptId);
    try {
      await api.post(`/appointments/${apptId}/remind`);
      toast.success('Rappel envoyé !');
      setAppointments(prev => prev.map(a => a.id === apptId ? { ...a, reminder_sent: true } : a));
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Erreur d\'envoi du rappel');
    } finally {
      setSendingReminder(null);
    }
  };

  const handleGridClick = (e: React.MouseEvent, date: Date) => {
    if (!isDateOpen(date, agendaSettings, exceptions)) return;
    if ((e.target as HTMLElement).closest('.appointment-item')) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hourHeight = 80; // h-20 in tailwind is 5rem=80px
    const slotIndex = Math.floor(y / (hourHeight / 4)); // 15 min slots
    
    const hours = startHour + Math.floor(slotIndex / 4);
    const minutes = (slotIndex % 4) * 15;
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    if (!isTimeWithinSchedule(timeString, getDaySchedule(date, agendaSettings))) return;
    
    setModalDate(date);
    setInitialTime(timeString);
    setIsModalOpen(true);
  };

  // Calculer les dates de la semaine commencant par lundi
  const getWeekDays = (date: Date) => {
    const startOfWeek = new Date(date);
    const day = startOfWeek.getDay();
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // lundi
    startOfWeek.setDate(diff);
    
    return Array.from({ length: 7 }).map((_, i) => {
      const d = new Date(startOfWeek);
      d.setDate(startOfWeek.getDate() + i);
      return d;
    });
  };

  const weekDays = getWeekDays(selectedDate);
  const { startHour, endHour } = getWeekBounds(weekDays, agendaSettings, exceptions);
  const totalHours = endHour - startHour;

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const start = new Date(weekDays[0]);
      start.setHours(0, 0, 0, 0);
      const end = new Date(weekDays[6]);
      end.setHours(23, 59, 59, 999);

      const res = await api.get('/appointments/', {
        params: {
          start_date: start.toISOString(),
          end_date: end.toISOString()
        }
      });
      setAppointments(res.data);
    } catch (e) {
      console.error("Erreur hebdo:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  const getStatusColor = (status: AppointmentStatus) => {
    switch(status) {
      case 'PRÉVU': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'EN_S_ATTENTE': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'EN_FAUTEUIL': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'TERMINÉ': return 'bg-slate-50 text-slate-400 border-slate-200 opacity-60';
      case 'ANNULÉ': return 'bg-rose-50 text-rose-400 border-rose-200 line-through opacity-70';
      case 'EN_ATTENTE_DEMANDE': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'EN_ATTENTE_CONFIRM': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'CONFIRMÉ': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'REFUSÉ': return 'bg-red-100 text-red-500 border-red-200 line-through opacity-70';
      case 'EXPIRÉ': return 'bg-gray-100 text-gray-400 border-gray-200 opacity-50';
      case 'ABSENT': return 'bg-rose-100 text-rose-600 border-rose-200';
      default: return 'bg-blue-50 text-blue-600';
    }
  };

  return (
    <div className="w-full space-y-6">
      
      {/* QUICK ACTIONS BAR */}
      <div className="flex justify-end gap-3 px-2">
        <button onClick={fetchAppointments} className="p-3 bg-white/50 border border-white hover:bg-white text-slate-500 rounded-2xl transition-all shadow-sm">
          <RefreshCw size={18} className={cn(loading && "animate-spin text-blue-500")} />
        </button>
        <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-[#003380] text-white font-bold rounded-2xl shadow-xl shadow-blue-900/10 hover:bg-blue-900 transition-all flex items-center gap-2">
          <Plus size={18} /> Nouveau RV
        </button>
      </div>

      <div className="md:hidden space-y-3">
        {weekDays.map((date) => {
          const schedule = getDaySchedule(date, agendaSettings);
          const exception = getExceptionForDate(date, exceptions);
          const open = isDateOpen(date, agendaSettings, exceptions);
          const dayAppointments = appointments
            .filter((appt) => new Date(appt.datetime_start).toDateString() === date.toDateString())
            .sort((a, b) => new Date(a.datetime_start).getTime() - new Date(b.datetime_start).getTime());
          return (
            <div key={date.toISOString()} className={cn("rounded-2xl border p-4 shadow-sm", open ? "bg-white border-slate-100" : "bg-slate-100/80 border-slate-200")}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-widest text-slate-400">{date.toLocaleDateString('fr-FR', { weekday: 'long' })}</p>
                  <p className="font-black text-slate-800 mt-1">{date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long' })}</p>
                  <p className="text-xs font-bold text-slate-500 mt-1">{exception ? exception.reason || 'Fermeture exceptionnelle' : formatScheduleSummary(schedule)}</p>
                </div>
                <span className={cn("text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full", open ? "bg-emerald-50 text-emerald-700" : "bg-slate-200 text-slate-600")}>{open ? 'Ouvert' : 'Fermé'}</span>
              </div>
              <div className="mt-3 space-y-2">
                {dayAppointments.length === 0 ? (
                  <p className="text-sm font-medium text-slate-400 py-2">Aucun rendez-vous</p>
                ) : dayAppointments.map((appt) => (
                  <button
                    key={appt.id}
                    type="button"
                    onClick={() => { setEditingAppointment(appt); setModalDate(date); setIsModalOpen(true); }}
                    className={cn("w-full text-left rounded-xl border px-3 py-2", getStatusColor(appt.status))}
                  >
                    <span className="font-black text-sm">{appt.patient_name || 'Patient'}</span>
                    <span className="block text-xs font-bold opacity-75 mt-0.5">
                      {appt.scheduling_type && appt.scheduling_type !== 'EXACT_TIME'
                        ? appt.scheduling_type === 'MORNING' ? 'Matin' : appt.scheduling_type === 'AFTERNOON' ? 'Après-midi' : 'Toute la journée'
                        : new Date(appt.datetime_start).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                      {appt.motif ? ` · ${appt.motif}` : ''}
                    </span>
                  </button>
                ))}
              </div>
              {open && (
                <button
                  type="button"
                  onClick={() => { setModalDate(date); setInitialTime(schedule.morning_start); setEditingAppointment(null); setIsModalOpen(true); }}
                  className="mt-3 w-full rounded-xl border border-primary/20 bg-primary/5 text-primary font-black text-sm py-2.5"
                >
                  + Ajouter un rendez-vous
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="hidden md:block bg-white/60 backdrop-blur-2xl border border-white rounded-[2.5rem] shadow-2xl overflow-hidden">
        <div className="grid grid-cols-8 border-b border-slate-100 bg-slate-50/50">
          <div className="p-4 border-r border-slate-100"></div>
          {weekDays.map((date, i) => {
            const open = isDateOpen(date, agendaSettings, exceptions);
            const exception = getExceptionForDate(date, exceptions);
            return (
              <div key={i} className={cn(
                "p-3 text-center border-r border-slate-100 last:border-0 min-w-0",
                !open ? "bg-slate-100/80" : date.toDateString() === new Date().toDateString() ? "bg-blue-50/50" : ""
              )}>
                <span className="block text-[10px] font-black text-slate-400 uppercase tracking-widest">{date.toLocaleDateString('fr-FR', { weekday: 'short' })}</span>
                <span className={cn(
                  "inline-flex items-center justify-center w-8 h-8 mt-1 text-sm font-black rounded-lg",
                  date.toDateString() === new Date().toDateString() ? "bg-[#003380] text-white" : "text-slate-700"
                )}>{date.getDate()}</span>
                {!open && <span className="block mt-1 text-[8px] font-black uppercase tracking-wider text-slate-500 truncate" title={exception?.reason || 'Fermé'}>{exception?.reason || 'Fermé'}</span>}
              </div>
            );
          })}
        </div>

        {/* SECTION FLEXIBLE / ALL DAY */}
        <div className="grid grid-cols-8 border-b border-slate-200 bg-slate-50/30">
          <div className="p-2 border-r border-slate-100 flex items-center justify-center">
             <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest text-center">Flexible</span>
          </div>
          {weekDays.map((date, dayIdx) => {
            const flexAppts = appointments.filter(a => 
              new Date(a.datetime_start).toDateString() === date.toDateString() && 
              a.scheduling_type && a.scheduling_type !== 'EXACT_TIME'
            );
            return (
              <div key={dayIdx} className="border-r border-slate-100 last:border-0 p-1 min-h-[40px] flex flex-col gap-1">
                {flexAppts.map(appt => (
                  <div
                    key={appt.id}
                    onClick={(e) => { e.stopPropagation(); setEditingAppointment(appt); setIsModalOpen(true); }}
                    className={cn(
                      "appointment-item p-1 rounded border-l-2 text-[9px] font-bold shadow-sm cursor-pointer break-words hover:scale-[1.02]",
                      getStatusColor(appt.status)
                    )}
                  >
                    <span className="opacity-75 uppercase tracking-tighter text-[8px] block mb-0.5">
                      {appt.scheduling_type === 'FULL_DAY' ? 'JOUR.' : appt.scheduling_type === 'MORNING' ? 'MATIN' : 'APREM'}
                    </span>
                    {appt.patient_name || 'Patient'}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        <div className="overflow-y-auto relative" style={{ height: '600px' }}>
          <div className="grid grid-cols-8">
            {/* Heures */}
            <div className="flex flex-col">
              {Array.from({ length: totalHours }).map((_, i) => (
                <div key={i} className="h-20 border-b border-slate-100 text-center relative">
                  <span className="absolute -top-2 left-0 w-full text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                    {startHour + i}:00
                  </span>
                </div>
              ))}
            </div>

            {/* Colonnes des jours */}
            {weekDays.map((date, dayIdx) => (
              <div 
                key={dayIdx} 
                className={cn("relative border-r border-slate-100 last:border-0 grow transition-colors", isDateOpen(date, agendaSettings, exceptions) ? "cursor-crosshair hover:bg-slate-50/30" : "cursor-not-allowed bg-slate-100/60")}
                onClick={(e) => handleGridClick(e, date)}
              >
                {Array.from({ length: totalHours }).map((_, i) => (
                  <div key={i} className="h-20 border-b border-slate-100/50"></div>
                ))}
                
                {/* Rendu des rendez-vous exacts pour ce jour */}
                {appointments.filter(appt => 
                  new Date(appt.datetime_start).toDateString() === date.toDateString() &&
                  (!appt.scheduling_type || appt.scheduling_type === 'EXACT_TIME')
                ).map(appt => {
                  const d = new Date(appt.datetime_start);
                  const h = d.getHours();
                  const m = d.getMinutes();
                  const top = (h - startHour) * 80 + (m / 60) * 80;
                  const height = (appt.duration_minutes / 60) * 80;

                  return (
                    <div
                      key={appt.id}
                      onClick={(e) => { e.stopPropagation(); setEditingAppointment(appt); setIsModalOpen(true); }}
                      className={cn(
                        "appointment-item absolute left-1 right-1 p-2 rounded-lg border border-l-2 text-[10px] font-bold shadow-sm cursor-pointer z-10 break-words hover:scale-[1.02] transition-transform group/card",
                        getStatusColor(appt.status)
                      )}
                      style={{ top: `${top}px`, height: `${height - 2}px` }}
                    >
                      <div className="truncate">{appt.patient_name || 'Patient'}</div>
                      {height > 40 && (
                        <button
                          onClick={(e) => handleRemind(e, appt.id)}
                          disabled={sendingReminder === appt.id}
                          className={cn(
                            "absolute bottom-1 right-1 p-0.5 rounded opacity-0 group-hover/card:opacity-100 transition-opacity",
                            appt.reminder_sent ? "text-emerald-600" : "text-slate-400 hover:text-blue-600"
                          )}
                          title={appt.reminder_sent ? "Rappel déjà envoyé" : "Envoyer rappel SMS"}
                        >
                          {appt.reminder_sent ? <Bell size={10} /> : <BellOff size={10} />}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      <AgendaModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingAppointment(null); }}
        onSaved={fetchAppointments}
        selectedDate={modalDate || selectedDate}
        initialTime={initialTime}
        editingAppointment={editingAppointment}
      />
    </div>
  );
};
