import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { AgendaView } from './views/AgendaView';
import { FinanceView } from './views/FinanceView';
import { LabView } from './views/LabView';
import { MobilePreviewBotView } from './MobilePreviewBotView';
import { MobilePreviewSecurityView } from './MobilePreviewSecurityView';
import { LabJobStatus, type LabJob } from '../../../types/labJob';
import type { Appointment, Snapshot, Tab } from './types';

const DEMO_PATIENTS = [
  { id: 101, name: 'Patient 01', phone: null },
  { id: 102, name: 'Patient 02', phone: null },
  { id: 103, name: 'Patient 03', phone: null },
  { id: 104, name: 'Patient 04', phone: null },
];

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

export function MobilePreviewDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));
  const mainRef = useRef<HTMLElement>(null);
  const snapshot = useMemo(() => buildSnapshot(selectedDate), [selectedDate]);
  const totalCount = snapshot.appointments.length;
  const termineCount = snapshot.appointments.filter(appointment => appointment.status === 'TERMINE').length;

  useEffect(() => {
    document.documentElement.dataset.theme = '';
    document.body.dataset.theme = '';
  }, []);

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
  }, [activeTab]);

  return (
    <div data-dc-mobile-shell data-dc-preview-demo className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit pb-28 select-none relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
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
        <p className="text-[9px] font-black text-primary uppercase tracking-[0.16em]">MODE DÉMO — PREVIEW VERCEL</p>
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
