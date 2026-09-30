import { useEffect, useState } from 'react';
import { ArrowLeft, KeyRound, MonitorCog, TabletSmartphone } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { workstationModeService } from '../../services/workstationMode';

const errorDetail = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (response?.status === 401) return 'Connexion administrateur requise.';
    if (response?.data?.detail) return response.data.detail;
  }
  return 'Autorisation impossible.';
};

export const WorkstationExperiencePage = ({ experience }: { experience: 'station' | 'control-center' }) => {
  const navigate = useNavigate();
  const isStation = experience === 'station';
  const Icon = isStation ? TabletSmartphone : MonitorCog;
  const [ownerPin, setOwnerPin] = useState('');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [adminOpen, setAdminOpen] = useState(false);
  const [adminTapCount, setAdminTapCount] = useState(0);

  useEffect(() => {
    if (!isStation) return;
    const handleAdminShortcut = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.altKey && event.key.toLowerCase() === 'h') {
        event.preventDefault();
        setAdminOpen(true);
      }
    };
    window.addEventListener('keydown', handleAdminShortcut);
    return () => window.removeEventListener('keydown', handleAdminShortcut);
  }, [isStation]);

  const registerAdminTap = () => {
    if (!isStation || adminOpen) return;
    setAdminTapCount((count) => {
      const next = count + 1;
      if (next >= 5) {
        setAdminOpen(true);
        return 0;
      }
      return next;
    });
  };

  const leaveStation = async () => {
    if (!/^\d{4,8}$/.test(ownerPin)) {
      setFeedback('PIN propriétaire requis.');
      return;
    }
    setBusy(true);
    setFeedback('');
    try {
      await workstationModeService.authorizeStationEscape(ownerPin);
      setOwnerPin('');
      navigate('/hub?select=1', { replace: true });
    } catch (error) {
      setFeedback(errorDetail(error));
    } finally {
      setBusy(false);
    }
  };

  return <main data-workstation-experience={experience} className="relative min-h-screen overflow-hidden bg-main-bg text-main flex items-center justify-center px-5 py-10">
    <div aria-hidden="true" className="pointer-events-none absolute left-1/2 top-1/2 h-[42rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/[0.045]" />
    <div aria-hidden="true" className="pointer-events-none absolute left-1/2 top-1/2 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/[0.06]" />
    <div aria-hidden="true" className="pointer-events-none absolute left-1/2 top-1/2 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/[0.035] blur-3xl" />
    <section className="relative z-10 w-full max-w-2xl overflow-hidden rounded-elite-lg border border-border-main bg-card-bg/95 p-7 sm:p-10 shadow-elite text-center backdrop-blur-sm">
      <div aria-hidden="true" className="absolute inset-x-24 top-0 h-px bg-gradient-to-r from-transparent via-primary/45 to-transparent" />
      {isStation ? (
        <button
          type="button"
          aria-label="Digital Crown"
          onClick={registerAdminTap}
          className="mx-auto flex h-16 w-16 items-center justify-center rounded-elite-sm bg-primary/10 text-primary"
        >
          <Icon size={30}/>
        </button>
      ) : (
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-elite-sm bg-primary/10 text-primary"><Icon size={30}/></div>
      )}
      <p className="mt-6 text-xs font-black uppercase tracking-widest text-primary">Digital Crown</p>
      <h1 className="mt-2 font-outfit text-3xl font-black tracking-tight">{isStation ? "Station d'accueil" : 'Centre de contrôle'}</h1>
      <p className="mx-auto mt-4 max-w-xl text-sm font-semibold leading-relaxed text-text-muted">{isStation ? "Configuration en cours de construction. La Station patient sera activée après le contrat de mode poste sécurisé." : "Espace technique en cours de construction. Le diagnostic local restera accessible même si le serveur cabinet est indisponible."}</p>
      {isStation && !adminOpen && <div aria-hidden="true" className="mx-auto mt-8 flex max-w-md items-center gap-4"><span className="h-px flex-1 bg-gradient-to-r from-transparent to-border-main"/><span className="h-2 w-2 rounded-full border-2 border-card-bg bg-primary/55 shadow-[0_0_0_4px_rgba(15,76,129,0.06)]"/><span className="h-px flex-1 bg-gradient-to-l from-transparent to-border-main"/></div>}

      {isStation && adminOpen ? (
        <div data-station-admin className="mx-auto mt-8 max-w-sm rounded-elite-sm border border-border-main bg-main-bg p-4 text-left">
          <p className="text-xs font-black uppercase tracking-widest text-text-muted">Administration du poste</p>
          <label className="mt-4 block text-xs font-black uppercase tracking-wide text-text-muted">
            PIN propriétaire
            <input
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              value={ownerPin}
              onChange={(event) => setOwnerPin(event.target.value.replace(/\D/g, '').slice(0, 8))}
              className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-card-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
            />
          </label>
          <button
            type="button"
            disabled={busy || !ownerPin}
            onClick={leaveStation}
            className="mt-3 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-elite-sm bg-primary px-4 text-sm font-black text-card-bg transition-elite disabled:bg-slate-200 disabled:text-slate-500 disabled:opacity-100"
          >
            <KeyRound size={16} />
            {busy ? 'Vérification…' : 'Autoriser l’accès au Hub'}
          </button>
          {feedback && <p role="status" className="mt-3 text-sm font-bold text-text-muted">{feedback}</p>}
        </div>
      ) : !isStation ? (
        <button type="button" onClick={() => navigate('/hub')} className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-elite-sm border border-border-main px-5 text-sm font-black text-main transition-elite hover:bg-primary/5"><ArrowLeft size={16}/> Retour au Hub</button>
      ) : null}
    </section>
  </main>;
};
