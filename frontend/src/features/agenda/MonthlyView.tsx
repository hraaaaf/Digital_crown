import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { RefreshCw, Plus } from 'lucide-react';
import { cn } from '../../utils/cn';
import { AgendaModal } from './AgendaModal';
import type { Appointment } from './DailyView';

interface MonthlyViewProps {
  selectedDate: Date;
}

export const MonthlyView: React.FC<MonthlyViewProps> = ({ selectedDate }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalDate, setModalDate] = useState<Date | null>(null);

  const handleDayClick = (day: Date) => {
    setModalDate(day);
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

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const start = new Date(days[0]);
      start.setHours(0, 0, 0, 0);
      const end = new Date(days[41]);
      end.setHours(23, 59, 59, 999);

      const res = await api.get('/appointments/', {
        params: {
          start_date: start.toISOString(),
          end_date: end.toISOString()
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
  }, [selectedDate]);

  return (
    <div className="w-full space-y-6">
      <div className="flex justify-end gap-3 px-2">
        <button onClick={fetchAppointments} className="p-3 bg-white/50 border border-white hover:bg-white text-slate-500 rounded-2xl transition-all shadow-sm">
          <RefreshCw size={18} className={cn(loading && "animate-spin text-blue-500")} />
        </button>
        <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-[#003380] text-white font-bold rounded-2xl shadow-xl shadow-blue-900/10 hover:bg-blue-900 transition-all flex items-center gap-2">
          <Plus size={18} /> Nouveau RV
        </button>
      </div>

      <div className="bg-white/60 backdrop-blur-2xl border border-white rounded-[2.5rem] shadow-2xl overflow-hidden min-h-[700px]">
        <div className="grid grid-cols-7 border-b border-slate-100 bg-slate-50/50">
          {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map(d => (
            <div key={d} className="p-4 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest border-r border-slate-100 last:border-0">{d}</div>
          ))}
        </div>

        <div className="grid grid-cols-7 grid-rows-6 flex-1">
          {days.map((day, i) => {
            const isToday = day.toDateString() === new Date().toDateString();
            const isCurrentMonth = day.getMonth() === selectedDate.getMonth();
            const dayAppts = appointments.filter(a => new Date(a.datetime_start).toDateString() === day.toDateString());
            
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
                    let timeLabel = new Date(a.datetime_start).toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
                    if (a.scheduling_type === 'FULL_DAY') timeLabel = 'JOUR';
                    if (a.scheduling_type === 'MORNING') timeLabel = 'MATIN';
                    if (a.scheduling_type === 'AFTERNOON') timeLabel = 'APREM';
                    return (
                      <div key={a.id} className="text-[9px] font-bold bg-white border border-slate-100 p-1 rounded-md text-slate-700 truncate shadow-sm">
                        {timeLabel} - {a.patient_name}
                      </div>
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
        onClose={() => setIsModalOpen(false)} 
        onSaved={fetchAppointments} 
        selectedDate={modalDate || selectedDate} 
      />
    </div>
  );
};
