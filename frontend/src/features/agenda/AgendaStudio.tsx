import React, { useState } from 'react';
import { Calendar, ChevronLeft, ChevronRight, LayoutGrid, CalendarDays, ListFilter } from 'lucide-react';
import { cn } from '../../utils/cn';
import { DailyView } from './DailyView';
import { WeeklyView } from './WeeklyView';
import { MonthlyView } from './MonthlyView';

export type AgendaViewMode = 'day' | 'week' | 'month';

export const AgendaStudio: React.FC = () => {
  const [viewMode, setViewMode] = useState<AgendaViewMode>('week');
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const handlePrev = () => {
    const newDate = new Date(selectedDate);
    if (viewMode === 'day') newDate.setDate(newDate.getDate() - 1);
    else if (viewMode === 'week') newDate.setDate(newDate.getDate() - 7);
    else if (viewMode === 'month') newDate.setMonth(newDate.getMonth() - 1);
    setSelectedDate(newDate);
  };

  const handleNext = () => {
    const newDate = new Date(selectedDate);
    if (viewMode === 'day') newDate.setDate(newDate.getDate() + 1);
    else if (viewMode === 'week') newDate.setDate(newDate.getDate() + 7);
    else if (viewMode === 'month') newDate.setMonth(newDate.getMonth() + 1);
    setSelectedDate(newDate);
  };

  const handleToday = () => {
    setSelectedDate(new Date());
  };

  const renderView = () => {
    switch (viewMode) {
      case 'day': return <DailyView selectedDate={selectedDate} />;
      case 'week': return <WeeklyView selectedDate={selectedDate} />;
      case 'month': return <MonthlyView selectedDate={selectedDate} />;
      default: return <DailyView selectedDate={selectedDate} />;
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      
      {/* GLOBAL CONTROLS HEADER */}
      <div className="flex flex-col lg:flex-row justify-between items-center gap-6 bg-white/40 backdrop-blur-2xl border border-white/60 p-6 rounded-[2.5rem] shadow-2xl">
        
        {/* Left: Branding & Date Navigation */}
        <div className="flex items-center gap-6">
          <div className="w-14 h-14 bg-gradient-to-br from-[#003380] to-[#0055d4] text-white rounded-2xl flex items-center justify-center shadow-lg shadow-blue-900/20 transform hover:scale-105 transition-transform">
            <Calendar size={28} />
          </div>
          
          <div className="space-y-1">
            <h1 className="text-3xl font-black text-[#003380] tracking-tight">Studio Agenda</h1>
            <div className="flex items-center gap-3">
              <button onClick={handlePrev} className="p-1.5 hover:bg-white/60 rounded-full transition-colors text-[#003380]">
                <ChevronLeft size={20} />
              </button>
              <span className="text-sm font-black text-slate-600 min-w-[140px] text-center uppercase tracking-wider">
                {viewMode === 'month' 
                  ? selectedDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
                  : selectedDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
              </span>
              <button onClick={handleNext} className="p-1.5 hover:bg-white/60 rounded-full transition-colors text-[#003380]">
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* Right: View Switching & Actions */}
        <div className="flex items-center gap-4 bg-slate-100/50 p-1.5 rounded-2xl border border-slate-200/50 backdrop-blur-md">
          <button 
            onClick={() => setViewMode('day')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'day' ? "bg-white text-[#003380] shadow-sm" : "text-slate-500 hover:text-[#003380] hover:bg-white/40"
            )}
          >
            <CalendarDays size={18} /> Jour
          </button>
          <button 
            onClick={() => setViewMode('week')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'week' ? "bg-white text-[#003380] shadow-sm" : "text-slate-500 hover:text-[#003380] hover:bg-white/40"
            )}
          >
            <ListFilter size={18} /> Semaine
          </button>
          <button 
            onClick={() => setViewMode('month')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'month' ? "bg-white text-[#003380] shadow-sm" : "text-slate-500 hover:text-[#003380] hover:bg-white/40"
            )}
          >
            <LayoutGrid size={18} /> Mois
          </button>
          <div className="w-px h-6 bg-slate-200 mx-1" />
          <button 
            onClick={handleToday}
            className="px-5 py-2.5 bg-white text-slate-700 font-bold text-sm rounded-xl hover:bg-slate-50 transition-all border border-slate-200 shadow-sm"
          >
            Aujourd'hui
          </button>
        </div>
      </div>

      {/* RENDER ACTIVE VIEW */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        {renderView()}
      </div>

    </div>
  );
};
