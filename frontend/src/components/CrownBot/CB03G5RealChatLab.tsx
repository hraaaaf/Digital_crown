// G5 CI screenshot lab: REAL CrownBotChat component with an isolated
// floating shell, NOT a screenshot of the clinic's MainLayout or live data.
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { CrownBotChat } from './CrownBotChat';
import { useAuthStore } from '../../stores/useAuthStore';
import '../../index.css';

if (import.meta.env.VITE_CB03_G5_CHAT_LAB !== 'true'
    || import.meta.env.VITE_CROWN_BOT_CB03_CHAT_ENABLED !== 'true'
    || location.hostname !== '127.0.0.1'
    || location.pathname !== '/cb03-g5-chat-lab.html') {
  throw new Error('REFUSED: isolated G5 demo needs loopback + explicit CI opt-in');
}
// The PG integration test supplies its freshly minted synthetic owner ID
// through a CI-only Vite variable. It is a UX hint, NEVER authentication.
const labOwner = Number(import.meta.env.VITE_CB03_G5_LAB_PRACTITIONER_ID || '9');
if (!Number.isSafeInteger(labOwner) || labOwner <= 0) {
  throw new Error('REFUSED: invalid synthetic G5 practitioner');
}
useAuthStore.setState({
  // Entirely fictitious account, no patient or real clinic identity.
  user: { id: labOwner, employer_id: labOwner, role: 'DENTISTE' } as never,
  isAuthenticated: true,
});

function SyntheticShell() {
  const [open,setOpen] = useState(false);
  return <div className="min-h-screen bg-slate-100 p-6 text-slate-900">
    <div className="max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-wide text-slate-500">CB-03 G5 · simulation CI isolée</p>
      <h1 className="mt-2 text-xl font-bold">Digital Crown · exemple visuel de la vraie fenêtre conversationnelle</h1>
      <p className="mt-1 text-sm text-slate-600">Le composant intérieur est le vrai CrownBotChat. Le bouton flottant est un cadre de démonstration.
        {import.meta.env.VITE_CB03_G7_REAL_CHAT_SQLCIPHER === 'true'
          ? 'Les demandes sont traitées dans un environnement d’essai avec une base chiffrée temporaire. Aucun patient réel.'
          : import.meta.env.VITE_CB03_G5_REAL_CHAT_PG === 'true'
          ? 'Les demandes sont traitées dans un environnement d’essai avec une base temporaire. Aucun patient réel.'
          : 'Les réponses sont simulées, sans accès à un dossier réel.'}</p>
    </div>
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {open && <div className="h-[min(660px,calc(100vh-115px))] w-[min(420px,calc(100vw-32px))] min-w-0">
        <CrownBotChat onClose={()=>setOpen(false)}/>
      </div>}
      <button type="button" aria-label={open ? 'Fermer CrownBot' : 'Ouvrir CrownBot'}
        onClick={()=>setOpen(v=>!v)}
        className="min-h-12 rounded-full bg-indigo-800 px-6 py-3 text-sm font-bold text-white shadow-lg">
        {open ? 'Fermer Crown Bot' : 'Crown Bot · Ouvrir'}
      </button>
    </div>
  </div>;
}
const root=document.getElementById('root');
if(!root) throw new Error('No G5 lab root');
createRoot(root).render(<MemoryRouter><SyntheticShell/></MemoryRouter>);
