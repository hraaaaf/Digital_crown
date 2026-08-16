import React, { useCallback, useEffect, useState } from 'react';
import { BarChart2, ChevronRight, Sparkles, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '../utils/cn';
import { hasAccess } from '../utils/accessControl';
import { useSettingsStore } from '../features/admin/Settings/hooks/useSettingsStore';
import { useAuthStore } from '../stores/useAuthStore';
import { MobileSecurity } from '../features/admin/Security/MobileSecurity';
import { EliteGhostLoader } from '../components/EliteGhostLoader';
import { DayOneTour } from '../components/DayOneTour';
import { getCabinetHealthDisplayState, useCabinetHealth } from '../hooks/useCabinetHealth';
import { dashboardContainerVariants } from '../features/dashboard/animations';
import { BusinessInsights } from '../features/dashboard/components/BusinessInsights';
import { CabinetHealth } from '../features/dashboard/components/CabinetHealth';
import { DashboardHeader } from '../features/dashboard/components/DashboardHeader';
import { FinanceSummary } from '../features/dashboard/components/FinanceSummary';
import { IntelligenceAlerts } from '../features/dashboard/components/IntelligenceAlerts';
import { MarketplaceCard } from '../features/dashboard/components/MarketplaceCard';
import { QuickActions } from '../features/dashboard/components/QuickActions';
import { RecentActivity } from '../features/dashboard/components/RecentActivity';
import { WaitingRoom } from '../features/dashboard/components/WaitingRoom';
import { WeeklyPerformance } from '../features/dashboard/components/WeeklyPerformance';
import { useDashboardFinance } from '../features/dashboard/hooks/useDashboardFinance';
import { useDashboardStats } from '../features/dashboard/hooks/useDashboardStats';
import { usePatientSearch } from '../features/dashboard/hooks/usePatientSearch';
import { useProactiveAlerts } from '../features/dashboard/hooks/useProactiveAlerts';
import { useTodayAppointments } from '../features/dashboard/hooks/useTodayAppointments';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const showPatientBadges = useSettingsStore(state => state.profile.show_patient_badges);
  const { user, isLoading: authLoading } = useAuthStore();
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);
  const [showManagement, setShowManagement] = useState(false);
  const [ghostSecretariatPatient, setGhostSecretariatPatient] = useState<{ nom: string; prenom: string } | null>(null);
  const [ghostChecklist, setGhostChecklist] = useState({ encaisser: false, ordonnance: false, rdv: false });

  const canReadPatients = hasAccess(user, 'patients');
  const canUseAgenda = hasAccess(user, 'agenda');
  const canReadAccounting = hasAccess(user, 'accounting');
  const canAdmin = hasAccess(user, 'admin');

  const { stats, statsState, praticienName, refreshStats } = useDashboardStats(user, authLoading);
  const {
    forecast,
    conversion,
    projection,
    latentCash,
    financeToday,
  } = useDashboardFinance(user, authLoading);
  const { alerts, markRead, snooze } = useProactiveAlerts(user, authLoading);
  const patientSearch = usePatientSearch(user);

  const handleCompletedAppointment = useCallback((patient: { nom: string; prenom: string }) => {
    setGhostSecretariatPatient(patient);
    setGhostChecklist({ encaisser: false, ordonnance: false, rdv: false });
  }, []);

  const {
    appointments,
    loadingAppointments,
    refreshAppointments,
    updateAppointmentStatus,
  } = useTodayAppointments({
    user,
    authLoading,
    onStatsRefresh: refreshStats,
    onCompleted: handleCompletedAppointment,
  });

  const cabinetHealthState = useCabinetHealth({
    enabled: canAdmin,
    authLoading,
  });
  const systemStatus = getCabinetHealthDisplayState(cabinetHealthState);

  useEffect(() => {
    if (!(ghostChecklist.encaisser && ghostChecklist.ordonnance && ghostChecklist.rdv)) return;
    const timeout = window.setTimeout(() => {
      setGhostSecretariatPatient(null);
      setGhostChecklist({ encaisser: false, ordonnance: false, rdv: false });
    }, 1000);
    return () => window.clearTimeout(timeout);
  }, [ghostChecklist]);

  useEffect(() => {
    if (!canUseAgenda) setGhostSecretariatPatient(null);
  }, [canUseAgenda]);

  const today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
  const dateLabel = today.charAt(0).toUpperCase() + today.slice(1);
  const displayName = user?.nom_complet || (user?.role === 'SECRETAIRE' ? 'Assistante' : praticienName);
  const dashboardLoading = authLoading || (canReadPatients && statsState !== 'ready' && statsState !== 'error');

  if (dashboardLoading) {
    return <EliteGhostLoader text="Initialisation de votre cabinet..." />;
  }

  return (
    <motion.div
      variants={dashboardContainerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-[1600px] mx-auto w-full px-6 py-8 md:px-10 md:py-10 space-y-10"
    >
      <DayOneTour />

      <DashboardHeader
        displayName={displayName}
        dateLabel={dateLabel}
        canReadPatients={canReadPatients}
        canUseAgenda={canUseAgenda}
        canAdmin={canAdmin}
        systemStatus={systemStatus}
        search={{
          isExpanded: patientSearch.isExpanded,
          query: patientSearch.query,
          results: patientSearch.results,
          loading: patientSearch.loading,
          open: patientSearch.open,
          close: patientSearch.close,
          change: patientSearch.change,
        }}
        onNavigatePatient={patientId => navigate(`/patients/${patientId}`)}
        onOpenMobile={() => setIsMobileModalOpen(true)}
      />

      {/* Priorité 1 : actions fréquentes immédiatement disponibles. */}
      <QuickActions canReadPatients={canReadPatients} canUseAgenda={canUseAgenda} />

      {/* Priorité 2-3 : flux clinique du jour avant toute donnée de pilotage. */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <WaitingRoom
          visible={canUseAgenda}
          appointments={appointments}
          loading={loadingAppointments}
          onRefresh={() => { void refreshAppointments(); }}
          onStatusChange={(appointmentId, status) => { void updateAppointmentStatus(appointmentId, status); }}
        />
        <RecentActivity visible={canReadPatients} stats={stats} showPatientBadges={showPatientBadges} />
      </div>

      {/* Priorité 4 : uniquement les alertes actionnables restent dans le flux principal. */}
      <IntelligenceAlerts
        forecast={null}
        alerts={alerts}
        showForecast={false}
        showAlerts={canReadPatients}
        onNavigatePatient={patientId => navigate(`/patients/${patientId}`)}
        onSnooze={alertId => { void snooze(alertId); }}
        onMarkRead={alertId => { void markRead(alertId); }}
      />

      {/* Priorité 5 : pilotage cabinet disponible, mais replié par défaut. */}
      {canReadAccounting && (
        <motion.section data-tour="dashboard-stats" className="rounded-elite-lg border border-border-main bg-card-bg/60 shadow-elite overflow-hidden">
          <button
            type="button"
            onClick={() => setShowManagement(value => !value)}
            className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left hover:bg-primary/5 transition-colors"
          >
            <span className="flex items-center gap-3 min-w-0">
              <span className="w-10 h-10 rounded-elite-sm bg-primary/10 text-primary border border-primary/15 flex items-center justify-center shrink-0">
                <BarChart2 size={19} />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-black text-primary font-outfit">Pilotage du cabinet</span>
                <span className="block text-xs font-medium text-text-muted mt-0.5">Finances, performance et projections</span>
              </span>
            </span>
            <ChevronRight size={18} className={cn('text-text-muted transition-transform', showManagement && 'rotate-90')} />
          </button>

          <AnimatePresence initial={false}>
            {showManagement && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="border-t border-border-main px-6 py-6 space-y-8">
                  <FinanceSummary visible finance={financeToday} />
                  <WeeklyPerformance visible={canReadPatients} stats={stats} />
                  <IntelligenceAlerts
                    forecast={forecast}
                    alerts={[]}
                    showForecast
                    showAlerts={false}
                    onNavigatePatient={patientId => navigate(`/patients/${patientId}`)}
                    onSnooze={() => undefined}
                    onMarkRead={() => undefined}
                  />
                  <BusinessInsights
                    visible
                    conversion={conversion}
                    projection={projection}
                    latentCash={latentCash}
                    onNavigatePatient={patientId => navigate(`/patients/${patientId}`)}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      )}

      {/* Priorité 6 : état technique réservé à l'administration. */}
      <CabinetHealth visible={canAdmin} healthState={cabinetHealthState} />

      {/* Priorité 7 : approvisionnement secondaire, après le cockpit clinique. */}
      <MarketplaceCard visible={canReadPatients} />

      {/* GHOST SECRÉTARIAT MODAL (To-Do List Magique) */}
      <AnimatePresence>
        {canUseAgenda && ghostSecretariatPatient && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className="fixed bottom-6 right-6 z-50 w-80 bg-slate-900 text-white rounded-2xl shadow-2xl border border-slate-700/50 p-5 overflow-hidden"
          >
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-400 to-cyan-400" />
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-1 flex items-center gap-1">
                  <Sparkles size={10} /> Ghost Action
                </p>
                <h3 className="text-sm font-black text-white truncate max-w-[200px]">
                  Patient Sortant : {ghostSecretariatPatient.nom.toUpperCase()} {ghostSecretariatPatient.prenom}
                </h3>
              </div>
              <button onClick={() => setGhostSecretariatPatient(null)} className="text-slate-400 hover:text-white transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-800 bg-slate-800/50 cursor-pointer hover:bg-slate-800 transition-colors">
                <input
                  type="checkbox"
                  checked={ghostChecklist.encaisser}
                  onChange={event => setGhostChecklist(previous => ({ ...previous, encaisser: event.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
                />
                <span className={cn('text-xs font-bold', ghostChecklist.encaisser ? 'text-slate-500 line-through' : 'text-slate-200')}>
                  Encaisser les soins du jour
                </span>
              </label>
              <label className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-800 bg-slate-800/50 cursor-pointer hover:bg-slate-800 transition-colors">
                <input
                  type="checkbox"
                  checked={ghostChecklist.ordonnance}
                  onChange={event => setGhostChecklist(previous => ({ ...previous, ordonnance: event.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
                />
                <span className={cn('text-xs font-bold', ghostChecklist.ordonnance ? 'text-slate-500 line-through' : 'text-slate-200')}>
                  Remettre l'ordonnance
                </span>
              </label>
              <label className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-800 bg-slate-800/50 cursor-pointer hover:bg-slate-800 transition-colors">
                <input
                  type="checkbox"
                  checked={ghostChecklist.rdv}
                  onChange={event => setGhostChecklist(previous => ({ ...previous, rdv: event.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-900"
                />
                <span className={cn('text-xs font-bold', ghostChecklist.rdv ? 'text-slate-500 line-through' : 'text-slate-200')}>
                  Fixer le RDV de contrôle
                </span>
              </label>
            </div>
            {ghostChecklist.encaisser && ghostChecklist.ordonnance && ghostChecklist.rdv && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 text-center text-[10px] font-black uppercase text-emerald-400">
                Action terminée !
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Security Modal */}
      <AnimatePresence>
        {canAdmin && isMobileModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileModalOpen(false)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] z-10"
            >
              <button
                onClick={() => setIsMobileModalOpen(false)}
                className="absolute top-6 right-6 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors z-20"
              >
                <X size={24} />
              </button>
              <div className="p-8 overflow-y-auto">
                <MobileSecurity />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
