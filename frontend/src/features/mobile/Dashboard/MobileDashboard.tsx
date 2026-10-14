import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { WifiOff } from 'lucide-react';
import { useMobileDashboard } from './hooks/useMobileDashboard';
import { useMobileRuntimeTheme } from './hooks/useMobileRuntimeTheme';
import { useMobileQuickActionCapabilities } from './hooks/useMobileQuickActionCapabilities';
import { usePocketReadCapabilities } from './hooks/usePocketReadCapabilities';
import { canOpenPocketReadTab } from './pocketReadCapabilities';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { WhatsAppModal } from './components/WhatsAppModal';
import { SignatureModal } from './components/SignatureModal';
import { AddApptModal } from './components/AddApptModal';
import { MobileQuickActionHub, type MobileQuickPatientAction } from './components/MobileQuickActionHub';
import { MobileQuickPatientFlow } from './components/MobileQuickPatientFlow';
import { MobileQuickNewPatientModal } from './components/MobileQuickNewPatientModal';
import { PocketTodayOverview } from './components/PocketTodayOverview';
import { PocketAgendaDay } from './views/PocketAgendaDay';
import './components/mobileQuickActionHub.css';
import { WaitingRoomView } from './views/WaitingRoomView';
import { MobilePatientsGate } from './views/MobilePatientsGate';
import { SecuriteView } from './views/SecuriteView';
import { FrontdeskView } from './views/FrontdeskView';
import { NotificationsView } from './views/NotificationsView';
import { FinanceView } from './views/FinanceView';
import { LabView } from './views/LabView';
import { BotView } from './views/BotView';
import { DentistsView } from './views/DentistsView';
import { StockView } from './views/StockView';
import { LibraryView } from './views/LibraryView';
import { MarketplaceView } from './views/MarketplaceView';
import { PWAInstallPrompt } from '../../../components/PWAInstallPrompt';
import { resolveDashboardTab } from '../bridge';

export const MobileDashboard = () => {
  const location = useLocation();
  const { state, actions, refs: { mainRef } } = useMobileDashboard();
  const { access: readAccess, status: readStatus, refresh: refreshReadAccess } = usePocketReadCapabilities(state.snapshot?.generated_at);
  const { capabilities, loaded: capabilitiesLoaded, refresh: refreshCapabilities } = useMobileQuickActionCapabilities();
  const [showQuickAppointment, setShowQuickAppointment] = useState(false);
  const [showQuickNewPatient, setShowQuickNewPatient] = useState(false);
  const [quickPatientAction, setQuickPatientAction] = useState<MobileQuickPatientAction | null>(null);
  const [quickActionsOpen, setQuickActionsOpen] = useState(false);
  const [initialPatientId, setInitialPatientId] = useState<number | null>(null);
  useMobileRuntimeTheme(state.snapshot?.generated_at);

  useEffect(() => {
    actions.setActiveTab(resolveDashboardTab(location.search));
  // setActiveTab is the stable React state setter exposed by the dashboard hook.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  const termineCount = state.snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = state.snapshot?.appointments.length ?? 0;
  const role = state.snapshot?.role ?? '';
  const practitionerModuleAllowed = role === 'DENTISTE' || role === 'ADMIN';
  const effectiveQuickCapabilities = {
    ...capabilities,
    can_create_appointment: capabilities.can_create_appointment && readAccess.agenda,
    can_create_patient: capabilities.can_create_patient && readAccess.patients,
    can_open_clinical_context: capabilities.can_open_clinical_context && readAccess.clinical,
  };
  const quickActionsAvailable = capabilitiesLoaded && (
    effectiveQuickCapabilities.can_create_appointment
    || effectiveQuickCapabilities.can_create_patient
    || effectiveQuickCapabilities.can_open_clinical_context
  );
  const tabAllowed = canOpenPocketReadTab(state.activeTab, readAccess);

  useEffect(() => {
    if (!readAccess.agenda) setShowQuickAppointment(false);
    if (!readAccess.patients) { setShowQuickNewPatient(false); setInitialPatientId(null); }
    if (!readAccess.clinical) setQuickPatientAction(null);
    if (!quickActionsAvailable) setQuickActionsOpen(false);
  }, [readAccess.agenda, readAccess.patients, readAccess.clinical, quickActionsAvailable]);

  const refreshAfterPatientMutation = () => {
    void actions.fetchPatients();
    void actions.fetchSnapshot();
    void refreshCapabilities();
  };

  const selectNavTab = (tab: typeof state.activeTab) => {
    setQuickActionsOpen(false);
    if (tab !== 'patients') setInitialPatientId(null);
    actions.setActiveTab(tab);
  };

  const openPatientCockpit = (patientId: number) => {
    if (!readAccess.patients) return;
    setInitialPatientId(patientId);
    setQuickActionsOpen(false);
    actions.setActiveTab('patients');
  };

  return (
    <div
      data-dc-mobile-shell
      data-pocket-read-status={readStatus}
      data-mob3-quick-action-shell
      className="min-h-[100dvh] bg-background text-text-main flex flex-col pb-28 select-none relative"
      style={{
        backgroundColor: 'var(--bg-medical-pearl)',
        fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
      }}
    >
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />

      <MobileHeader
        activeTab={state.activeTab}
        syncStatus={state.syncStatus}
        snapshot={state.snapshot}
        selectedDate={state.selectedDate}
        setSelectedDate={actions.setSelectedDate}
        fetchSnapshot={() => { void actions.fetchSnapshot(); void refreshReadAccess(); void refreshCapabilities(); }}
        totalCount={readAccess.agenda ? totalCount : 0}
        termineCount={termineCount}
        queuedActionsCount={state.queuedActionsCount}
        onOpenPatients={readAccess.patients ? () => selectNavTab('patients') : undefined}
        notificationsEnabled={readAccess.patients}
      />

      {state.error && state.syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-warning-surface border border-warning-border rounded-[16px] flex items-center gap-3 relative z-10 shadow-sm">
          <WifiOff size={14} className="text-warning shrink-0" />
          <p className="text-[10px] font-black text-warning uppercase tracking-widest">{state.error}</p>
        </div>
      )}

      <div className="relative z-10 mt-2">
        <PWAInstallPrompt />
      </div>

      <main ref={mainRef} className="min-w-0 flex-1 px-4 sm:px-6 overflow-x-hidden overflow-y-auto pb-[calc(132px+env(safe-area-inset-bottom))]">
        <AnimatePresence mode="wait">
          <motion.div
            key={state.activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="h-full"
          >
            {!tabAllowed ? <PocketReadAccessState status={readStatus} onRetry={() => { void refreshReadAccess(); }} /> : <>
            {state.activeTab === 'today' && (
              <PocketTodayOverview
                snapshot={state.snapshot}
                selectedDate={state.selectedDate}
                onOpenPatient={openPatientCockpit}
                canOpenPatient={readAccess.patients}
                onOpenWaitingRoom={() => selectNavTab('waiting-room')}
                onOpenFrontdesk={() => selectNavTab('frontdesk')}
                onOpenAlerts={() => selectNavTab('notifications')}
              />
            )}
            {state.activeTab === 'agenda' && (
              <PocketAgendaDay snapshot={state.snapshot} selectedDate={state.selectedDate} isOnline={state.isOnline} onOpenPatient={openPatientCockpit} canOpenPatient={readAccess.patients} />
            )}
            {state.activeTab === 'waiting-room' && (
              <WaitingRoomView
                snapshot={state.snapshot}
                onStatusChange={actions.handleStatusChange}
              />
            )}
            {state.activeTab === 'patients' && (
              <MobilePatientsGate
                isOnline={state.isOnline}
                initialSelectedId={initialPatientId}
                onClose={() => {
                  setInitialPatientId(null);
                  selectNavTab('today');
                }}
              />
            )}
            {state.activeTab === 'securite' && <SecuriteView snapshot={state.snapshot} syncStatus={state.syncStatus} isOnline={state.isOnline} handleLogout={actions.handleLogout} />}
            {state.activeTab === 'frontdesk' && <FrontdeskView />}
            {state.activeTab === 'notifications' && <NotificationsView onNavigate={selectNavTab} />}
            {state.activeTab === 'lab' && (practitionerModuleAllowed
              ? <LabView labJobs={state.labJobs} handleWhatsAppSend={actions.handleWhatsAppSend} isOnline={state.isOnline} />
              : <PocketRestrictedView label="Envois Labo" />)}
            {state.activeTab === 'finance' && <FinanceView snapshot={state.snapshot} syncStatus={state.syncStatus} selectedDate={state.selectedDate} openWhatsApp={actions.openWhatsApp} handleExportPDF={actions.handleExportPDF} pocketSummaryOnly />}
            {state.activeTab === 'dentists' && <DentistsView embedded />}
            {state.activeTab === 'stock' && <StockView quickMode isOnline={state.isOnline} />}
            {state.activeTab === 'library' && <LibraryView role={state.snapshot?.role} />}
            {state.activeTab === 'marketplace' && (practitionerModuleAllowed
              ? <MarketplaceView />
              : <PocketRestrictedView label="Approvisionnement" />)}
            {state.activeTab === 'bot' && <BotView />}
            </>}
          </motion.div>
        </AnimatePresence>
      </main>

      <MobileQuickActionHub
        capabilities={effectiveQuickCapabilities}
        capabilitiesLoaded={capabilitiesLoaded}
        isOnline={state.isOnline}
        open={quickActionsOpen}
        onOpenChange={setQuickActionsOpen}
        hideLauncher
        onNewAppointment={() => setShowQuickAppointment(true)}
        onNewPatient={() => setShowQuickNewPatient(true)}
        onPatientAction={setQuickPatientAction}
      />

      <MobileBottomNav
        activeTab={state.activeTab}
        setActiveTab={selectNavTab}
        totalCount={totalCount}
        termineCount={termineCount}
        snapshot={state.snapshot}
        readAccess={readAccess}
        quickActionsAvailable={quickActionsAvailable}
        quickActionsOpen={quickActionsOpen}
        onToggleQuickActions={() => setQuickActionsOpen(value => !value)}
      />

      {showQuickAppointment && readAccess.agenda && (
        <AddApptModal
          selectedDate={state.selectedDate}
          patients={state.patients}
          onClose={() => setShowQuickAppointment(false)}
          onSuccess={() => { void actions.fetchSnapshot(); setShowQuickAppointment(false); }}
          onPatientCreated={() => refreshAfterPatientMutation()}
        />
      )}

      {showQuickNewPatient && readAccess.patients && <MobileQuickNewPatientModal onClose={() => setShowQuickNewPatient(false)} onCreated={refreshAfterPatientMutation} />}

      {quickPatientAction && readAccess.clinical && <MobileQuickPatientFlow action={quickPatientAction} onClose={() => setQuickPatientAction(null)} />}

      {state.whatsappApt && readAccess.agenda && (
        <WhatsAppModal
          whatsappTemplate={state.whatsappTemplate}
          setWhatsappTemplate={actions.setWhatsappTemplate}
          customMessage={state.customMessage}
          setCustomMessage={actions.setCustomMessage}
          onCancel={() => actions.setWhatsappApt(null)}
          onSend={actions.handleSendWhatsApp}
        />
      )}

      {state.sigPatientId && readAccess.clinical && (
        <SignatureModal
          sigPatientName={state.sigPatientName}
          isLoadingDocs={state.isLoadingDocs}
          sigDocs={state.sigDocs}
          selectedDocId={state.selectedDocId}
          setSelectedDocId={actions.setSelectedDocId}
          isSigning={state.isSigning}
          onSaveSignature={actions.handleSaveSignature}
          onCancel={() => actions.setSigPatientId(null)}
        />
      )}
    </div>
  );
};
function PocketRestrictedView({ label }: { label: string }) {
  return (
    <section data-mobile-restricted className="pb-8 pt-2">
      <div className="rounded-[24px] border border-glass-border bg-card p-5 shadow-sm">
        <p className="text-[10px] font-black uppercase tracking-[0.16em] text-text-muted">{label}</p>
        <h1 className="mt-2 text-[24px] font-black tracking-tight text-text-main">Accès réservé</h1>
        <p className="mt-2 text-[12px] font-semibold leading-relaxed text-text-muted">
          Cette surface Pocket nécessite une autorisation dans les réglages du profil.
        </p>
      </div>
    </section>
  );
}

function PocketReadAccessState({ status, onRetry }: { status: 'loading' | 'ready' | 'unavailable'; onRetry: () => void }) {
  if (status === 'ready') return <PocketRestrictedView label="Droits du profil" />;
  return <section data-pocket-read-pending className="pb-8 pt-2">
    <div className="rounded-[24px] border border-glass-border bg-card p-5 shadow-sm" role="status">
      <h2 className="text-[20px] font-bold text-text-main">{status === 'loading' ? 'Vérification des accès…' : 'Accès à vérifier'}</h2>
      <p className="mt-2 text-[12px] font-semibold leading-relaxed text-text-muted">{status === 'loading' ? 'Pocket vérifie les droits de votre profil auprès du cabinet.' : 'Reconnectez-vous au cabinet pour vérifier vos droits. Votre appairage est conservé.'}</p>
      {status === 'unavailable' && <button type="button" onClick={onRetry} className="mt-4 min-h-11 rounded-[16px] bg-primary px-4 text-[14px] font-semibold text-on-primary">Réessayer</button>}
    </div>
  </section>;
}
