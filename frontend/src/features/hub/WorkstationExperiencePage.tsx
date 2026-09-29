import { MonitorCog, TabletSmartphone, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const WorkstationExperiencePage = ({ experience }: { experience: 'station' | 'control-center' }) => {
  const navigate = useNavigate();
  const isStation = experience === 'station';
  const Icon = isStation ? TabletSmartphone : MonitorCog;
  return <main data-workstation-experience={experience} className="min-h-screen bg-main-bg text-main flex items-center justify-center px-5 py-10">
    <section className="w-full max-w-2xl rounded-elite-lg border border-border-main bg-card-bg p-7 sm:p-10 shadow-elite text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-elite-sm bg-primary/10 text-primary"><Icon size={30}/></div>
      <p className="mt-6 text-xs font-black uppercase tracking-widest text-primary">Digital Crown</p>
      <h1 className="mt-2 font-outfit text-3xl font-black tracking-tight">{isStation ? "Station d'accueil" : 'Centre de contrôle'}</h1>
      <p className="mt-4 text-sm font-semibold leading-relaxed text-text-muted">{isStation ? "Configuration en cours de construction. La Station patient sera activ\u00e9e apr\u00e8s le contrat de mode poste s\u00e9curis\u00e9." : "Espace technique en cours de construction. Le diagnostic local restera accessible m\u00eame si le serveur cabinet est indisponible."}</p>
      {!isStation && <button type="button" onClick={() => navigate('/hub')} className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-elite-sm border border-border-main px-5 text-sm font-black text-main transition-elite hover:bg-primary/5"><ArrowLeft size={16}/> Retour au Hub</button>}
    </section>
  </main>;
};
