import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import './index.css';
import './styles/mobileGlassSystem.css';
import { MobileContext } from './features/mobile/Context/MobileContext';
import { MobileStorage } from './services/zka/MobileStorage';

const jwt = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjQxMDI0NDQ4MDB9.';
await MobileStorage.clearAll().catch(() => {});
await MobileStorage.saveCredentials({
  publicId: 'abcdef1234567890',
  masterKey: 'a'.repeat(64),
  access_token: jwt,
  refresh_token: 'm6-a-before-refresh',
  device_id: '11111111-2222-4333-8444-555555555555',
  api_base_url: 'http://127.0.0.1:8005',
});
await MobileStorage.saveBridgeContext({
  type: 'patient',
  key: 'M6A-Patient',
  label: 'Dossier patient',
  state: 'ready',
  reason: null,
});

createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/mobile/context']}>
    <Routes><Route path="/mobile/context" element={<MobileContext />} /></Routes>
  </MemoryRouter>,
);
