import { useEffect, useState } from 'react';
import { KeyRound, MonitorCog, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  workstationModeService,
  type WorkstationBootstrapState,
  type WorkstationExperience,
  type WorkstationState,
} from '../../services/workstationMode';

const modeLabels: Record<WorkstationExperience, string> = {
  cabinet: 'Digital Crown',
  station: "Station d'accueil",
  control_center: 'Centre de contrôle',
};

const modeRoutes: Record<WorkstationExperience, string> = {
  cabinet: '/cabinet',
  station: '/station',
  control_center: '/control-center',
};

const errorDetail = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail === 'WORKSTATION_ENROLLMENT_REQUIRED') {
      return 'Ce navigateur doit être réenregistré comme poste autorisé.';
    }
    if (response?.data?.detail) return response.data.detail;
  }
  return 'Action refusée ou serveur indisponible.';
};

export const WorkstationModeAdminPanel = () => {
  const navigate = useNavigate();
  const [bootstrap, setBootstrap] = useState<WorkstationBootstrapState | null>(null);
  const [state, setState] = useState<WorkstationState | null>(null);
  const [ownerPin, setOwnerPin] = useState('');
  const [accountPassword, setAccountPassword] = useState('');
  const [enrollmentPassword, setEnrollmentPassword] = useState('');
  const [newPin, setNewPin] = useState('');
  const [selectedMode, setSelectedMode] = useState<WorkstationExperience>('cabinet');
  const [busy, setBusy] = useState<'enroll' | 'pin' | 'mode' | null>(null);
  const [feedback, setFeedback] = useState('');

  const refresh = async () => {
    const nextBootstrap = await workstationModeService.getBootstrapState();
    setBootstrap(nextBootstrap);
    if (nextBootstrap.enrollmentRequired) {
      setState(null);
      return;
    }
    const next = await workstationModeService.getState();
    setState(next);
    if (next.defaultExperience) setSelectedMode(next.defaultExperience);
  };

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const nextBootstrap = await workstationModeService.getBootstrapState();
        if (!active) return;
        setBootstrap(nextBootstrap);
        if (!nextBootstrap.canManage || nextBootstrap.enrollmentRequired) return;

        const next = await workstationModeService.getState();
        if (!active) return;
        setState(next);
        if (next.defaultExperience) setSelectedMode(next.defaultExperience);
      } catch {
        if (active) setState(null);
      }
    };

    void load();
    return () => { active = false; };
  }, []);

  const enroll = async () => {
    if (!enrollmentPassword) {
      setFeedback('Mot de passe du compte requis.');
      return;
    }
    setBusy('enroll');
    setFeedback('');
    try {
      const next = await workstationModeService.enrollWorkstation(enrollmentPassword);
      setEnrollmentPassword('');
      setState(next);
      setBootstrap({ ...next, authenticated: true });
      if (next.defaultExperience) setSelectedMode(next.defaultExperience);
      setFeedback('Poste réenregistré. Choisissez ensuite son mode de démarrage.');
    } catch (error) {
      setFeedback(errorDetail(error));
    } finally {
      setBusy(null);
    }
  };

  if (bootstrap?.enrollmentRequired) {
    return (
      <section data-workstation-enrollment className="mt-6 rounded-elite-lg border border-primary/20 bg-card-bg p-5 shadow-elite sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-elite-sm bg-primary/10 text-primary">
            <ShieldCheck size={19} />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-widest text-primary">Identité du poste requise</p>
            <h2 className="mt-1 font-outfit text-lg font-black">Réenregistrer ce navigateur</h2>
            <p className="mt-1 max-w-2xl text-sm font-semibold leading-relaxed text-text-muted">
              L'identité locale du poste est absente ou invalide. L'accès clinique reste verrouillé jusqu'à un réenregistrement explicite par le propriétaire principal.
            </p>
          </div>
        </div>

        {bootstrap.canConfigurePin ? (
          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <label className="flex-1 text-xs font-black uppercase tracking-wide text-text-muted">
              Mot de passe du compte propriétaire
              <input
                type="password"
                value={enrollmentPassword}
                onChange={(event) => setEnrollmentPassword(event.target.value)}
                autoComplete="current-password"
                className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-main-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
              />
            </label>
            <button
              type="button"
              disabled={busy !== null || !enrollmentPassword}
              onClick={enroll}
              className="self-end min-h-11 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg transition-elite disabled:border disabled:border-border-main disabled:bg-main-bg disabled:text-text-muted disabled:opacity-100"
            >
              {busy === 'enroll' ? 'Vérification…' : 'Réenregistrer le poste'}
            </button>
          </div>
        ) : (
          <p className="mt-5 rounded-elite-sm border border-border-main bg-main-bg p-3 text-sm font-semibold text-text-muted">
            Le propriétaire principal doit réenregistrer ce poste.
          </p>
        )}

        {feedback && <p role="status" className="mt-3 text-sm font-bold text-text-muted">{feedback}</p>}
      </section>
    );
  }

  if (!state?.canManage) return null;

  const savePin = async () => {
    if (!/^\d{4,8}$/.test(newPin)) {
      setFeedback('Le PIN doit contenir 4 à 8 chiffres.');
      return;
    }
    setBusy('pin');
    setFeedback('');
    try {
      await workstationModeService.configureOwnerPin(accountPassword, newPin);
      setAccountPassword('');
      setNewPin('');
      await refresh();
      setFeedback('PIN propriétaire enregistré.');
    } catch (error) {
      setFeedback(errorDetail(error));
    } finally {
      setBusy(null);
    }
  };

  const saveMode = async () => {
    if (!/^\d{4,8}$/.test(ownerPin)) {
      setFeedback('Saisissez le PIN propriétaire.');
      return;
    }
    setBusy('mode');
    setFeedback('');
    try {
      await workstationModeService.changeMode(selectedMode, ownerPin);
      setOwnerPin('');
      navigate(modeRoutes[selectedMode], { replace: true });
    } catch (error) {
      setFeedback(errorDetail(error));
    } finally {
      setBusy(null);
    }
  };

  return (
    <section data-workstation-admin className="mt-6 rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-primary">
            <MonitorCog size={18} />
            <span className="text-xs font-black uppercase tracking-widest">Configuration du poste</span>
          </div>
          <h2 className="mt-2 font-outfit text-lg font-black">Mode de démarrage permanent</h2>
          <p className="mt-1 text-sm font-semibold text-text-muted">
            Le serveur reste l'autorité. Un changement permanent exige le PIN propriétaire.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 self-start rounded-elite-sm border border-border-main bg-main-bg px-3 py-2 text-xs font-black text-text-muted">
          <ShieldCheck size={15} />
          {state.pinConfigured ? 'PIN configuré' : 'PIN à configurer'}
        </div>
      </div>

      {!state.pinConfigured && !state.canConfigurePin && (
        <p className="mt-5 rounded-elite-sm border border-border-main bg-main-bg p-3 text-sm font-semibold text-text-muted">
          Le propriétaire principal doit d'abord configurer le PIN de ce cabinet.
        </p>
      )}

      {state.canConfigurePin && (
        <details className="mt-5 rounded-elite-sm border border-border-main bg-main-bg p-4">
          <summary className="cursor-pointer text-sm font-black text-main">
            {state.pinConfigured ? 'Changer le PIN propriétaire' : 'Configurer le PIN propriétaire'}
          </summary>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-xs font-black uppercase tracking-wide text-text-muted">
              Mot de passe du compte
              <input
                type="password"
                value={accountPassword}
                onChange={(event) => setAccountPassword(event.target.value)}
                autoComplete="current-password"
                className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-card-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
              />
            </label>
            <label className="text-xs font-black uppercase tracking-wide text-text-muted">
              Nouveau PIN
              <input
                type="password"
                inputMode="numeric"
                pattern="[0-9]*"
                value={newPin}
                onChange={(event) => setNewPin(event.target.value.replace(/\D/g, '').slice(0, 8))}
                autoComplete="new-password"
                className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-card-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary"
              />
            </label>
          </div>
          <button
            type="button"
            disabled={busy !== null || !accountPassword || !newPin}
            onClick={savePin}
            className="mt-3 inline-flex min-h-11 items-center gap-2 rounded-elite-sm bg-primary px-4 text-sm font-black text-card-bg transition-elite disabled:opacity-50"
          >
            <KeyRound size={16} />
            {busy === 'pin' ? 'Enregistrement…' : 'Enregistrer le PIN'}
          </button>
        </details>
      )}

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {(Object.keys(modeLabels) as WorkstationExperience[]).map((mode) => (
          <button
            key={mode}
            type="button"
            disabled={!state.pinConfigured || busy !== null}
            onClick={() => setSelectedMode(mode)}
            aria-pressed={selectedMode === mode}
            className={`min-h-11 rounded-elite-sm border px-3 text-sm font-black transition-elite disabled:opacity-50 ${selectedMode === mode ? 'border-primary bg-primary/10 text-primary' : 'border-border-main bg-main-bg text-main hover:border-primary/40'}`}
          >
            {modeLabels[mode]}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <label className="flex-1 text-xs font-black uppercase tracking-wide text-text-muted">
          PIN propriétaire
          <input
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            value={ownerPin}
            onChange={(event) => setOwnerPin(event.target.value.replace(/\D/g, '').slice(0, 8))}
            disabled={!state.pinConfigured || busy !== null}
            className="mt-2 min-h-11 w-full rounded-elite-sm border border-border-main bg-main-bg px-3 text-sm font-semibold text-main outline-none focus:border-primary disabled:opacity-50"
          />
        </label>
        <button
          type="button"
          disabled={!state.pinConfigured || busy !== null || !ownerPin}
          onClick={saveMode}
          className="self-end min-h-11 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg transition-elite disabled:border disabled:border-border-main disabled:bg-main-bg disabled:text-text-muted disabled:opacity-100"
        >
          {busy === 'mode' ? 'Application…' : 'Appliquer ce mode'}
        </button>
      </div>

      {feedback && <p role="status" className="mt-3 text-sm font-bold text-text-muted">{feedback}</p>}
    </section>
  );
};
