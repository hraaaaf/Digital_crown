import { useState, useMemo } from 'react';
import { Calendar, Clock, Plus, WifiOff } from 'lucide-react';
import { DndContext, TouchSensor, MouseSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { format, addDays, startOfWeek, startOfMonth, endOfMonth, isSameDay, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import type { Snapshot, SyncStatus, ApptStatus, Appointment } from '../types';
import { Skeleton } from '../components/Skeleton';
import { DraggableApptCard } from '../components/DraggableApptCard';
import { DroppableDay } from '../components/DroppableDay';
import { AddApptModal } from '../components/AddApptModal';
import { cn } from '../../../../utils/cn';

type ViewMode = 'jour' | 'semaine' | 'mois';

const TIME_SLOTS = Array.from({ length: 20 }, (_, i) => {
  const hour = Math.floor(i / 2) + 9;
  const min = i % 2 === 0 ? '00' : '30';
  return `${hour.toString().padStart(2, '0')}:${min}`;
});

export function AgendaView({
  snapshot,
  syncStatus,
  selectedDate,
  setSelectedDate,
  patients,
  onStatusChange,
  onRescheduleAppt,
  openApptWhatsApp,
  handleDeleteAppt,
  handleOpenSignature,
  onRefresh,
  onPatientCreated
}: {
  snapshot: Snapshot | null;
  syncStatus: SyncStatus;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  patients: { id: number; name: string; phone: string | null }[];
  onStatusChange: (id: number, status: ApptStatus) => void;
  onRescheduleAppt: (id: number, newDate: string, newTime: string) => void;
  openApptWhatsApp: (apt: Appointment) => void;
  handleDeleteAppt: (id: number) => void;
  handleOpenSignature: (id: number, name: string) => void;
  onRefresh: () => void;
  onPatientCreated: (pt: { id: number; name: string; phone: string | null }) => void;
}) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('jour');

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 10 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } })
  );

  const termineCount = snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = snapshot?.appointments.length ?? 0;
  const dayAppointments = snapshot?.appointments.filter(a => !a.date || a.date === selectedDate) || [];

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const aptId = parseInt(active.id.toString().replace('appt-', ''), 10);
    const targetDate = over.id.toString().replace('day-', '');
    
    if (targetDate === selectedDate) return;

    const apt = snapshot?.appointments.find(a => a.id === aptId);
    if (!apt) return;

    if (window.confirm(`Déplacer ce rendez-vous au ${format(parseISO(targetDate), 'dd MMMM', { locale: fr })} à ${apt.time} ?`)) {
      onRescheduleAppt(aptId, targetDate, apt.time);
      setSelectedDate(targetDate);
    }
  };

  const currentParsedDate = useMemo(() => parseISO(selectedDate), [selectedDate]);

  const weekDays = useMemo(() => {
    const start = startOfWeek(currentParsedDate, { weekStartsOn: 1 });
    return Array.from({ length: 7 }).map((_, i) => addDays(start, i));
  }, [currentParsedDate]);

  const monthDays = useMemo(() => {
    const start = startOfMonth(currentParsedDate);
    const end = endOfMonth(currentParsedDate);
    const days = [];
    let d = start;
    while (d <= end) {
      days.push(d);
      d = addDays(d, 1);
    }
    return days;
  }, [currentParsedDate]);

  const hasApptOnDate = (d: string) => {
    return snapshot?.appointments.some(a => a.date === d) || false;
  };

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="space-y-6">
        
        {/* Toggle Mode */}
        <div className="flex bg-glass-bg border border-glass-border rounded-full p-1 shadow-sm">
          {(['jour', 'semaine', 'mois'] as ViewMode[]).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={cn(
                "flex-1 py-2 rounded-full text-xs font-black uppercase tracking-widest transition-all",
                viewMode === mode 
                  ? "bg-primary text-white shadow-md scale-[1.02]" 
                  : "text-text-muted hover:text-primary"
              )}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Calendar Navigators */}
        {viewMode === 'semaine' && (
          <div className="flex gap-2 overflow-x-auto pb-2 snap-x hide-scrollbar">
            {weekDays.map(d => {
              const dateStr = format(d, 'yyyy-MM-dd');
              return (
                <div key={dateStr} className="snap-center min-w-[4rem]">
                  <DroppableDay 
                    date={dateStr}
                    label={format(d, 'd')}
                    sublabel={format(d, 'EEE', { locale: fr })}
                    isSelected={dateStr === selectedDate}
                    onClick={() => setSelectedDate(dateStr)}
                    hasAppointments={hasApptOnDate(dateStr)}
                  />
                </div>
              );
            })}
          </div>
        )}

        {viewMode === 'mois' && (
          <div className="bg-white border border-slate-100 rounded-[24px] p-4 shadow-sm">
            <h3 className="text-sm font-black text-center mb-4 capitalize">{format(currentParsedDate, 'MMMM yyyy', { locale: fr })}</h3>
            <div className="grid grid-cols-7 gap-2">
              {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map(day => (
                <div key={day} className="text-center text-[10px] font-black text-text-muted uppercase tracking-widest mb-2">{day}</div>
              ))}
              {Array.from({ length: (weekDays[0].getDay() + 6) % 7 }).map((_, i) => (
                <div key={`empty-${i}`} />
              ))}
              {monthDays.map(d => {
                const dateStr = format(d, 'yyyy-MM-dd');
                return (
                  <DroppableDay 
                    key={dateStr}
                    date={dateStr}
                    label={format(d, 'd')}
                    isSelected={dateStr === selectedDate}
                    onClick={() => setSelectedDate(dateStr)}
                    isMonthView
                    hasAppointments={hasApptOnDate(dateStr)}
                  />
                );
              })}
            </div>
            <p className="text-[10px] text-center text-text-muted mt-4 mt-2">
              Glissez-déposez un rendez-vous sur un jour pour le déplacer.
            </p>
          </div>
        )}

        {/* Progress bar */}
        {totalCount > 0 && viewMode === 'jour' && (
          <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5">
                <Clock size={12} /> Progression du jour
              </span>
              <span className="text-[10px] font-black text-primary">{termineCount}/{totalCount} terminés</span>
            </div>
            <div className="h-1.5 bg-border-main rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-700"
                style={{ width: `${(termineCount / totalCount) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Appointments List */}
        {syncStatus === 'loading' && !snapshot ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
          </div>
        ) : syncStatus === 'error' && !snapshot ? (
          <div className="bg-card border border-border-main rounded-[24px] py-20 text-center shadow-elite relative overflow-hidden mt-4">
            <div className="w-16 h-16 bg-amber-500/5 border border-amber-500/10 rounded-[20px] flex items-center justify-center mx-auto mb-4 text-amber-500">
              <WifiOff size={32} />
            </div>
            <h4 className="font-black text-amber-500 font-outfit">Données indisponibles</h4>
            <p className="text-text-muted text-[11px] font-medium mt-1">Impossible de charger l'agenda hors-ligne.</p>
          </div>
        ) : !dayAppointments.length ? (
          <div className="bg-card border border-border-main rounded-[24px] py-20 text-center shadow-elite relative overflow-hidden mt-4">
            <div className="w-16 h-16 bg-primary/5 border border-primary/10 rounded-[20px] flex items-center justify-center mx-auto mb-4 text-primary">
              <Calendar size={32} />
            </div>
            <h4 className="font-black text-primary font-outfit">Aucun RDV</h4>
            <p className="text-text-muted text-[11px] font-medium mt-1">L'agenda est libre pour cette date.</p>
          </div>
        ) : (
          <div className="relative pl-8 pb-10">
            {/* Ligne verticale de la timeline */}
            <div className="absolute left-[15px] top-4 bottom-0 w-0.5 bg-border-main/50 rounded-full" />
            
            {viewMode === 'jour' ? (
              <div className="space-y-6">
                {TIME_SLOTS.map(time => {
                  const apts = dayAppointments.filter(a => a.time.startsWith(time.substring(0, 4))); // Match approx
                  // Find exact matches for this slot
                  const exactApt = dayAppointments.find(a => a.time === time);
                  
                  if (exactApt) {
                    return (
                      <div key={time} className="relative">
                        <div className="absolute -left-10 mt-3 bg-white px-1 text-[10px] font-bold text-slate-500 w-8 text-right z-10">
                          {time}
                        </div>
                        <div className="absolute left-[-19px] top-4 w-2.5 h-2.5 rounded-full border-2 border-primary bg-white z-10" />
                        <DraggableApptCard
                          key={exactApt.id}
                          apt={exactApt}
                          onStatusChange={onStatusChange}
                          openApptWhatsApp={openApptWhatsApp}
                          handleDeleteAppt={handleDeleteAppt}
                          handleOpenSignature={handleOpenSignature}
                        />
                      </div>
                    );
                  } else {
                    return (
                      <div key={time} className="relative flex items-center group cursor-pointer" onClick={() => setShowAddModal(true)}>
                        <div className="absolute -left-10 bg-glass-bg px-1 text-[10px] font-medium text-slate-400 w-8 text-right z-10">
                          {time}
                        </div>
                        <div className="absolute left-[-18px] w-2 h-2 rounded-full border border-slate-300 bg-slate-100 z-10 group-hover:border-primary group-hover:bg-primary/20 transition-colors" />
                        <div className="h-10 flex-1 ml-4 border border-dashed border-slate-200 rounded-[12px] flex items-center px-4 text-[10px] text-slate-400 font-medium group-hover:border-primary/50 group-hover:text-primary transition-colors bg-white/30 backdrop-blur-sm">
                          <Plus size={12} className="mr-1" /> Créneau libre
                        </div>
                      </div>
                    );
                  }
                })}
              </div>
            ) : (
              <div className="space-y-4">
                {dayAppointments.map(apt => (
                  <div key={apt.id} className="relative">
                    <div className="absolute -left-10 mt-3 bg-white px-1 text-[10px] font-bold text-slate-500 w-8 text-right z-10">
                      {apt.time}
                    </div>
                    <div className="absolute left-[-19px] top-4 w-2.5 h-2.5 rounded-full border-2 border-primary bg-white z-10" />
                    <DraggableApptCard
                      apt={apt}
                      onStatusChange={onStatusChange}
                      openApptWhatsApp={openApptWhatsApp}
                      handleDeleteAppt={handleDeleteAppt}
                      handleOpenSignature={handleOpenSignature}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bouton d'ajout de RDV */}
        <div className="fixed bottom-32 right-6 z-40">
          <button onClick={() => setShowAddModal(true)} className="w-14 h-14 bg-primary text-white rounded-full shadow-[0_8px_30px_rgba(var(--primary-rgb),0.4)] flex items-center justify-center hover:scale-105 active:scale-95 transition-transform border border-white/20">
            <Plus size={24} />
          </button>
        </div>

        {showAddModal && (
          <AddApptModal
            selectedDate={selectedDate}
            patients={patients}
            onClose={() => setShowAddModal(false)}
            onSuccess={onRefresh}
            onPatientCreated={onPatientCreated}
          />
        )}
      </div>
    </DndContext>
  );
}
