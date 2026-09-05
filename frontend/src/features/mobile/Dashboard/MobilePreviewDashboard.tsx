import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { MobileQuickActionHub } from './components/MobileQuickActionHub';
import './components/mobileQuickActionHub.css';
import { AgendaView } from './views/AgendaView';
import { FinanceView } from './views/FinanceView';
import { LabView } from './views/LabView';
import { MobilePatientsView, type MobilePatientsPreviewData } from './views/MobilePatientsView';
import { MobilePreviewBotView } from './MobilePreviewBotView';
import { MobilePreviewSecurityView } from './MobilePreviewSecurityView';
import { applyMobileRuntimeTheme } from './hooks/useMobileRuntimeTheme';
import { LabJobStatus, type LabJob } from '../../../types/labJob';
import type { Appointment, Snapshot, Tab } from './types';

const DEMO_PATIENTS = [
  { id: 101, name: 'Patient 01', phone: '+212600000001' },
  { id: 102, name: 'Patient 02', phone: '+212600000002' },
  { id: 103, name: 'Patient 03', phone: null },
  { id: 104, name: 'Patient 04', phone: null },
];

const DEMO_QUICK_CAPABILITIES = {
  can_create_appointment: true,
  can_create_patient: true,
  can_open_clinical_context: true,
  can_pay: true,
};

function isoDay(offset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

function buildSnapshot(selectedDate: string): Snapshot {
  return {
    generated_at: new Date().toISOString(),
    role: 'DENTISTE',
    is_superadmin: false,
    appointments: [
      { id: 9101, patient_id: 101, time: '09:00', date: selectedDate, patient_name: 'Patient 01', phone: null, motif: 'Contrôle ortho', status: 'TERMINE', duration_minutes: 30 },
      { id: 9102, patient_id: 102, time: '10:15', date: selectedDate, patient_name: 'Patient 02', phone: null, motif: 'Endodontie 16', status: 'EN_COURS', duration_minutes: 45 },
      { id: 9103, patient_id: 103, time: '11:30', date: selectedDate, patient_name: 'Patient 03', phone: null, motif: 'Empreinte', status: 'PLANIFIE', duration_minutes: 30 },
      { id: 9104, patient_id: 104, time: '14:00', date: selectedDate, patient_name: 'Patient 04', phone: null, motif: 'Couronne 26', status: 'PLANIFIE', duration_minutes: 45 },
    ],
    finance: {
      today_revenue: 7850,
      month_revenue: 126400,
      month_variation: 8.2,
      appointments_count: 84,
      weekly_revenue: [
        { date: isoDay(-6), amount: 9400 },
        { date: isoDay(-5), amount: 12100 },
        { date: isoDay(-4), amount: 8300 },
        { date: isoDay(-3), amount: 14750 },
        { date: isoDay(-2), amount: 10900 },
        { date: isoDay(-1), amount: 13600 },
        { date: isoDay(0), amount: 7850 },
      ],
      total_patients: 642,
      total_debt: 12750,
    },
    debtors: [
      { id: 201, name: 'Patient Démo A', amount: 4200, phone: null },
      { id: 202, name: 'Patient Démo B', amount: 2500, phone: null },
    ],
  };
}

const DEMO_PATIENT_COCKPIT: MobilePatientsPreviewData = {
  initialSelectedId: 101,
  results: [
    { id: 101, name: 'Patient Démo A', phone: '+212600000001', numero_dossier: 'P-0101', has_medical_alert: true },
    { id: 102, name: 'Patient Démo B', phone: '+212600000002', numero_dossier: 'P-0102', has_medical_alert: false },
    { id: 103, name: 'Patient Démo C', phone: null, numero_dossier: 'P-0103', has_medical_alert: false },
  ],
  cockpit: {
    patient: {
      id: 101,
      name: 'Patient Démo A',
      prenom: 'Patient',
      nom: 'Démo A',
      numero_dossier: 'P-0101',
      date_naissance: '1988-03-18T00:00:00',
      phone: '+212600000001',
      assurance: 'CNSS',
      has_medical_alert: true,
      medical_alert_summary: 'Allergie médicamenteuse renseignée dans le dossier.',
    },
    next_appointment: {
      id: 9201,
      datetime_start: `${isoDay(2)}T10:30:00`,
      duration_minutes: 45,
      motif: 'Contrôle clinique',
      status: 'PRÉVU',
    },
    finance: {
      has_billing_data: true,
      remaining_due: 1250,
      total_collected: 4100,
      overdue_count: 1,
    },
  },
  resources: {
    documents: [
      {
        id: 9301,
        label: 'Consentement implantologie',
        document_type: 'CONSENTEMENT',
        created_at: `${isoDay(-3)}T11:20:00`,
      },
    ],
    panoramics: [
      {
        id: 9401,
        label: 'Panoramique #9401',
        created_at: `${isoDay(-7)}T09:15:00`,
      },
    ],
  },
};

const DEMO_LAB_JOBS: LabJob[] = [
  {
    id: 7001,
    patient_id: 101,
    act_id: 8001,
    material: 'Zircone',
    shade: 'A2',
    type: 'Couronne',
    tooth_number: '26',
    notes: 'Données fictives Preview',
    deadline: isoDay(3),
    status: LabJobStatus.PRESCRIPTION,
    is_remake: false,
    is_late: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 7002,
    patient_id: 103,
    act_id: 8002,
    material: 'Disilicate',
    shade: 'B1',
    type: 'Facette',
    tooth_number: '11',
    notes: 'Données fictives Preview',
    deadline: isoDay(5),
    status: LabJobStatus.PRESCRIPTION,
    is_remake: false,
    is_late: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const noop = () => undefined;

function requestedPreviewTab(): Tab {
  const tab = new URLSearchParams(window.location.search).get('tab');
  return tab === 'patients' ? 'patients' : 'agenda';
}

function requestedQuickOpen(): boolean {
  return new URLSearchParams(window.location.search).get('quick') === '1';
}

export function MobilePreviewDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>(requestedPreviewTab);
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));
  const mainRef = useRef<HTMLElement>(null);
  const snapshot = useMemo(() => buildSnapshot(selectedDate), [selectedDate]);
  const totalCount = snapshot.appointments.length;
  const termineCount = snapshot.appointments.filter(appointment => appointment.status === 'TERMINE').length;

  useEffect(() => {
    applyMobileRuntimeTheme({
      selected_theme: 'elite',
      primary_color: '#003380',
      secondary_color: '#1e40af',
      accent_color: '#60a5fa',
      app_accent_color: null,
      font_fr: 'inter',
    });
  }, []);

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
  }, [activeTab]);

  return (
    <div
      data-dc-mobile-shell
      data-dc-preview-demo
      data-mob3-quick-action-shell
      className="min-h-[100dvh] bg-background text-text-main flex flex-col pb-28 select-none relative"
      style={{
        backgroundColor: 'var(--bg-medical-pearl)',
        fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
      }}
    >
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />

      <MobileHeader
        activeTab={activeTab}
        syncStatus="error"
        snapshot={snapshot}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        fetchSnapshot={noop}
        totalCount={totalCount}
        termineCount={termineCount}
        queuedActionsCount={0}
        previewMode
      />

      <div className="mx-6 mb-4 px-4 py-3 rounded-[18px] border border-primary/15 bg-primary/5 relative z-10 shadow-sm">
        <p className="text-[9px] font-black text-primary uppercase tracking-[0.16em]">MODE DÉMO — PREVIEW LOCALE</p>
        <p className="mt-1 text-[10px] font-bold text-text-muted">Aucune donnée cabinet • aucune session réelle</p>
      </div>

      <main ref={mainRef} className="flex-1 px-6 overflow-x-hidden overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="h-full"
          >
            {activeTab === 'agenda' && (
              <div className="pointer-events-none" aria-label="Agenda de démonstration en lecture seule">
                <AgendaView
                  snapshot={snapshot}
                  syncStatus="success"
                  selectedDate={selectedDate}
                  setSelectedDate={setSelectedDate}
                  patients={DEMO_PATIENTS}
                  onStatusChange={noop}
                  onRescheduleAppt={noop}
                  openApptWhatsApp={noop as (appointment: Appointment) => void}
                  handleDeleteAppt={noop}
                  handleOpenSignature={noop}
                  onRefresh={noop}
                  onPatientCreated={noop}
                />
              </div>
            )}
            {activeTab === 'patients' && (
              <MobilePatientsView
                onClose={() => setActiveTab('agenda')}
                previewData={DEMO_PATIENT_COCKPIT}
              />
            )}
            {activeTab === 'finance' && (
              <FinanceView
                snapshot={snapshot}
                syncStatus="success"
                selectedDate={selectedDate}
                openWhatsApp={noop}
                handleExportPDF={noop}
              />
            )}
            {activeTab === 'lab' && (
              <LabView labJobs={DEMO_LAB_JOBS} handleWhatsAppSend={noop} />
            )}
            {activeTab === 'bot' && <MobilePreviewBotView />}
            {activeTab === 'securite' && <MobilePreviewSecurityView />}
          </motion.div>
        </AnimatePresence>
      </main>

      <MobileQuickActionHub
        capabilities={DEMO_QUICK_CAPABILITIES}
        isOnline
        defaultOpen={requestedQuickOpen()}
        onNewAppointment={noop}
        onNewPatient={noop}
        onPatientAction={() => undefined}
      />

      <MobileBottomNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        totalCount={totalCount}
        termineCount={termineCount}
        labJobs={DEMO_LAB_JOBS}
        snapshot={snapshot}
      />
    </div>
  );
}
