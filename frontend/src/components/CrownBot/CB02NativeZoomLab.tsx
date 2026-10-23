// Independent CB-02 source-only accessibility lab. NOT imported by app.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { CrownBotGuidedNluCb02 } from './CrownBotGuidedNluCb02';
import '../../index.css';

if (import.meta.env.VITE_CB02_NATIVE_A11Y_LAB !== 'true'
    || location.hostname !== '127.0.0.1'
    || location.pathname !== '/cb02-native-zoom-lab.html') {
  throw new Error('REFUSED: CB-02 native lab only permitted on opt-in loopback');
}
const root = document.getElementById('root');
if (!root) throw new Error('CB-02 lab root missing');
createRoot(root).render(
  <React.StrictMode>
    <main className="flex min-h-screen min-w-0 flex-col gap-3 bg-slate-50 p-3 text-slate-900">
      <h1 className="text-lg font-bold">CB-02 — laboratoire synthétique</h1>
      <p className="text-xs">Données fictives. Vérification de syntaxe sans exécution.</p>
      <div data-cb02-native-lab-panel className="w-full max-w-[590px] min-w-0">
        <CrownBotGuidedNluCb02 />
      </div>
    </main>
  </React.StrictMode>,
);
