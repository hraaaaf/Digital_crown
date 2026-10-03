import { useEffect, useState } from 'react';
import { ArrowLeft, KeyRound, MonitorCog } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { workstationModeService } from '../../services/workstationMode';
import { StationKioskShell } from './StationKioskShell';

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
        setAdminTapCount(0);
      }
    };
    window.addEventListener('keydown', handleAdminShortcut);
    return () => window.removeEventListener('keydown', handleAdminShortcut);
  }, [isStation]);

  useEffect(() => {
    if (!adminTapCount || adminOpen) return;
    const timer = window.setTimeout(() => setAdminTapCount(0), 3_000);
    return () => window.clearTimeout(timer);
  }, [adminOpen, adminTapCount]);

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

  if (isStation && !adminOpen) {
    return <StationKioskShell onAdminTap={registerAdminTap} />;
  }

  if (isStation) {
    return (
      <main
        data-workstation-experience="station"
        data-station-admin
        className="relative min-h-screen overflow-x-hidden bg-main-bg px-4 py-8 text-main sm:px-6 sm:py-10"
      >
        <section className="mx-auto w-full max-w-md rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite sm:p-8">
          <p className="text-xs font-black uppercase tracking-widest text-primary">Digital Crown · Administration</p>
          <h1 className="mt-3 font-outfit text-2xl font-black tracking-tight">Administration du poste</h1>
          <p className="mt-3 text-sm font-semibold leading-relaxed text-text-muted">
            La Station reste verrouillée tant que le PIN propriétaire n’est pas validé par le serveur.
          </p>
          <label className="mt-6 block text-xs font-black uppercase tracking-wide text-text-muted">
            PIN propriétaire
            <input
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              autoComplete="off"
              value={ownerPin}
              onChange={(event) => setOwnerPin(event.target.value.replace(/\D/g, '').slice(0, 8))}
              className="mt-2 min-h-12 w-full rounded-elite-sm border border-border-main bg-main-bg px-4 text-base font-semibold text-main outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary"
            />
          </label>
          <button
            type="button"
            disabled={busy || !ownerPin}
            onClick={leaveStation}
            className="mt-4 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-elite-sm bg-primary px-4 text-sm font-black text-card-bg transition-elite disabled:border disabled:border-border-main disabled:bg-main-bg disabled:text-text-muted disabled:opacity-100"
          >
            <KeyRound size={17} aria-hidden="true" />
            {busy ? 'Vérification…' : 'Autoriser l’accès au Hub'}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setOwnerPin('');
              setFeedback('');
              setAdminOpen(false);
            }}
            className="mt-3 inline-flex min-h-12 w-full items-center justify-center rounded-elite-sm border border-border-main px-4 text-sm font-black text-main transition-elite hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Annuler
          </button>
          {feedback && <p role="status" className="mt-4 text-sm font-bold text-text-muted">{feedback}</p>}
        </section>
      </main>
    );
  }

  return (
    <main data-workstation-experience={experience} className="relative flex min-h-screen items-center justify-center overflow-hidden bg-main-bg px-5 py-10 text-main">
      <section className="relative z-10 w-full max-w-2xl rounded-elite-lg border border-border-main bg-card-bg/95 p-7 text-center shadow-elite backdrop-blur-sm sm:p-10">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-elite-sm bg-primary/10 text-primary">
          <MonitorCog size={30} aria-hidden="true" />
        </div>
        <p className="mt-6 text-xs font-black uppercase tracking-widest text-primary">Digital Crown</p>
        <h1 className="mt-2 font-outfit text-3xl font-black tracking-tight">Centre de contrôle</h1>
        <p className="mx-auto mt-4 max-w-xl text-sm font-semibold leading-relaxed text-text-muted">
          Espace technique en cours de construction. Le diagnostic local restera accessible même si le serveur cabinet est indisponible.
        </p>
        <button
          type="button"
          onClick={() => navigate('/hub')}
          className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-elite-sm border border-border-main px-5 text-sm font-black text-main transition-elite hover:bg-primary/5"
        >
          <ArrowLeft size={16} aria-hidden="true" /> Retour au Hub
        </button>
      </section>
    </main>
  );
};
