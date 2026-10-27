// CB2 G6 loopback-only lab mounts REAL MainLayout, including its REAL launcher.
// The surrounding page and API fixtures are synthetic; no clinical deployment.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { MainLayout } from '../Layout/MainLayout';
import { useAuthStore } from '../../stores/useAuthStore';
import '../../index.css';
if(import.meta.env.VITE_CB03_G6_MAINLAYOUT_LAB!=='true'
  ||import.meta.env.VITE_CROWN_BOT_CB03_CHAT_ENABLED!=='true'
  ||location.hostname!=='127.0.0.1'
  ||location.pathname!=='/cb03-g6-mainlayout-lab.html'){
  throw new Error('REFUSED: exact loopback and G6 opt-in required');
}
const owner=Number(import.meta.env.VITE_CB03_G5_LAB_PRACTITIONER_ID||'9');
if(!Number.isSafeInteger(owner)||owner<1)throw new Error('REFUSED: invalid synthetic owner');
useAuthStore.setState({user:{id:owner,employer_id:owner,role:'DENTISTE',
  nom_complet:'Praticien fictif G6',permissions:{patients:true,agenda:true,
    accounting:true,settings:true}} as never,isAuthenticated:true});
const node=document.getElementById('root');
if(!node)throw new Error('Missing G6 root');
createRoot(node).render(<MemoryRouter initialEntries={['/cb03-g6-mainlayout-lab.html']}>
  <MainLayout><div className="rounded-xl bg-white p-5 text-slate-900" data-g6-isolated-dashboard>
    <h1 className="text-lg font-bold">Banc Crown Bot 2.0 · MainLayout réel</h1>
    <p className="text-sm">Espace de démonstration sans patient réel. Le lanceur Crown Bot en bas à droite est celui du vrai MainLayout.</p>
  </div></MainLayout>
</MemoryRouter>);
