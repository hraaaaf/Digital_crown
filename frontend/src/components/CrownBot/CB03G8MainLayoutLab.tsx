// G8 CI-only entry: actual clinic MainLayout and its genuine CrownBotChat.
// No mock clinical HTTP. Synthetic account, isolated SQLCipher, localhost only.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../../stores/useAuthStore';
import { MainLayout } from '../Layout/MainLayout';
import '../../index.css';

if (import.meta.env.VITE_CB03_G8_MAINLAYOUT_LAB !== 'true'
    || import.meta.env.VITE_CROWN_BOT_CB03_CHAT_ENABLED !== 'true'
    || location.hostname !== '127.0.0.1'
    || location.pathname !== '/cb03-g8-mainlayout-lab.html') {
  throw new Error('REFUSED: G8 CI-only MainLayout needs explicit loopback opt-in');
}
const ownerId = Number(import.meta.env.VITE_CB03_G8_SYNTHETIC_OWNER_ID);
if (!Number.isSafeInteger(ownerId) || ownerId <= 0) {
  throw new Error('REFUSED: invalid synthetic G8 owner ID');
}
useAuthStore.setState({
  user: {id: ownerId, employer_id: ownerId, role: 'DENTISTE', nom_complet: 'G8 Dentist', is_licensed: true} as never,
  isAuthenticated: true,
});
const root = document.getElementById('root');
if (!root) throw new Error('No G8 root');
createRoot(root).render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter initialEntries={['/dashboard']}>
      <MainLayout>
        <section aria-label="Espace clinique synthétique G8" data-cb03-g8-workspace>
          <h1>Cabinet synthétique — certification MainLayout</h1>
          <p>Patient fictif. Les demandes sont traitées dans un environnement d’essai avec une base chiffrée temporaire.</p>
        </section>
      </MainLayout>
    </MemoryRouter>
  </QueryClientProvider>
);
