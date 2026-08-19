import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Plus, Loader2, RefreshCw, Calendar } from 'lucide-react';
import { cn } from '../../utils/cn';
import { AgendaModal } from './AgendaModal';
import { getDayBounds, getDaySchedule, getExceptionForDate, isDateOpen, type AgendaExceptionLike, type AgendaSettingsLike } from './agendaSchedule';

export type AppointmentStatus = 'PRÉVU' | 'EN_S_ATTENTE' | 'EN_FAUTEUIL' | 'TERMINÉ' | 'ANNULÉ' | 'EN_ATTENTE_DEMANDE' | 'EN_ATTENTE_CONFIRM' | 'CONFIRMÉ' | 'REFUSÉ' | 'EXPIRÉ' | 'ABSENT';

export interface Appointment {
  id: number;
  patient_id?: number | null;
  patient_name?: string | null;
  datetime_start: string;
  duration_minutes: number;
  motif?: string | null;
  status: AppointmentStatus;
  scheduling_type?: 'EXACT_TIME' | 'MORNING' | 'AFTERNOON' | 'FULL_DAY';
  notes?: string | null;
  reminder_sent?: boolean;
  reminder_sent_at?: string | null;
}

interface DailyViewProps {
  selectedDate: Date;
  agendaSettings?: AgendaSettingsLike | null;
  exceptions?: AgendaExceptionLike[] | null;
}

export const DailyView: React.FC<DailyViewProps> = ({ selectedDate, agendaSettings, exceptions }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [initialTime, setInitialTime] = useState('09:00');
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  
  const daySchedule = getDaySchedule(selectedDate, agendaSettings);
  const exception = getExceptionForDate(selectedDate, exceptions);
  const dayOpen = isDateOpen(selectedDate, agendaSettings, exceptions);
  const { startHour, endHour } = getDayBounds(daySchedule);
  const totalHours = endHour - startHour;
  const slotsPerHour = 4;
  const totalSlots = totalHours * slotsPerHour;

  const handleGridClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!dayOpen) return;
    // Ne pas ouvrir si on clique sur un rdv existant (ils ont leur propre z-index et stopPropagation pourrait être ajouté)
    if ((e.target as HTMLElement).closest('.appointment-item')) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const slotIndex = Math.floor(y / 24); // 24px par slot de 15 min
    
    const hours = startHour + Math.floor(slotIndex / slotsPerHour);
    const minutes = (slotIndex % slotsPerHour) * 15;
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    
    setInitialTime(timeString);
    setEditingAppointment(null);
    setIsModalOpen(true);
  };

  const handleEditClick = (e: React.MouseEvent, appt: Appointment) => {
    e.stopPropagation();
    setEditingAppointment(appt);
    setIsModalOpen(true);
  };


  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const startOfDay = new Date(selectedDate);
      startOfDay.setHours(0, 0, 0, 0);
      
      const endOfDay = new Date(selectedDate);
      endOfDay.setHours(23, 59, 59, 999);

      const res = await api.get('/appointments/', {
        params: {
          start_date: startOfDay.toISOString(),
          end_date: endOfDay.toISOString()
        }
      });
      setAppointments(res.data);
    } catch (e) {
      console.error("Erreur de récupération des rendez-vous:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  // Générer les labels de temps : 08:00, 09:00, etc.
  const timeLabels = Array.from({ length: totalHours }).map((_, i) => {
    const hour = startHour + i;
    return `${hour.toString().padStart(2, '0')}:00`;
  });

    const getStatusColor = (status: AppointmentStatus) => {
    switch(status) {
      case 'PRÉVU': return 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20';
      case 'EN_S_ATTENTE': return 'bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200';
      case 'EN_FAUTEUIL': return 'bg-emerald-100 text-emerald-700 border-emerald-200 hover:bg-emerald-200';
      case 'TERMINÉ': return 'bg-slate-100 text-slate-500 border-slate-200 opacity-60';
      case 'ANNULÉ': return 'bg-rose-50 text-rose-500 border-rose-200 line-through opacity-70';
      case 'EN_ATTENTE_DEMANDE': return 'bg-orange-100 text-orange-700 border-orange-400 hover:bg-orange-200';
      case 'EN_ATTENTE_CONFIRM': return 'bg-yellow-100 text-yellow-700 border-yellow-400 hover:bg-yellow-200';
      case 'CONFIRMÉ': return 'bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-200';
      case 'REFUSÉ': return 'bg-red-100 text-red-500 border-red-200 line-through opacity-70';
      case 'EXPIRÉ': return 'bg-gray-100 text-gray-400 border-gray-200 opacity-50';
      case 'ABSENT': return 'bg-rose-100 text-rose-600 border-rose-200 hover:bg-rose-200';
      default: return 'bg-primary/5 text-primary border-primary/10';
    }
  };

  const getStatusBadgeColor = (status: AppointmentStatus) => {
    switch(status) {
      case 'PRÉVU': return 'bg-primary';
      case 'EN_S_ATTENTE': return 'bg-amber-500';
      case 'EN_FAUTEUIL': return 'bg-emerald-500';
      case 'TERMINÉ': return 'bg-slate-400';
      case 'ANNULÉ': return 'bg-rose-500';
      case 'EN_ATTENTE_DEMANDE': return 'bg-orange-500';
      case 'EN_ATTENTE_CONFIRM': return 'bg-yellow-500';
      case 'CONFIRMÉ': return 'bg-blue-500';
      case 'REFUSÉ': return 'bg-red-500';
      case 'EXPIRÉ': return 'bg-gray-400';
      case 'ABSENT': return 'bg-rose-600';
      default: return 'bg-primary';
    }
  };

  // Convertit une datetime backend en index de row (0 à totalSlots-1)
  const getSlotRow = (isoString: string) => {
    const date = new Date(isoString);
    const hour = date.getHours();
    const min = date.getMinutes();
    
    // Si hors plage, limite
    if (hour < startHour) return 0;
    if (hour >= endHour) return totalSlots - 1;
    
    const rowOffset = (hour - startHour) * slotsPerHour;
    const minOffset = Math.floor(min / 15);
    return rowOffset + minOffset;
  };

  // Convertit une durée en nombre de slots (span)
  const getDurationSpan = (minutes: number) => {
    return Math.max(1, Math.ceil(minutes / 15));
  };

  const exactAppointments = appointments.filter(a => !a.scheduling_type || a.scheduling_type === 'EXACT_TIME');
  const flexAppointments = appointments.filter(a => a.scheduling_type && a.scheduling_type !== 'EXACT_TIME');

  return (
    <div className="w-full space-y-6">
      
      {/* QUICK ACTIONS BAR */}
      <div className="flex justify-end gap-3 px-2">
        <button onClick={fetchAppointments} className="p-3 bg-white/50 border border-white hover:bg-white text-slate-500 rounded-2xl transition-all shadow-sm">
          <RefreshCw size={18} className={cn(loading && "animate-spin text-primary")} />
        </button>
        <button 
          onClick={() => setIsModalOpen(true)}
          disabled={!dayOpen}
          title={!dayOpen ? 'Cabinet fermé ce jour' : 'Nouveau rendez-vous'}
          className="px-4 sm:px-6 py-3 bg-primary text-white font-bold rounded-2xl shadow-xl shadow-primary/20 hover:brightness-110 hover:-translate-y-0.5 transition-all flex items-center gap-2 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none disabled:hover:translate-y-0 disabled:cursor-not-allowed"
        >
          <Plus size={18} /> Nouveau RV
        </button>
      </div>

      {!dayOpen && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
          <p className="font-black">Cabinet fermé ce jour</p>
          <p className="text-sm font-medium mt-1">{exception?.reason || 'Jour fermé selon les horaires du cabinet.'}</p>
        </div>
      )}

      {/* CSS GRID AGENDA */}
      <div className="bg-white/80 backdrop-blur-xl border border-white rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
        
        {/* FLEXIBLE APPOINTMENTS HEADER */}
        {flexAppointments.length > 0 && (
          <div className="border-b border-slate-100 bg-slate-50/50 p-4">
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Calendar size={14} /> Planification Flexible
            </h3>
            <div className="flex flex-col gap-2">
              {flexAppointments.map(appt => {
                const labels: Record<string, string> = {
                  'MORNING': 'Matin',
                  'AFTERNOON': 'Après-Midi',
                  'FULL_DAY': 'Toute la journée'
                };
                const typeLabel = labels[appt.scheduling_type as string] || '';
                return (
                  <div
                    key={appt.id}
                    onClick={(e) => handleEditClick(e, appt)}
                    className={cn(
                      "p-3 rounded-xl border border-l-4 shadow-sm cursor-pointer transition-all flex justify-between items-center hover:scale-[1.01]",
                      getStatusColor(appt.status)
                    )}
                    style={{ borderLeftColor: 'currentColor' }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-black uppercase tracking-widest bg-white/50 px-2 py-1 rounded-md">
                        {typeLabel}
                      </span>
                      <span className="font-black text-sm">
                        {appt.patient_name || `Patient #${appt.patient_id}`}
                      </span>
                      {appt.motif && <span className="text-xs opacity-90">— {appt.motif}</span>}
                    </div>
                    <div className="flex items-center gap-1.5 opacity-80">
                      <div className={cn("w-2 h-2 rounded-full", getStatusBadgeColor(appt.status))}></div>
                      <span className="text-[10px] font-bold tracking-widest capitalize">{appt.status.replace('_', ' ')}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {loading && appointments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-primary/60">
            <Loader2 className="animate-spin mb-4 text-primary" size={40} />
            <p className="font-bold tracking-widest uppercase text-xs">Chargement des créneaux...</p>
          </div>
        ) : (
          <div className="flex relative overflow-y-auto" style={{ height: '700px' }}>
            
            {/* Colonne des heures (gauche) */}
            <div className="w-20 flex-shrink-0 border-r border-slate-100 bg-slate-50/50 sticky left-0 z-20">
              {timeLabels.map((time) => (
                <div key={time} className="h-24 relative border-b border-slate-100">
                  <span className="absolute -top-3 left-0 w-full text-center text-xs font-black text-slate-400 tracking-wide">{time}</span>
                </div>
              ))}
            </div>

            {/* Grille Principale (Droite) */}
            <div 
              className="flex-1 relative bg-white/30 cursor-crosshair group" 
              onClick={handleGridClick}
              style={{
                backgroundImage: 'linear-gradient(to bottom, transparent 95%, rgba(226, 232, 240, 0.5) 95%)',
                backgroundSize: '100% 6rem' 
              }}
            >
              
              {/* Lignes pointillées pour les 15 mins (visuel léger) */}
              <div className="absolute inset-0 pointer-events-none" style={{
                backgroundImage: 'linear-gradient(to bottom, transparent 95%, rgba(226, 232, 240, 0.2) 95%)',
                backgroundSize: '100% 1.5rem' // 1.5rem = 24px -> hauteur de 15 minutes
              }}></div>

              {/* Empty state */}
              {!loading && appointments.length === 0 && (
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none opacity-30">
                  <Calendar size={40} className="mb-2 text-primary" />
                  <p className="text-sm font-black text-slate-500 uppercase tracking-widest">Aucun rendez-vous ce jour</p>
                </div>
              )}

              {/* Rendu des Rendez-vous - On utilise `top` et `height` absolus */}
              {exactAppointments.map((appt) => {
                const rowStart = getSlotRow(appt.datetime_start);
                const span = getDurationSpan(appt.duration_minutes);
                
                // Si out of bounds
                if (rowStart < 0 || rowStart >= totalSlots) return null;

                const topPixel = rowStart * 24; // 24px par slot de 15 min
                const heightPixel = span * 24;  // hauteur en px

                return (
                  <div 
                    key={appt.id}
                    onClick={(e) => handleEditClick(e, appt)}
                    className={cn(
                      "appointment-item absolute left-2 right-4 p-3 rounded-xl border border-l-4 shadow-sm cursor-pointer transition-all z-10 flex flex-col hover:scale-[1.01] hover:shadow-md",
                      getStatusColor(appt.status)
                    )}
                    style={{ 
                      top: `${topPixel}px`, 
                      height: `${heightPixel - 4}px`, // -4px pour laisser de l'espace margin
                      borderLeftColor: 'currentColor'
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="font-black text-sm truncate pr-2">
                        {appt.patient_name || `Patient #${appt.patient_id}`}
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0 opacity-80">
                         <div className={cn("w-2 h-2 rounded-full", getStatusBadgeColor(appt.status))}></div>
                         <span className="text-[10px] font-bold tracking-widest capitalize">{appt.status.replace('_', ' ')}</span>
                      </div>
                    </div>
                    
                    {appt.motif && heightPixel >= 48 && ( // N'affiche le motif que si le créneau est >= 30min
                      <p className="text-xs font-medium mt-1 truncate opacity-90">{appt.motif}</p>
                    )}
                  </div>
                );
              })}

              {/* Ligne rouge "Maintenant" (Si on est sur la date du jour) */}
              {selectedDate.toDateString() === new Date().toDateString() && (
                <div 
                  className="absolute left-0 right-0 border-t-2 border-rose-500 z-30 pointer-events-none"
                  style={{
                    top: `${getSlotRow(new Date().toISOString()) * 24}px`
                  }}
                >
                  <div className="absolute -top-1.5 -left-1.5 w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(225,29,72,0.8)]"></div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>

      <AgendaModal 
        isOpen={isModalOpen}
        onClose={() => {
            setIsModalOpen(false);
            setEditingAppointment(null);
        }}
        onSaved={fetchAppointments}
        selectedDate={selectedDate}
        initialTime={initialTime}
        editingAppointment={editingAppointment}
      />

    </div>
  );
};
