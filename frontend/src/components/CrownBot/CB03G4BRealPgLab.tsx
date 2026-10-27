// G4-B CI ONLY. Production app does not import this file.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { CrownBotGuidedActionsG3 } from './CrownBotGuidedActionsG3';
import '../../index.css';

if (import.meta.env.VITE_CB03_G4B_LIVE_PG_LAB !== 'true'
    || import.meta.env.VITE_CROWN_BOT_CB03_G3_ENABLED !== 'true'
    || location.hostname !== '127.0.0.1'
    || location.pathname !== '/cb03-g4b-live-pg-lab.html') {
  throw new Error('REFUSED: CB-03 G4B real PostgreSQL lab is isolated and opt-in');
}
const element=document.getElementById('root');
if (!element) throw new Error('REFUSED: missing isolated lab root');
createRoot(element).render(
  <React.StrictMode>
    <main className="mx-auto flex min-h-screen w-full min-w-0 max-w-3xl flex-col gap-3 bg-slate-50 p-3 text-slate-900">
      <h1 className="text-lg font-bold">Crown Bot CB-03 G4-B — HTTP réel / PostgreSQL jetable</h1>
      <p className="text-xs">Comptes et dossiers entièrement synthétiques. API FastAPI réelle en local, base PostgreSQL Docker temporaire. Aucun patient réel, aucun backend externe, aucune activité clinique.</p>
      <CrownBotGuidedActionsG3 />
    </main>
  </React.StrictMode>,
);
