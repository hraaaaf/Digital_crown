import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, useLocation } from 'react-router-dom';
import './index.css';
import { MobileContext } from './features/mobile/Context/MobileContext';
import { MobileStorage } from './services/zka/MobileStorage';

const params = new URLSearchParams(window.location.search);
const mode = params.get('mode') || 'unpaired';
const futureJwt = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJleHAiOjQxMDI0NDQ4MDB9.';

await MobileStorage.clearAll().catch(() => {});
if (mode !== 'unpaired') {
  await MobileStorage.saveCredentials({
    publicId: 'abcdef1234567890',
    masterKey: 'a'.repeat(64),
    access_token: futureJwt,
    refresh_token: 'm4-final-refresh',
    device_id: '11111111-2222-4333-8444-555555555555',
    api_base_url: 'http://127.0.0.1:8005',
  });
  const unavailable = mode === 'revoked';
  await MobileStorage.saveBridgeContext({
    type: 'appointment',
    key: `M4Final-${mode}`,
    label: 'Rendez-vous',
    state: unavailable ? 'unavailable' : 'ready',
    reason: unavailable ? 'Permission agenda révoquée.' : null,
  });
}

function LocationProbe() {
  const location = useLocation();
  return <div data-location-probe className="sr-only">{location.pathname}{location.search}</div>;
}

createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/mobile/context']}>
    <MobileContext />
    <LocationProbe />
  </MemoryRouter>,
);
