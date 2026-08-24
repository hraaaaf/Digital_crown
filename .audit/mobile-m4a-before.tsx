import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './index.css';
import { PatientDetails } from './features/patients/PatientDetailsInner';
import { MobileDashboard } from './features/mobile/Dashboard/MobileDashboard';
import { MobileStorage } from './services/zka/MobileStorage';
import { useAuthStore } from './stores/useAuthStore';

const params = new URLSearchParams(window.location.search);
const view = params.get('view') || 'patient';
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

useAuthStore.setState({
  user: ({
    id: 1,
    email: 'dentiste@m4a-before.local',
    nom_complet: 'Dr M4A',
    role: 'ADMIN',
    employer_id: null,
    is_superadmin: false,
    permissions: { patients: true, agenda: true, clinical: true, accounting: true, payments: true, panoramic: true, cephalo: true },
  } as any),
  isAuthenticated: true,
  isLoading: false,
  error: null,
});

if (view === 'mobile') {
  await MobileStorage.clearAll().catch(() => {});
  await MobileStorage.saveCredentials({
    publicId: 'abcdef1234567890',
    masterKey: 'a'.repeat(64),
    access_token: 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjQxMDI0NDQ4MDB9.',
    refresh_token: 'm4a-before-refresh',
    device_id: '11111111-2222-4333-8444-555555555555',
    api_base_url: 'http://127.0.0.1:8005',
  });
}

const entry = view === 'mobile' ? '/mobile/dashboard?tab=agenda' : '/patients/42';
const node = view === 'mobile' ? (
  <Routes><Route path="/mobile/dashboard" element={<MobileDashboard />} /></Routes>
) : (
  <Routes><Route path="/patients/:id" element={<PatientDetails />} /></Routes>
);

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry]}>{node}</MemoryRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
