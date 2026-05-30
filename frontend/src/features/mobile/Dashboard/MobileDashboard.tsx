import { useState } from 'react';
import { WifiOff } from 'lucide-react';
import { useMobileDashboard } from './hooks/useMobileDashboard';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { WhatsAppModal } from './components/WhatsAppModal';
import { SignatureModal } from './components/SignatureModal';
import { AgendaView } from './views/AgendaView';
import { FinanceView } from './views/FinanceView';
import { SecuriteView } from './views/SecuriteView';
import { LabView } from './views/LabView';
import { CrownBotChat } from '../../../components/CrownBot/CrownBotChat';
import { Bot } from 'lucide-react';

export const MobileDashboard = () => {
  const { state, actions, refs: { mainRef } } = useMobileDashboard();
  const [isBotOpen, setIsBotOpen] = useState(false);

  const termineCount = state.snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = state.snapshot?.appointments.length ?? 0;

  return (
    <div className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit pb-28 select-none relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
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
      />

      {state.error && state.syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-amber-500/5 border border-amber-200 rounded-[16px] flex items-center gap-3 relative z-10 shadow-sm">
          <WifiOff size={14} className="text-amber-500 shrink-0" />
          <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest">{state.error}</p>
        </div>
      )}

      <main ref={mainRef} className="flex-1 px-6 overflow-y-auto">
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
      </main>

      <MobileBottomNav 
        activeTab={state.activeTab}
        setActiveTab={actions.setActiveTab}
        totalCount={totalCount}
        termineCount={termineCount}
        labJobs={state.labJobs}
        snapshot={state.snapshot}
      />

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

      {/* Bouton Flottant Crown Bot */}
      <div className="fixed bottom-28 left-6 z-40">
        <button onClick={() => setIsBotOpen(true)} className="w-14 h-14 bg-gradient-to-tr from-primary to-secondary text-white rounded-full shadow-[0_8px_30px_rgba(var(--primary-rgb),0.5)] flex items-center justify-center hover:scale-105 active:scale-95 transition-transform border border-white/20">
          <Bot size={24} />
        </button>
      </div>

      {/* Overlay Crown Bot */}
      {isBotOpen && (
        <div className="fixed inset-0 z-50 flex flex-col justify-end bg-black/40 backdrop-blur-sm sm:items-center sm:p-6" onClick={() => setIsBotOpen(false)}>
          <div className="w-full h-[85vh] sm:w-[400px] sm:h-[600px] animate-slide-up sm:animate-in sm:fade-in sm:zoom-in" onClick={e => e.stopPropagation()}>
            <CrownBotChat onClose={() => setIsBotOpen(false)} />
          </div>
        </div>
      )}
    </div>
  );
};
