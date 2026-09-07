import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { MobileHeader } from './components/MobileHeader';
import { MobileBottomNav } from './components/MobileBottomNav';
import { MobileQuickActionHub } from './components/MobileQuickActionHub';
import './components/mobileQuickActionHub.css';
import { AgendaView } from './views/AgendaView';
import { WaitingRoomView } from './views/WaitingRoomView';
import { FinanceView } from './views/FinanceView';
import { LabView } from './views/LabView';
import { MobilePatientsView, type MobilePatientsPreviewData } from './views/MobilePatientsView';
import { FrontdeskView, type PendingRequest } from './views/FrontdeskView';
import { NotificationsView, type MobileAlert } from './views/NotificationsView';
import { StockView, type MobileStockItem } from './views/StockView';
import { LibraryView } from './views/LibraryView';
import { MarketplaceView } from './views/MarketplaceView';
import { MobilePreviewBotView } from './MobilePreviewBotView';
import { MobilePreviewSecurityView } from './MobilePreviewSecurityView';
import { applyMobileRuntimeTheme } from './hooks/useMobileRuntimeTheme';
import { LabJobStatus, type LabJob } from '../../../types/labJob';
import type { MarketplacePreviewData } from '../../partnerMarketplace/usePartnerMarketplace';
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
    generated_at: new Date().toISOString(), role: 'DENTISTE', is_superadmin: false,
    appointments: [
      { id: 9101, patient_id: 101, time: '09:00', date: selectedDate, patient_name: 'Patient 01', phone: null, motif: 'Contrôle ortho', status: 'TERMINE', duration_minutes: 30 },
      { id: 9102, patient_id: 102, time: '10:15', date: selectedDate, patient_name: 'Patient 02', phone: null, motif: 'Endodontie 16', status: 'EN_COURS', duration_minutes: 45 },
      { id: 9103, patient_id: 103, time: '11:30', date: selectedDate, patient_name: 'Patient 03', phone: null, motif: 'Empreinte', status: 'EN_ATTENTE', duration_minutes: 30, ticket_number: 12 },
      { id: 9104, patient_id: 104, time: '14:00', date: selectedDate, patient_name: 'Patient 04', phone: null, motif: 'Couronne 26', status: 'PLANIFIE', duration_minutes: 45 },
    ],
    finance: { today_revenue: 7850, month_revenue: 126400, month_variation: 8.2, appointments_count: 84, weekly_revenue: [], total_patients: 642, total_debt: 12750 },
    debtors: [],
  };
}

const DEMO_PATIENT_COCKPIT: MobilePatientsPreviewData = {
  initialSelectedId: 101,
  results: [
    { id: 101, name: 'Patient Démo A', phone: '+212600000001', numero_dossier: 'P-0101', has_medical_alert: true },
    { id: 102, name: 'Patient Démo B', phone: '+212600000002', numero_dossier: 'P-0102', has_medical_alert: false },
  ],
  cockpit: {
    patient: { id: 101, name: 'Patient Démo A', prenom: 'Patient', nom: 'Démo A', numero_dossier: 'P-0101', date_naissance: '1988-03-18T00:00:00', phone: '+212600000001', assurance: 'CNSS', has_medical_alert: true, medical_alert_summary: 'Allergie médicamenteuse renseignée dans le dossier.' },
    next_appointment: { id: 9201, datetime_start: `${isoDay(2)}T10:30:00`, duration_minutes: 45, motif: 'Contrôle clinique', status: 'PRÉVU' },
    finance: { has_billing_data: true, remaining_due: 1250, total_collected: 4100, overdue_count: 1 },
  },
  resources: { documents: [], panoramics: [] },
};

const DEMO_LAB_JOBS: LabJob[] = [{ id: 7001, patient_id: 101, act_id: 8001, material: 'Zircone', shade: 'A2', type: 'Couronne', tooth_number: '26', notes: 'Données fictives Preview', deadline: isoDay(3), status: LabJobStatus.PRESCRIPTION, is_remake: false, is_late: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }];

const DEMO_FRONTDESK: PendingRequest[] = [
  { id: 8101, patient_name: 'Nadia El Mansouri', phone: '+212612345678', datetime_start: `${isoDay(0)}T15:30:00`, duration_minutes: 30, motif: 'Douleur molaire', status: 'EN_ATTENTE_DEMANDE', source: 'frontdesk', expires_at: `${isoDay(0)}T16:00:00`, created_at: new Date().toISOString() },
  { id: 8102, patient_name: 'Youssef Amrani', phone: '+212623456789', datetime_start: `${isoDay(1)}T10:00:00`, duration_minutes: 45, motif: 'Contrôle implant', status: 'EN_ATTENTE_CONFIRM', source: 'frontdesk', expires_at: `${isoDay(0)}T17:30:00`, created_at: new Date().toISOString() },
];

const DEMO_NOTIFICATIONS: MobileAlert[] = [
  { id: 8201, patient_id: 101, patient_name: 'Nadia El Mansouri', type: 'OVERDUE_PAYMENT', title: 'Paiement à régulariser', message: 'Un règlement patient nécessite une vérification aujourd’hui.', priority: 'HIGH', created_at: new Date(Date.now() - 12 * 60_000).toISOString() },
  { id: 8202, patient_id: 102, patient_name: 'Youssef Amrani', type: 'PATIENT_FOLLOWUP', title: 'Suivi clinique', message: 'Le contrôle prévu cette semaine mérite une vérification du dossier.', priority: 'MEDIUM', created_at: new Date(Date.now() - 75 * 60_000).toISOString() },
  { id: 8203, patient_id: 103, patient_name: 'Salma Idrissi', type: 'PATIENT_INFO', title: 'Information patient', message: 'Une information non urgente est disponible dans le dossier.', priority: 'LOW', created_at: new Date(Date.now() - 26 * 60 * 60_000).toISOString() },
];

const DEMO_STOCK: MobileStockItem[] = [
  { id: 8301, nom: 'Gants nitrile M', categorie: 'CONSOMMABLE', quantite: 0, seuil_alerte: 4, unite: 'boîtes', fournisseur: 'Fournisseur démo', alerte: true },
  { id: 8302, nom: 'Composite universel', categorie: 'MATERIAU', quantite: 2, seuil_alerte: 3, unite: 'seringues', fournisseur: null, alerte: true },
  { id: 8303, nom: 'Anesthésique local', categorie: 'MEDICAMENT', quantite: 8, seuil_alerte: 4, unite: 'boîtes', fournisseur: null, alerte: false },
  { id: 8304, nom: 'Masques chirurgicaux', categorie: 'CONSOMMABLE', quantite: 12, seuil_alerte: 5, unite: 'boîtes', fournisseur: null, alerte: false },
];

const DEMO_MARKETPLACE: MarketplacePreviewData = {
  strategyPresets: [{ key: 'sent_commission_10', label: 'Commission sur commande envoyée', settlementBasis: 'SENT_TO_PARTNER', revenueModel: 'COMMISSION_PERCENT', commissionRate: 10, discountRate: 0, fixedFeeAmount: 0, description: 'Démonstration' }],
  catalogMeta: { categories: ['Consommables', 'Restauration', 'Endodontie'], specialties: ['Omnipratique', 'Endodontie'], availability: ['AVAILABLE', 'ON_REQUEST', 'DISCONTINUED'] },
  suppliers: [{ id: 11, supplierKey: 'preview-dental', name: 'Preview Dental Supply', badge: 'Démo', description: 'Catalogue fictif', promise: 'Aucune donnée réelle', apiBaseUrl: null, syncMode: 'manual', isActive: true, productCount: 4 }],
  products: [
    { id: '101', supplierId: '11', supplierName: 'Preview Dental Supply', name: 'Composite universel nano-hybride', category: 'Restauration', specialty: 'Omnipratique', sku: 'CMP-NH-01', unit: 'seringue', price: 390, availability: 'Disponible', description: 'Composite universel de démonstration.', longDescription: 'Donnée fictive.', benefits: [], isFeatured: true, sortOrder: 1 },
    { id: '102', supplierId: '11', supplierName: 'Preview Dental Supply', name: 'Limes rotatives NiTi', category: 'Endodontie', specialty: 'Endodontie', sku: 'ENDO-NITI', unit: 'blister', price: 295, availability: 'Disponible', description: 'Limes de démonstration.', longDescription: 'Donnée fictive.', benefits: [], isFeatured: true, sortOrder: 2 },
    { id: '103', supplierId: '11', supplierName: 'Preview Dental Supply', name: 'Gants nitrile premium', category: 'Consommables', specialty: 'Omnipratique', sku: 'NIT-PRO-M', unit: 'boîte', price: 78, availability: 'Disponible', description: 'Gants de démonstration.', longDescription: 'Donnée fictive.', benefits: [], isFeatured: false, sortOrder: 3 },
    { id: '104', supplierId: '11', supplierName: 'Preview Dental Supply', name: 'Ciment verre ionomère', category: 'Restauration', specialty: 'Omnipratique', sku: 'CVI-09', unit: 'kit', price: 520, availability: 'Sur commande', description: 'Kit de démonstration.', longDescription: 'Donnée fictive.', benefits: [], isFeatured: false, sortOrder: 4 },
  ],
  customer: { fullName: 'Dr Baseline', clinic: 'Cabinet Atlas', email: 'baseline@digitalcrown.local', phone: '0600000000', city: 'Rabat' },
};

const noop = () => undefined;

function requestedPreviewTab(): Tab {
  const tab = new URLSearchParams(window.location.search).get('tab') as Tab | null;
  return tab && ['agenda', 'waiting-room', 'patients', 'finance', 'lab', 'bot', 'securite', 'dentists', 'frontdesk', 'notifications', 'stock', 'library', 'marketplace'].includes(tab) ? tab : 'agenda';
}

function requestedQuickOpen(): boolean { return new URLSearchParams(window.location.search).get('quick') === '1'; }

export function MobilePreviewDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>(requestedPreviewTab);
  const [quickActionsOpen, setQuickActionsOpen] = useState(requestedQuickOpen);
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));
  const mainRef = useRef<HTMLElement>(null);
  const snapshot = useMemo(() => buildSnapshot(selectedDate), [selectedDate]);
  const totalCount = snapshot.appointments.length;
  const termineCount = snapshot.appointments.filter(appointment => appointment.status === 'TERMINE').length;

  useEffect(() => { applyMobileRuntimeTheme({ selected_theme: 'elite', primary_color: '#003380', secondary_color: '#1e40af', accent_color: '#60a5fa', app_accent_color: null, font_fr: 'inter' }); }, []);
  useEffect(() => { mainRef.current?.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior }); }, [activeTab]);
  const selectNavTab = (tab: Tab) => { setQuickActionsOpen(false); setActiveTab(tab); };

  return (
    <div data-dc-mobile-shell data-dc-preview-demo data-mob3-quick-action-shell className="min-h-[100dvh] bg-background text-text-main flex flex-col pb-28 select-none relative" style={{ backgroundColor: 'var(--bg-medical-pearl)', fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)' }}>
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />
      <MobileHeader activeTab={activeTab} syncStatus="error" snapshot={snapshot} selectedDate={selectedDate} setSelectedDate={setSelectedDate} fetchSnapshot={noop} totalCount={totalCount} termineCount={termineCount} queuedActionsCount={0} onOpenPatients={() => selectNavTab('patients')} previewMode />
      <div className="mx-6 mb-4 px-4 py-3 rounded-[18px] border border-primary/15 bg-primary/5 relative z-10 shadow-sm"><p className="text-[9px] font-black text-primary uppercase tracking-[0.16em]">MODE DÉMO — PREVIEW LOCALE</p><p className="mt-1 text-[10px] font-bold text-text-muted">Aucune donnée cabinet • aucune session réelle</p></div>
      <main ref={mainRef} className="flex-1 px-6 overflow-x-hidden overflow-y-auto">
        <AnimatePresence mode="wait"><motion.div key={activeTab} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2, ease: 'easeOut' }} className="h-full">
          {activeTab === 'agenda' && <div className="pointer-events-none" aria-label="Agenda de démonstration en lecture seule"><AgendaView snapshot={snapshot} syncStatus="success" selectedDate={selectedDate} setSelectedDate={setSelectedDate} patients={DEMO_PATIENTS} onStatusChange={noop} onRescheduleAppt={noop} openApptWhatsApp={noop as (appointment: Appointment) => void} handleDeleteAppt={noop} handleOpenSignature={noop} onRefresh={noop} onPatientCreated={noop} /></div>}
          {activeTab === 'waiting-room' && <WaitingRoomView snapshot={snapshot} onStatusChange={noop} />}
          {activeTab === 'patients' && <MobilePatientsView onClose={() => selectNavTab('agenda')} previewData={DEMO_PATIENT_COCKPIT} />}
          {activeTab === 'finance' && <FinanceView snapshot={snapshot} syncStatus="success" selectedDate={selectedDate} openWhatsApp={noop} handleExportPDF={noop} />}
          {activeTab === 'lab' && <LabView labJobs={DEMO_LAB_JOBS} handleWhatsAppSend={noop} />}
          {activeTab === 'frontdesk' && <FrontdeskView previewData={DEMO_FRONTDESK} />}
          {activeTab === 'notifications' && <NotificationsView onNavigate={selectNavTab} previewData={DEMO_NOTIFICATIONS} />}
          {activeTab === 'stock' && <StockView previewData={DEMO_STOCK} />}
          {activeTab === 'library' && <LibraryView role="DENTISTE" />}
          {activeTab === 'marketplace' && <MarketplaceView previewData={DEMO_MARKETPLACE} />}
          {activeTab === 'bot' && <MobilePreviewBotView />}
          {activeTab === 'securite' && <MobilePreviewSecurityView />}
        </motion.div></AnimatePresence>
      </main>
      <MobileQuickActionHub capabilities={DEMO_QUICK_CAPABILITIES} isOnline open={quickActionsOpen} onOpenChange={setQuickActionsOpen} hideLauncher onNewAppointment={noop} onNewPatient={noop} onPatientAction={() => undefined} />
      <MobileBottomNav activeTab={activeTab} setActiveTab={selectNavTab} totalCount={totalCount} termineCount={termineCount} labJobs={DEMO_LAB_JOBS} snapshot={snapshot} quickActionsAvailable quickActionsOpen={quickActionsOpen} onToggleQuickActions={() => setQuickActionsOpen(value => !value)} />
    </div>
  );
}