import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import './index.css';
import './styles/mobileGlassSystem.css';
import { MobileHeader } from './features/mobile/Dashboard/components/MobileHeader';
import type { Snapshot } from './features/mobile/Dashboard/types';
import { MobileStorage } from './services/zka/MobileStorage';

const encode = (value: unknown) => btoa(JSON.stringify(value)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
const auditToken = `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ exp: 4102444800 })}.audit`;

await MobileStorage.clearAll();
await MobileStorage.saveCredentials({
  publicId: '0123456789abcdef',
  masterKey: 'a'.repeat(64),
  access_token: auditToken,
  refresh_token: 'audit-refresh-token',
  device_id: '11111111-1111-4111-8111-111111111111',
  api_base_url: 'http://127.0.0.1:4199',
});

const snapshot: Snapshot = {
  generated_at: '2026-08-26T00:00:00',
  role: 'DENTISTE',
  appointments: [
    { id: 1, patient_id: 12, time: '09:00', patient_name: 'PATIENT TEST', phone: null, motif: 'Contrôle', status: 'PLANIFIE', duration_minutes: 30 },
    { id: 2, patient_id: 13, time: '10:30', patient_name: 'PATIENT DEMO', phone: null, motif: 'Consultation', status: 'TERMINE', duration_minutes: 30 },
  ],
  finance: { today_revenue: 0, month_revenue: 0, month_variation: null, appointments_count: 2, weekly_revenue: [], total_patients: 2, total_debt: 0 },
  debtors: [],
};

function AuditApp() {
  return (
    <MemoryRouter>
      <div data-dc-mobile-shell className="min-h-[100dvh] bg-background text-text-main font-outfit relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
        <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />
        <MobileHeader
          activeTab="agenda"
          syncStatus="success"
          snapshot={snapshot}
          selectedDate="2026-08-26"
          setSelectedDate={() => {}}
          fetchSnapshot={() => {}}
          totalCount={2}
          termineCount={1}
          queuedActionsCount={0}
        />
        <main className="relative z-10 px-6 mt-2">
          <div className="rounded-[24px] border border-glass-border bg-card p-5 shadow-elite" style={{ backgroundColor: 'var(--glass-bg)' }}>
            <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Surface audit M6-D2</p>
            <h2 className="mt-2 text-lg font-black text-text-main">Agenda du jour</h2>
            <p className="mt-2 text-xs text-text-muted">Les alertes réelles du cabinet restent dans le centre mobile authentifié.</p>
          </div>
        </main>
      </div>
    </MemoryRouter>
  );
}

createRoot(document.getElementById('root')!).render(<AuditApp />);
