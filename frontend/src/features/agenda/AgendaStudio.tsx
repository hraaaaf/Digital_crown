import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Calendar, ChevronLeft, ChevronRight, LayoutGrid, CalendarDays, ListFilter, UploadCloud, Ticket, Users } from 'lucide-react';
import { cn } from '../../utils/cn';
import { DailyView } from './DailyView';
import { WeeklyView } from './WeeklyView';
import { MonthlyView } from './MonthlyView';
import { GoogleImportModal } from './GoogleImportModal';
import { FrontdeskModal } from './FrontdeskModal';
import { AgendaModal } from './AgendaModal';
import { PendingRequestCard } from './PendingRequestCard';
import { api } from '../../services/api';
import { Ghost, Settings, AlertCircle } from 'lucide-react';

export type AgendaViewMode = 'day' | 'week' | 'month' | 'multi';

const STATUS_COLORS: Record<string, string> = {
  'PRÉVU': 'bg-blue-100 text-blue-700',
  'EN_S_ATTENTE': 'bg-amber-100 text-amber-700',
  'EN_FAUTEUIL': 'bg-emerald-100 text-emerald-700',
  'TERMINÉ': 'bg-slate-100 text-slate-400',
  'ANNULÉ': 'bg-rose-50 text-rose-400',
  'EN_ATTENTE_DEMANDE': 'bg-orange-100 text-orange-700',
  'EN_ATTENTE_CONFIRM': 'bg-yellow-100 text-yellow-700',
  'CONFIRMÉ': 'bg-blue-100 text-blue-700',
  'REFUSÉ': 'bg-red-100 text-red-500 line-through',
  'EXPIRÉ': 'bg-gray-100 text-gray-400',
  'ABSENT': 'bg-rose-100 text-rose-600',
};

const MultiPractitionerView: React.FC<{ data: any; loading: boolean }> = ({ data, loading }) => {
  if (loading) return (
    <div className="py-20 text-center text-slate-400 font-bold animate-pulse">Chargement…</div>
  );
  if (!data) return null;
  if (data.error === 'PREMIUM') return (
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

  const dentists: any[] = data.dentists || [];
  return (
    <div className="bg-white/60 backdrop-blur-2xl border border-white rounded-[2.5rem] shadow-2xl overflow-hidden">
      <div className={cn("grid divide-x divide-slate-100")} style={{ gridTemplateColumns: `repeat(${dentists.length}, 1fr)` }}>
        {dentists.map((dentist: any) => (
          <div key={dentist.dentist_id} className="flex flex-col">
            <div className="px-6 py-4 bg-indigo-50/50 border-b border-slate-100 text-center">
              <p className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">Dr.</p>
              <p className="font-black text-slate-800 text-sm truncate">{dentist.dentist_name}</p>
              <p className="text-[9px] text-slate-400 font-bold">{dentist.appointments.length} RDV cette semaine</p>
            </div>
            <div className="p-3 space-y-2 min-h-[300px]">
              {dentist.appointments.length === 0 ? (
                <p className="text-center text-[10px] text-slate-300 font-bold pt-8">Aucun RDV</p>
              ) : (
                dentist.appointments.map((appt: any) => (
                  <div key={appt.id} className={cn("p-2 rounded-xl text-[10px] font-bold border", STATUS_COLORS[appt.status] || 'bg-slate-50 text-slate-500')}>
                    <p className="font-black truncate">{appt.patient_name || 'Patient'}</p>
                    <p className="opacity-70 mt-0.5">
                      {new Date(appt.datetime_start).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}
                      {' '}
                      {new Date(appt.datetime_start).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                      {' · '}{appt.duration_minutes}min
                    </p>
                    {appt.motif && <p className="opacity-60 truncate mt-0.5 italic">{appt.motif}</p>}
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const AgendaStudio: React.FC = () => {
  const location = useLocation();
  const [viewMode, setViewMode] = useState<AgendaViewMode>('week');
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isFrontdeskModalOpen, setIsFrontdeskModalOpen] = useState(false);
  const [showPendingOnly, setShowPendingOnly] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [upcomingHolidays, setUpcomingHolidays] = useState<any[]>([]);
  const [settings, setSettings] = useState<any>(null);
  const [multiData, setMultiData] = useState<any>(null);
  const [loadingMulti, setLoadingMulti] = useState(false);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);

  // Préremplissage patient (CTA "Prendre RDV" depuis le dossier patient) — modale
  // dédiée, indépendante de celles montées dans DailyView/WeeklyView/MonthlyView.
  const [prefillOpen, setPrefillOpen] = useState(false);
  const [prefillPatient, setPrefillPatient] = useState<{ id: number; nom: string; prenom: string } | null>(null);

  useEffect(() => {
    const state = location.state as { prefillPatientId?: number; prefillPatientNom?: string; prefillPatientPrenom?: string } | null;
    if (state?.prefillPatientId) {
      setPrefillPatient({ id: state.prefillPatientId, nom: state.prefillPatientNom || '', prenom: state.prefillPatientPrenom || '' });
      setPrefillOpen(true);
      // Nettoie le state de navigation pour qu'un retour arrière ne rouvre pas la modale.
      window.history.replaceState({}, '', location.pathname);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPendingRequests = async () => {
    try {
      const res = await api.get('/appointments/pending');
      setPendingRequests(res.data);
      setPendingCount(res.data.length);
    } catch (err) {
      console.error('Error fetching pending requests:', err);
    }
  };

  useEffect(() => {
    api.get('/upcoming-holidays').then(res => setUpcomingHolidays(res.data)).catch(console.error);
    api.get('/agenda/settings').then(res => setSettings(res.data)).catch(console.error);
    fetchPendingRequests();
  }, []);

  useEffect(() => {
    const interval = setInterval(fetchPendingRequests, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

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

  const fetchMulti = async () => {
    setLoadingMulti(true);
    try {
      const start = new Date(selectedDate);
      start.setDate(start.getDate() - start.getDay() + 1);
      start.setHours(0,0,0,0);
      const end = new Date(start);
      end.setDate(end.getDate() + 6);
      end.setHours(23,59,59,999);
      const res = await api.get('/appointments/multi-practitioner', {
        params: { start_date: start.toISOString(), end_date: end.toISOString() }
      });
      setMultiData(res.data);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setMultiData({ error: 'PREMIUM' });
      }
    } finally {
      setLoadingMulti(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'multi') fetchMulti();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewMode, selectedDate]);

  const renderView = () => {
    switch (viewMode) {
      case 'day': return <DailyView key={`day-${refreshKey}`} selectedDate={selectedDate} />;
      case 'week': return <WeeklyView key={`week-${refreshKey}`} selectedDate={selectedDate} />;
      case 'month': return <MonthlyView key={`month-${refreshKey}`} selectedDate={selectedDate} />;
      case 'multi': return <MultiPractitionerView data={multiData} loading={loadingMulti} />;
      default: return <WeeklyView key={`week-${refreshKey}`} selectedDate={selectedDate} />;
    }
  };

  const handleBlockHoliday = async () => {
    if (upcomingHolidays.length === 0) return;
    const hol = upcomingHolidays[0];
    try {
      await api.post('/agenda/exceptions', {
        start_date: hol.date,
        end_date: hol.date,
        reason: hol.name,
        is_recurring: false
      });
      // Optionally reload or show a success message
      setUpcomingHolidays(prev => prev.slice(1));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      
      {/* GHOST CALENDRIER */}
      {upcomingHolidays.length > 0 && (
        <div className="bg-primary text-white p-4 rounded-2xl shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-4">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-white/20 rounded-xl">
              <Ghost size={24} className="animate-pulse" />
            </div>
            <div>
              <h3 className="font-black text-lg">Ghost Calendrier</h3>
              <p className="text-white/80 text-sm">
                Prochain jour férié : <strong>{upcomingHolidays[0].name}</strong> le {new Date(upcomingHolidays[0].date).toLocaleDateString('fr-FR')}
              </p>
            </div>
          </div>
          <button 
            onClick={handleBlockHoliday}
            className="bg-white text-primary px-4 py-2 rounded-xl font-bold text-sm hover:bg-slate-100 transition-colors"
          >
            Bloquer l'agenda
          </button>
        </div>
      )}

      {/* GLOBAL CONTROLS HEADER */}
      <div data-tour="agenda-header" className="flex flex-col lg:flex-row justify-between items-center gap-6 bg-white/40 backdrop-blur-2xl border border-white/60 p-6 rounded-[2.5rem] shadow-2xl">
        
        {/* Left: Branding & Date Navigation */}
        <div className="flex items-center gap-6">
          <div className="w-14 h-14 bg-primary text-white rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20 transform hover:scale-105 transition-transform">
            <Calendar size={28} />
          </div>
          
          <div className="space-y-1">
            <h1 className="text-3xl font-black text-primary tracking-tight">Studio Agenda</h1>
            <div className="flex items-center gap-3">
              <button onClick={handlePrev} className="p-1.5 hover:bg-white/60 rounded-full transition-colors text-primary">
                <ChevronLeft size={20} />
              </button>
              <span className="text-sm font-black text-slate-600 min-w-[140px] text-center uppercase tracking-wider">
                {viewMode === 'month' 
                  ? selectedDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
                  : selectedDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
              </span>
              <button onClick={handleNext} className="p-1.5 hover:bg-white/60 rounded-full transition-colors text-primary">
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* Right: View Switching & Actions */}
        <div data-tour="agenda-view-switcher" className="flex items-center gap-4 bg-slate-100/50 p-1.5 rounded-2xl border border-slate-200/50 backdrop-blur-md">
          {settings?.use_tickets && (
            <button 
              className="flex items-center gap-2 px-4 py-2.5 text-amber-600 hover:bg-amber-100 font-bold text-sm rounded-xl transition-all"
              title="Générer un ticket"
            >
              <Ticket size={18} />
              <span className="hidden xl:inline">Nouveau Ticket</span>
            </button>
          )}

          <button
            onClick={() => setIsFrontdeskModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 text-orange-600 hover:bg-orange-100 font-bold text-sm rounded-xl transition-all relative"
            title="Nouvelle demande RDV frontdesk"
          >
            <AlertCircle size={18} />
            <span className="hidden xl:inline">Demande RDV</span>
            {pendingCount > 0 && <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-black w-5 h-5 rounded-full flex items-center justify-center">{pendingCount}</span>}
          </button>

          <button
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 text-primary hover:brightness-110 hover:bg-primary/10 font-bold text-sm rounded-xl transition-all"
            title="Importer depuis Google Agenda"
          >
            <UploadCloud size={18} />
            <span className="hidden xl:inline">Importer</span>
          </button>
          
          <div className="w-px h-6 bg-slate-200 mx-1" />

          <button 
            onClick={() => setViewMode('day')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'day' ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-primary hover:bg-white/40"
            )}
          >
            <CalendarDays size={18} /> Jour
          </button>
          <button 
            onClick={() => setViewMode('week')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'week' ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-primary hover:bg-white/40"
            )}
          >
            <ListFilter size={18} /> Semaine
          </button>
          <button 
            onClick={() => setViewMode('month')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'month' ? "bg-white text-primary shadow-sm" : "text-slate-500 hover:text-primary hover:bg-white/40"
            )}
          >
            <LayoutGrid size={18} /> Mois
          </button>
          <button
            onClick={() => setViewMode('multi')}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all",
              viewMode === 'multi' ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-indigo-600 hover:bg-white/40"
            )}
            title="Vue multi-praticien (PREMIUM/ELITE)"
          >
            <Users size={18} /> Multi
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

      {/* PENDING REQUESTS SECTION */}
      {pendingCount > 0 && (
        <div className="space-y-3 bg-orange-50 border-2 border-orange-200 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-black text-orange-800 flex items-center gap-2">
              <AlertCircle size={20} /> Demandes en attente ({pendingCount})
            </h2>
            <button
              onClick={() => setShowPendingOnly(!showPendingOnly)}
              className="text-xs px-3 py-1.5 bg-orange-200 text-orange-800 rounded-lg hover:bg-orange-300 font-bold"
            >
              {showPendingOnly ? 'Afficher tout' : 'Afficher seulement'}
            </button>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {pendingRequests.map(req => (
              <PendingRequestCard
                key={req.id}
                request={req}
                onAction={() => {
                  fetchPendingRequests();
                  setRefreshKey(prev => prev + 1);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* RENDER ACTIVE VIEW */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        {renderView()}
      </div>

      <FrontdeskModal
        open={isFrontdeskModalOpen}
        onClose={() => setIsFrontdeskModalOpen(false)}
        onSuccess={() => {
          fetchPendingRequests();
          setRefreshKey(prev => prev + 1);
          setIsFrontdeskModalOpen(false);
        }}
        selectedDate={selectedDate}
      />

      <GoogleImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          // Force le rafraichissement de la vue active
          setRefreshKey(prev => prev + 1);
        }}
      />

      {prefillPatient && (
        <AgendaModal
          isOpen={prefillOpen}
          onClose={() => { setPrefillOpen(false); setPrefillPatient(null); }}
          onSaved={() => {
            setRefreshKey(prev => prev + 1);
            setPrefillOpen(false);
            setPrefillPatient(null);
          }}
          selectedDate={selectedDate}
          initialPatientId={prefillPatient.id}
          initialPatientNom={prefillPatient.nom}
          initialPatientPrenom={prefillPatient.prenom}
        />
      )}

    </div>
  );
};
