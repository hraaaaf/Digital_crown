import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { WifiOff } from 'lucide-react';
import { useMobileDashboard } from './hooks/useMobileDashboard';
import { useMobileRuntimeTheme } from './hooks/useMobileRuntimeTheme';
import { useMobileQuickActionCapabilities } from './hooks/useMobileQuickActionCapabilities';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { WhatsAppModal } from './components/WhatsAppModal';
import { SignatureModal } from './components/SignatureModal';
import { AddApptModal } from './components/AddApptModal';
import { MobileQuickActionHub, type MobileQuickPatientAction } from './components/MobileQuickActionHub';
import { MobileQuickPatientFlow } from './components/MobileQuickPatientFlow';
import { MobileQuickNewPatientModal } from './components/MobileQuickNewPatientModal';
import './components/mobileQuickActionHub.css';
import { AgendaView } from './views/AgendaView';
import { MobilePatientsGate } from './views/MobilePatientsGate';
import { FinanceView } from './views/FinanceView';
import { SecuriteView } from './views/SecuriteView';
import { LabView } from './views/LabView';
import { BotView } from './views/BotView';
import { DentistsView } from './views/DentistsView';
import { FrontdeskView } from './views/FrontdeskView';
import { PWAInstallPrompt } from '../../../components/PWAInstallPrompt';
import { resolveDashboardTab } from '../bridge';

export const MobileDashboard = () => {
  const location = useLocation();
  const { state, actions, refs: { mainRef } } = useMobileDashboard();
  const { capabilities, loaded: capabilitiesLoaded, refresh: refreshCapabilities } = useMobileQuickActionCapabilities();
  const [showQuickAppointment, setShowQuickAppointment] = useState(false);
  const [showQuickNewPatient, setShowQuickNewPatient] = useState(false);
  const [quickPatientAction, setQuickPatientAction] = useState<MobileQuickPatientAction | null>(null);
  const [quickActionsOpen, setQuickActionsOpen] = useState(false);
  useMobileRuntimeTheme(state.snapshot?.generated_at);

  useEffect(() => {
    actions.setActiveTab(resolveDashboardTab(location.search));
  // setActiveTab is the stable React state setter exposed by the dashboard hook.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  const termineCount = state.snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = state.snapshot?.appointments.length ?? 0;
  const quickActionsAvailable = capabilitiesLoaded && (
    capabilities.can_create_appointment
    || capabilities.can_create_patient
    || capabilities.can_open_clinical_context
    || capabilities.can_pay
  );

  const refreshAfterPatientMutation = () => {
    void actions.fetchPatients();
    void actions.fetchSnapshot();
    void refreshCapabilities();
  };

  const selectNavTab = (tab: typeof state.activeTab) => {
    setQuickActionsOpen(false);
    actions.setActiveTab(tab);
  };

  return (
    <div
      data-dc-mobile-shell
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
        fetchSnapshot={actions.fetchSnapshot}
        totalCount={totalCount}
        termineCount={termineCount}
        queuedActionsCount={state.queuedActionsCount}
        onOpenPatients={() => selectNavTab('patients')}
      />

      {state.error && state.syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-amber-500/5 border border-amber-200 rounded-[16px] flex items-center gap-3 relative z-10 shadow-sm">
          <WifiOff size={14} className="text-amber-500 shrink-0" />
          <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest">{state.error}</p>
        </div>
      )}

      <div className="relative z-10 mt-2">
        <PWAInstallPrompt />
      </div>

      <main ref={mainRef} className="flex-1 px-6 overflow-x-hidden overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={state.activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="h-full"
          >
            {state.activeTab === 'agenda' && (
              <AgendaView
                snapshot={state.snapshot}
                syncStatus={state.syncStatus}
                selectedDate={state.selectedDate}
                setSelectedDate={actions.setSelectedDate}
                patients={state.patients}
                onStatusChange={actions.handleStatusChange}
                onRescheduleAppt={actions.handleRescheduleAppt}
                openApptWhatsApp={actions.openApptWhatsApp}
                handleDeleteAppt={actions.handleDeleteAppt}
                handleOpenSignature={actions.handleOpenSignature}
                onRefresh={actions.fetchSnapshot}
                onPatientCreated={() => actions.fetchPatients()}
              />
            )}
            {state.activeTab === 'patients' && (
              <MobilePatientsGate
                isOnline={state.isOnline}
                onClose={() => selectNavTab('agenda')}
              />
            )}
            {state.activeTab === 'lab' && (
              <LabView
                labJobs={state.labJobs}
                handleWhatsAppSend={actions.handleWhatsAppSend}
              />
            )}
            {state.activeTab === 'finance' && (
              <FinanceView
                snapshot={state.snapshot}
                syncStatus={state.syncStatus}
                selectedDate={state.selectedDate}
                openWhatsApp={actions.openWhatsApp}
                handleExportPDF={actions.handleExportPDF}
              />
            )}
            {state.activeTab === 'securite' && (
              <SecuriteView
                snapshot={state.snapshot}
                syncStatus={state.syncStatus}
                isOnline={state.isOnline}
                handleLogout={actions.handleLogout}
              />
            )}
            {state.activeTab === 'dentists' && <DentistsView embedded />}
            {state.activeTab === 'frontdesk' && <FrontdeskView />}
            {state.activeTab === 'bot' && <BotView />}
          </motion.div>
        </AnimatePresence>
      </main>

      <MobileQuickActionHub
        capabilities={capabilities}
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
        labJobs={state.labJobs}
        snapshot={state.snapshot}
        quickActionsAvailable={quickActionsAvailable}
        quickActionsOpen={quickActionsOpen}
        onToggleQuickActions={() => setQuickActionsOpen(value => !value)}
      />

      {showQuickAppointment && (
        <AddApptModal
          selectedDate={state.selectedDate}
          patients={state.patients}
          onClose={() => setShowQuickAppointment(false)}
          onSuccess={() => {
            void actions.fetchSnapshot();
            setShowQuickAppointment(false);
          }}
          onPatientCreated={() => refreshAfterPatientMutation()}
        />
      )}

      {showQuickNewPatient && (
        <MobileQuickNewPatientModal
          onClose={() => setShowQuickNewPatient(false)}
          onCreated={refreshAfterPatientMutation}
        />
      )}

      {quickPatientAction && (
        <MobileQuickPatientFlow
          action={quickPatientAction}
          onClose={() => setQuickPatientAction(null)}
          onPaymentRecorded={() => void actions.fetchSnapshot()}
        />
      )}

      {state.whatsappApt && (
        <WhatsAppModal
          whatsappTemplate={state.whatsappTemplate}
          setWhatsappTemplate={actions.setWhatsappTemplate}
          customMessage={state.customMessage}
          setCustomMessage={actions.setCustomMessage}
          onCancel={() => actions.setWhatsappApt(null)}
          onSend={actions.handleSendWhatsApp}
        />
      )}

      {state.sigPatientId && (
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