import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import './index.css';
import './styles/mobileGlassSystem.css';
import { MobileDashboard } from './features/mobile/Dashboard/MobileDashboard';
import { OnboardingScanner } from './features/mobile/Onboarding/OnboardingScanner';
import { MobileContext } from './features/mobile/Context/MobileContext';
import { MobileStorage } from './services/zka/MobileStorage';

const params = new URLSearchParams(window.location.search);
const view = params.get('view') || 'dashboard';
const jwt = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjQxMDI0NDQ4MDB9.';

await MobileStorage.clearAll().catch(() => {});
if (view !== 'onboarding') {
  await MobileStorage.saveCredentials({
    publicId: 'abcdef1234567890',
    masterKey: 'a'.repeat(64),
    access_token: jwt,
    refresh_token: 'm6-g0-refresh',
    device_id: '11111111-2222-4333-8444-555555555555',
    api_base_url: 'http://127.0.0.1:8005',
  });
}
if (view === 'context') {
  await MobileStorage.saveBridgeContext({
    type: 'appointment',
    key: 'M6G0-Appointment',
    label: 'Rendez-vous',
    state: 'ready',
    reason: null,
  });
}

const entry = view === 'onboarding'
  ? '/mobile/onboarding'
  : view === 'context'
    ? '/mobile/context'
    : '/mobile/dashboard?tab=agenda';

createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={[entry]}>
    <Routes>
      <Route path="/mobile/onboarding" element={<OnboardingScanner />} />
      <Route path="/mobile/dashboard" element={<MobileDashboard />} />
      <Route path="/mobile/context" element={<MobileContext />} />
    </Routes>
  </MemoryRouter>,
);
