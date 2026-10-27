// Isolated loopback visual test only. Never imported by the clinic app.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { CrownBotGuidedActionsG3 } from './CrownBotGuidedActionsG3';
import '../../index.css';

if (import.meta.env.VITE_CB03_G3_VISUAL_LAB !== 'true'
    || import.meta.env.VITE_CROWN_BOT_CB03_G3_ENABLED !== 'true'
    || location.hostname !== '127.0.0.1'
    || location.pathname !== '/cb03-g3-visual-lab.html') {
  throw new Error('REFUSED: CB-03 G3 synthetic lab requires explicit local-only opt-in');
}
const root = document.getElementById('root');
if (!root) throw new Error('CB-03 G3 visual lab root missing');
createRoot(root).render(
  <React.StrictMode>
    <main className="mx-auto flex min-h-screen w-full min-w-0 max-w-3xl flex-col gap-3 bg-slate-50 p-3 text-slate-900">
      <h1 className="text-lg font-bold">Crown Bot CB-03 G3 — laboratoire synthétique</h1>
      <p className="text-xs">Données fictives pour la démonstration. Aucun dossier de patient réel n’est utilisé.</p>
      <CrownBotGuidedActionsG3 practitionerId={9} />
    </main>
  </React.StrictMode>,
);
