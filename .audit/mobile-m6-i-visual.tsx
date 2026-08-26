import React from 'react';
import ReactDOM from 'react-dom/client';
import { SecuriteView } from './features/mobile/Dashboard/views/SecuriteView';
import './index.css';
import './styles/mobileGlassSystem.css';

const snapshot = {
  generated_at: '2026-08-26T09:41:00',
  role: 'DENTISTE',
  is_superadmin: false,
  appointments: [],
  finance: {
    today_revenue: 0, month_revenue: 0, month_variation: 0,
    appointments_count: 0, weekly_revenue: [], total_patients: 42, total_debt: 0,
  },
  debtors: [],
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div data-dc-mobile-shell className="min-h-[100dvh] bg-background text-text-main font-outfit relative overflow-hidden" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />
      <header className="relative z-10 px-6 pt-14 pb-6">
        <h1 className="text-4xl font-black tracking-tight text-primary font-outfit leading-none">Sécurité</h1>
      </header>
      <main className="relative z-10 px-6 pb-12">
        <SecuriteView snapshot={snapshot} syncStatus="success" isOnline={true} handleLogout={() => undefined} />
      </main>
    </div>
  </React.StrictMode>,
);
