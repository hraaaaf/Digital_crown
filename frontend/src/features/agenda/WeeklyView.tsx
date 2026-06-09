import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { RefreshCw, Plus } from 'lucide-react';
import { cn } from '../../utils/cn';
import { AgendaModal } from './AgendaModal';
import type { Appointment, AppointmentStatus } from './DailyView';

interface WeeklyViewProps {
  selectedDate: Date;
}

export const WeeklyView: React.FC<WeeklyViewProps> = ({ selectedDate }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState<Date | null>(null);
  const [initialTime, setInitialTime] = useState('09:00');
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  
  // Configuration de la grille
  const startHour = 8;
  const endHour = 19;
  const totalHours = endHour - startHour;

  const handleGridClick = (e: React.MouseEvent, date: Date) => {
    if ((e.target as HTMLElement).closest('.appointment-item')) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hourHeight = 80; // h-20 in tailwind is 5rem=80px
    const slotIndex = Math.floor(y / (hourHeight / 4)); // 15 min slots
    
    const hours = startHour + Math.floor(slotIndex / 4);
    const minutes = (slotIndex % 4) * 15;
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    
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

      <div className="bg-white/60 backdrop-blur-2xl border border-white rounded-[2.5rem] shadow-2xl overflow-hidden">
        <div className="grid grid-cols-8 border-b border-slate-100 bg-slate-50/50">
          <div className="p-4 border-r border-slate-100"></div>
          {weekDays.map((date, i) => (
            <div key={i} className={cn(
              "p-4 text-center border-r border-slate-100 last:border-0",
              date.toDateString() === new Date().toDateString() ? "bg-blue-50/50" : ""
            )}>
              <span className="block text-[10px] font-black text-slate-400 uppercase tracking-widest">{date.toLocaleDateString('fr-FR', { weekday: 'short' })}</span>
              <span className={cn(
                "inline-flex items-center justify-center w-8 h-8 mt-1 text-sm font-black rounded-lg",
                date.toDateString() === new Date().toDateString() ? "bg-[#003380] text-white" : "text-slate-700"
              )}>
                {date.getDate()}
              </span>
            </div>
          ))}
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
                className="relative border-r border-slate-100 last:border-0 grow cursor-crosshair hover:bg-slate-50/30 transition-colors"
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
                        "appointment-item absolute left-1 right-1 p-2 rounded-lg border border-l-2 text-[10px] font-bold shadow-sm cursor-pointer z-10 break-words hover:scale-[1.02] transition-transform",
                        getStatusColor(appt.status)
                      )}
                      style={{ top: `${top}px`, height: `${height - 2}px` }}
                    >
                      {appt.patient_name || 'Patient'}
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
