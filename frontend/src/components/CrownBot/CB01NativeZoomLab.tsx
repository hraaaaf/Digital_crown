// CB-01 laboratory-only entrypoint. Not imported from the production App.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CrownBotChat } from './CrownBotChat';
import { useAuthStore } from '../../stores/useAuthStore';
import '../../index.css';

if (import.meta.env.VITE_CB01_NATIVE_A11Y_LAB !== 'true'
  || location.hostname !== '127.0.0.1'
  || location.pathname !== '/cb01-native-zoom-lab.html') {
  throw new Error('REFUSED: CB-01 laboratory route requires explicit opt-in and loopback');
}

// Synthetic staff identity: no token, session persistence, or real patient data.
useAuthStore.setState({
  user: {
    id: 990001,
    employer_id: 990001,
    role: 'SECRETAIRE',
    nom: 'TEST',
    prenom: 'SYNTHETIQUE',
  } as never,
  isAuthenticated: true,
  isLoading: false,
});

const host = document.getElementById('root');
if (!host) throw new Error('Missing CB-01 lab root');
createRoot(host).render(
  <React.StrictMode>
    <MemoryRouter initialEntries={['/agenda']}>
      <div className="flex h-screen min-w-0 overflow-hidden bg-slate-50 text-slate-900">
        <main className="flex min-w-0 flex-1 flex-col p-4" aria-label="Espace cabinet synthétique">
          <h1 className="text-lg font-bold">Digital Crown — laboratoire isolé</h1>
          <p className="text-sm">Aucune donnée réelle. Aucun acte exécutable.</p>
        </main>
        <aside data-cb01-native-lab-panel="true"
          className="fixed inset-x-2 bottom-2 top-2 min-w-0 sm:left-auto sm:right-2 sm:top-6 sm:bottom-6 sm:w-[430px] min-[1500px]:static min-[1500px]:w-[480px] min-[1500px]:shrink-0">
          <CrownBotChat />
        </aside>
      </div>
    </MemoryRouter>
  </React.StrictMode>,
);
