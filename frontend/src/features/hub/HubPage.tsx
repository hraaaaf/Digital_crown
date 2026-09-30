import { useEffect, useState } from 'react';
import { Building2, MonitorCog, TabletSmartphone, ArrowRight, WifiOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_BASE, getRuntimeAuthToken } from '../../services/api';
import { WorkstationModeAdminPanel } from './WorkstationModeAdminPanel';

type HubIdentity = { name: string; type: string; badge: string };

const experienceCards = [
  { id: 'cabinet', title: 'Digital Crown', eyebrow: 'DYNAMIC_MAIN', description: 'Votre espace clinique principal : agenda, patients, soins et gestion.', icon: Building2, route: '/cabinet' },
  { id: 'station', title: "Station d'accueil", eyebrow: 'Accueil', description: "Accueil tactile des patients. Configuration guidée avant mise en service.", icon: TabletSmartphone, route: '/station' },
  { id: 'control', title: 'Centre de contr\u00f4le', eyebrow: 'Technique', description: '\u00c9tat du poste, diagnostic local et configuration technique.', icon: MonitorCog, route: '/control-center' },
] as const;

export const HubPage = () => {
  const navigate = useNavigate();
  const [identity, setIdentity] = useState<HubIdentity>({ name: 'Votre \u00e9tablissement', type: '\u00c9tablissement dentaire', badge: '\u00c9TABLISSEMENT' });
  const [serverAvailable, setServerAvailable] = useState(true);

  useEffect(() => {
    let active = true;
    const loadIdentity = async () => {
      try {
        const token = getRuntimeAuthToken();
        const response = await fetch(`${API_BASE}/api/clinics/me`, {
          credentials: 'include',
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!response.ok) throw new Error(`hub identity ${response.status}`);
        const config = await response.json();
        if (!active) return;
        setIdentity({
          name: config.nom_cabinet || 'Votre \u00e9tablissement',
          type: config.cabinet_type === 'CLINIQUE' ? 'Clinique' : 'Cabinet dentaire',
          badge: config.cabinet_type === 'CLINIQUE' ? 'CLINIQUE' : 'CABINET',
        });
        setServerAvailable(true);
      } catch {
        if (active) setServerAvailable(false);
      }
    };
    void loadIdentity();
    return () => { active = false; };
  }, []);

  return <main data-v15-hub className="relative min-h-screen overflow-hidden bg-main-bg text-main px-5 py-8 sm:py-10 lg:py-12">
    <div aria-hidden="true" className="pointer-events-none absolute -left-40 -top-48 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />
    <div aria-hidden="true" className="pointer-events-none absolute -right-44 top-32 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />
    <section className="relative z-10 mx-auto w-full max-w-6xl">
      <div className="mb-6 sm:mb-8 text-center">
        <div className="inline-flex items-center gap-2 rounded-elite-sm border border-border-main bg-card-bg px-4 py-2 text-xs font-black uppercase tracking-widest text-primary shadow-elite">
          Digital Crown Hub
        </div>
        <h1 className="mt-5 font-outfit text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight">{identity.name}</h1>
        <p className="mt-3 text-sm font-bold text-text-muted">{identity.type} · Choisissez l’espace de ce poste</p>
        {!serverAvailable && <div data-hub-offline className="mx-auto mt-5 flex max-w-xl items-center justify-center gap-2 rounded-elite-sm border border-primary/20 bg-primary/5 px-4 py-3 text-xs font-bold text-primary">
          <WifiOff size={16}/> Serveur indisponible — le Hub et le Centre de contrôle restent accessibles. Les espaces cliniques restent verrouillés jusqu’au rétablissement.
        </div>}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {experienceCards.map(({ id, title, eyebrow, description, icon: Icon, route }) => <button
          key={id}
          type="button"
          data-hub-experience={id}
          onClick={() => navigate(route)}
          className={`group relative min-h-60 overflow-hidden rounded-elite-lg border bg-card-bg p-6 text-left shadow-elite transition-elite hover:-translate-y-1 hover:shadow-elite-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${id === 'cabinet' ? 'border-primary/25' : 'border-border-main hover:border-primary/30'}`}
        >
          {id === 'cabinet' && <div className="absolute inset-x-0 top-0 h-1 bg-primary" />}
          <div className="flex items-start justify-between gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-elite-sm bg-primary/10 text-primary"><Icon size={24}/></div>
            <span className="rounded-elite-sm border border-border-main bg-main-bg/70 px-2.5 py-1 text-xs font-black uppercase tracking-widest text-text-muted">{id === 'cabinet' ? identity.badge : eyebrow}</span>
          </div>
          <h2 className="mt-7 font-outfit text-xl font-black tracking-tight">{title}</h2>
          <p className="mt-3 min-h-16 text-sm font-semibold leading-relaxed text-text-muted">{description}</p>
          <div className="mt-5 flex items-center justify-between border-t border-border-main pt-4">
            <span className="text-xs font-black text-primary">{'Ouvrir l\u2019espace'}</span>
            <span className="flex h-8 w-8 items-center justify-center rounded-elite-sm bg-primary/10 text-primary transition-transform group-hover:translate-x-1"><ArrowRight size={15}/></span>
          </div>
        </button>)}
      </div>

      <WorkstationModeAdminPanel />

      <p className="mt-5 text-center text-xs font-bold text-text-muted">Le Hub ne contient aucune donnée patient ni donnée métier clinique.</p>
    </section>
  </main>;
};
