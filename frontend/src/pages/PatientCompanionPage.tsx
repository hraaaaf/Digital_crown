import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Crown,
  FileText,
  Image as ImageIcon,
  KeyRound,
  LockKeyhole,
  LogOut,
  Mail,
  RefreshCw,
  ShieldCheck,
  UserRound,
  UsersRound,
} from 'lucide-react';
import {
  isPatientFirebaseConfigured,
  patientAuthErrorMessage,
  patientAuthService,
  type PatientAuthSnapshot,
} from '../patient-companion/firebasePatientAuth';
import {
  PatientCompanionApiError,
  patientCompanionApi,
  type PatientAppointment,
  type PatientContext,
  type PatientShare,
} from '../patient-companion/patientCompanionApi';

interface PatientCompanionServices {
  auth: {
    configured: () => boolean;
    observe: (listener: (value: PatientAuthSnapshot | null) => void) => Promise<() => void>;
    signIn: (email: string, password: string) => Promise<PatientAuthSnapshot>;
    create: (email: string, password: string) => Promise<PatientAuthSnapshot>;
    resendVerification: () => Promise<void>;
    refresh: () => Promise<PatientAuthSnapshot | null>;
    signOut: () => Promise<void>;
  };
  api: {
    getContexts: () => Promise<PatientContext[]>;
    activate: (input: { token?: string; manual_code?: string }) => Promise<PatientContext>;
    getAppointments: (accessId: string) => Promise<PatientAppointment[]>;
    getShares: (accessId: string) => Promise<PatientShare[]>;
  };
  initialToken?: string;
}

const defaultServices: PatientCompanionServices = {
  auth: patientAuthService,
  api: patientCompanionApi,
};

const relationshipLabel: Record<string, string> = {
  SELF: 'Mon dossier',
  PARENT: 'Parent',
  GUARDIAN: 'Tuteur',
  CAREGIVER: 'Aidant',
};

function formatAppointment(value: string): { day: string; time: string } {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { day: 'Date à confirmer', time: '' };
  return {
    day: new Intl.DateTimeFormat('fr-MA', { weekday: 'long', day: 'numeric', month: 'long' }).format(date),
    time: new Intl.DateTimeFormat('fr-MA', { hour: '2-digit', minute: '2-digit' }).format(date),
  };
}

function patientApiMessage(error: unknown): string {
  if (error instanceof PatientCompanionApiError) {
    if (error.status === 401) return 'Votre session patient doit être renouvelée.';
    if (error.status === 403) return 'Cet accès patient n’est plus disponible.';
    if (error.status === 404) return 'Ce contexte patient n’est plus disponible.';
    if (error.status === 503) return 'Le service patient est temporairement indisponible.';
    return error.message;
  }
  return 'Impossible de charger votre espace patient.';
}

const Spinner = () => (
  <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden="true" />
);

export const PatientCompanionPage = ({ services = defaultServices }: { services?: PatientCompanionServices }) => {
  const initialQrToken = useMemo(() => {
    if (services.initialToken !== undefined) return services.initialToken;
    if (typeof window === 'undefined') return '';
    return new URLSearchParams(window.location.search).get('token')?.trim() || '';
  }, [services.initialToken]);

  const [authReady, setAuthReady] = useState(false);
  const [authUser, setAuthUser] = useState<PatientAuthSnapshot | null>(null);
  const [authMode, setAuthMode] = useState<'signin' | 'create'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authBusy, setAuthBusy] = useState(false);
  const [authMessage, setAuthMessage] = useState('');

  const [contexts, setContexts] = useState<PatientContext[]>([]);
  const [contextLoading, setContextLoading] = useState(false);
  const [selectedAccessId, setSelectedAccessId] = useState('');
  const [needsActivation, setNeedsActivation] = useState(false);
  const [qrToken, setQrToken] = useState(initialQrToken);
  const [manualCode, setManualCode] = useState('');
  const [activationBusy, setActivationBusy] = useState(false);
  const [activationMessage, setActivationMessage] = useState('');

  const [appointments, setAppointments] = useState<PatientAppointment[]>([]);
  const [shares, setShares] = useState<PatientShare[]>([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [pageMessage, setPageMessage] = useState('');

  const configured = services.auth.configured();

  const loadContexts = useCallback(async () => {
    setContextLoading(true);
    setPageMessage('');
    try {
      const next = await services.api.getContexts();
      setContexts(next);
      setNeedsActivation(false);
      setSelectedAccessId((current) => {
        if (current && next.some((item) => item.access_id === current)) return current;
        return next.length === 1 ? next[0].access_id : '';
      });
    } catch (error) {
      if (error instanceof PatientCompanionApiError && error.status === 403) {
        setContexts([]);
        setSelectedAccessId('');
        setNeedsActivation(true);
      } else {
        setPageMessage(patientApiMessage(error));
      }
    } finally {
      setContextLoading(false);
    }
  }, [services.api]);

  useEffect(() => {
    if (!configured) {
      setAuthReady(true);
      return;
    }
    let unsubscribe: (() => void) | undefined;
    let cancelled = false;
    services.auth.observe((value) => {
      if (cancelled) return;
      setAuthUser(value);
      setAuthReady(true);
      if (!value) {
        setContexts([]);
        setSelectedAccessId('');
        setNeedsActivation(false);
        setAppointments([]);
        setShares([]);
      }
    }).then((fn) => { unsubscribe = fn; }).catch(() => {
      if (!cancelled) {
        setAuthReady(true);
        setAuthMessage('Authentification patient indisponible.');
      }
    });
    return () => {
      cancelled = true;
      unsubscribe?.();
    };
  }, [configured, services.auth]);

  useEffect(() => {
    if (authUser?.emailVerified) void loadContexts();
  }, [authUser?.uid, authUser?.emailVerified, loadContexts]);

  useEffect(() => {
    if (!selectedAccessId) {
      setAppointments([]);
      setShares([]);
      return;
    }
    let cancelled = false;
    const load = async () => {
      setDataLoading(true);
      setPageMessage('');
      try {
        const [nextAppointments, nextShares] = await Promise.all([
          services.api.getAppointments(selectedAccessId),
          services.api.getShares(selectedAccessId),
        ]);
        if (!cancelled) {
          setAppointments(nextAppointments);
          setShares(nextShares);
        }
      } catch (error) {
        if (!cancelled) {
          setPageMessage(patientApiMessage(error));
          if (error instanceof PatientCompanionApiError && (error.status === 403 || error.status === 404)) {
            setSelectedAccessId('');
            void loadContexts();
          }
        }
      } finally {
        if (!cancelled) setDataLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [selectedAccessId, services.api, loadContexts]);

  const selectedContext = contexts.find((item) => item.access_id === selectedAccessId) ?? null;
  const documentShares = shares.filter((item) => item.resource_type === 'document');
  const mediaShares = shares.filter((item) => item.resource_type === 'media');

  const submitAuth = async (event: React.FormEvent) => {
    event.preventDefault();
    setAuthBusy(true);
    setAuthMessage('');
    try {
      const user = authMode === 'signin'
        ? await services.auth.signIn(email, password)
        : await services.auth.create(email, password);
      setAuthUser(user);
      if (authMode === 'create') setAuthMessage('Compte créé. Vérifiez votre e-mail avant l’activation.');
    } catch (error) {
      setAuthMessage(patientAuthErrorMessage(error));
    } finally {
      setAuthBusy(false);
    }
  };

  const refreshVerification = async () => {
    setAuthBusy(true);
    setAuthMessage('');
    try {
      const next = await services.auth.refresh();
      setAuthUser(next);
      if (!next?.emailVerified) setAuthMessage('E-mail pas encore vérifié.');
    } catch (error) {
      setAuthMessage(patientAuthErrorMessage(error));
    } finally {
      setAuthBusy(false);
    }
  };

  const activate = async (event: React.FormEvent) => {
    event.preventDefault();
    const code = manualCode.trim();
    if (!qrToken && !code) {
      setActivationMessage('Saisissez le code remis par votre cabinet.');
      return;
    }
    setActivationBusy(true);
    setActivationMessage('');
    try {
      await services.api.activate(qrToken ? { token: qrToken } : { manual_code: code });
      setQrToken('');
      setManualCode('');
      if (typeof window !== 'undefined' && window.location.search) {
        window.history.replaceState({}, '', window.location.pathname);
      }
      await loadContexts();
    } catch (error) {
      setActivationMessage(patientApiMessage(error));
    } finally {
      setActivationBusy(false);
    }
  };

  const logout = async () => {
    setAuthBusy(true);
    try {
      await services.auth.signOut();
      setAuthUser(null);
      setContexts([]);
      setSelectedAccessId('');
    } finally {
      setAuthBusy(false);
    }
  };

  return (
    <main className="min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_top_left,_#e7f0ff_0,_#f8fafc_42%,_#eef4fb_100%)] text-slate-900">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex min-h-16 w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[#003380] text-white shadow-sm">
              <Crown size={20} />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-black text-[#003380] sm:text-base">DigitalCrown</p>
              <p className="truncate text-xs font-semibold text-slate-500">Patient Companion</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 sm:flex">
              <ShieldCheck size={14} /> Accès patient sécurisé
            </span>
            {authUser && (
              <button
                type="button"
                onClick={logout}
                disabled={authBusy}
                className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
              >
                <LogOut size={16} /> <span className="hidden sm:inline">Déconnexion</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
        {!configured ? (
          <section className="mx-auto max-w-xl rounded-[28px] border border-amber-200 bg-white p-6 shadow-xl shadow-slate-200/50 sm:p-8">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-700"><LockKeyhole /></div>
            <h1 className="text-2xl font-black">Espace patient indisponible</h1>
            <p className="mt-3 leading-7 text-slate-600">La configuration Firebase Patient Companion n’est pas disponible sur cette installation. Aucun contournement d’authentification n’est autorisé.</p>
          </section>
        ) : !authReady ? (
          <div className="flex min-h-[55vh] items-center justify-center gap-3 font-bold text-[#003380]"><Spinner /> Ouverture de l’espace patient…</div>
        ) : !authUser ? (
          <section className="mx-auto grid max-w-5xl items-stretch gap-6 lg:grid-cols-[1.05fr_.95fr]">
            <div className="rounded-[32px] bg-[#003380] p-7 text-white shadow-2xl shadow-blue-950/20 sm:p-10">
              <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black uppercase tracking-[0.14em]"><ShieldCheck size={14} /> Patient Companion</span>
              <h1 className="mt-6 text-3xl font-black leading-tight sm:text-5xl">Vos rendez-vous et partages, sans ouvrir le dossier du cabinet.</h1>
              <p className="mt-5 max-w-xl text-sm font-medium leading-7 text-blue-100 sm:text-base">Une identité patient Firebase distincte protège votre accès. Les rendez-vous restent en lecture seule et seuls les documents ou médias explicitement partagés sont visibles.</p>
              <div className="mt-8 grid gap-3 text-sm font-bold sm:grid-cols-2">
                <div className="rounded-2xl bg-white/10 p-4"><LockKeyhole className="mb-2" size={20} />Identité séparée du cabinet</div>
                <div className="rounded-2xl bg-white/10 p-4"><FileText className="mb-2" size={20} />Partages explicites uniquement</div>
              </div>
            </div>

            <form onSubmit={submitAuth} className="rounded-[32px] border border-white bg-white/90 p-6 shadow-xl shadow-slate-200/60 backdrop-blur sm:p-8">
              <div className="mb-6">
                <p className="text-xs font-black uppercase tracking-[0.14em] text-[#003380]">Accès patient</p>
                <h2 className="mt-2 text-2xl font-black">{authMode === 'signin' ? 'Connexion' : 'Créer mon compte'}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-500">Utilisez l’adresse e-mail vérifiée à laquelle votre cabinet a adressé l’invitation.</p>
              </div>
              <label className="block text-sm font-bold text-slate-700">E-mail
                <span className="mt-2 flex min-h-12 items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 focus-within:border-[#003380] focus-within:ring-4 focus-within:ring-blue-100">
                  <Mail size={17} className="shrink-0 text-slate-400" />
                  <input className="min-w-0 flex-1 bg-transparent py-3 outline-none" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
                </span>
              </label>
              <label className="mt-4 block text-sm font-bold text-slate-700">Mot de passe
                <span className="mt-2 flex min-h-12 items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 focus-within:border-[#003380] focus-within:ring-4 focus-within:ring-blue-100">
                  <KeyRound size={17} className="shrink-0 text-slate-400" />
                  <input className="min-w-0 flex-1 bg-transparent py-3 outline-none" type="password" autoComplete={authMode === 'signin' ? 'current-password' : 'new-password'} minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
                </span>
              </label>
              {authMessage && <p role="status" className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">{authMessage}</p>}
              <button disabled={authBusy} className="mt-6 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[#003380] px-5 font-black text-white shadow-lg shadow-blue-900/20 hover:bg-blue-900 disabled:opacity-50">
                {authBusy ? <Spinner /> : <ChevronRight size={18} />}{authMode === 'signin' ? 'Me connecter' : 'Créer et vérifier mon compte'}
              </button>
              <button type="button" onClick={() => { setAuthMode(authMode === 'signin' ? 'create' : 'signin'); setAuthMessage(''); }} className="mt-4 w-full text-sm font-bold text-[#003380]">
                {authMode === 'signin' ? 'Première connexion ? Créer un compte' : 'J’ai déjà un compte'}
              </button>
            </form>
          </section>
        ) : !authUser.emailVerified ? (
          <section className="mx-auto max-w-xl rounded-[32px] border border-white bg-white/90 p-7 shadow-xl shadow-slate-200/60 sm:p-9">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-[#003380]"><Mail /></div>
            <h1 className="mt-5 text-2xl font-black">Vérifiez votre adresse e-mail</h1>
            <p className="mt-3 leading-7 text-slate-600">L’activation reste bloquée tant que Firebase ne confirme pas l’adresse du destinataire. C’est volontaire : un code photographié ne suffit pas.</p>
            {authMessage && <p role="status" className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">{authMessage}</p>}
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <button disabled={authBusy} onClick={refreshVerification} className="inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-[#003380] px-4 font-black text-white disabled:opacity-50"><RefreshCw size={17} /> J’ai vérifié</button>
              <button disabled={authBusy} onClick={() => services.auth.resendVerification().then(() => setAuthMessage('E-mail de vérification renvoyé.')).catch((error) => setAuthMessage(patientAuthErrorMessage(error)))} className="min-h-12 rounded-2xl border border-slate-200 bg-white px-4 font-black text-slate-700 disabled:opacity-50">Renvoyer l’e-mail</button>
            </div>
          </section>
        ) : contextLoading ? (
          <div className="flex min-h-[45vh] items-center justify-center gap-3 font-bold text-[#003380]"><Spinner /> Vérification de vos accès…</div>
        ) : needsActivation ? (
          <section className="mx-auto max-w-xl rounded-[32px] border border-white bg-white/90 p-7 shadow-xl shadow-slate-200/60 sm:p-9">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-[#003380]"><KeyRound /></span>
            <h1 className="mt-5 text-3xl font-black">Activer mon espace patient</h1>
            <p className="mt-3 leading-7 text-slate-600">Le code est à usage unique et doit correspondre à votre identité Firebase vérifiée.</p>
            <form onSubmit={activate} className="mt-6">
              {qrToken ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                  <p className="flex items-center gap-2 text-sm font-black text-emerald-800"><CheckCircle2 size={17} /> Invitation QR détectée</p>
                  <p className="mt-1 text-xs font-semibold text-emerald-700">Le secret n’est pas affiché à l’écran.</p>
                  <button type="button" onClick={() => setQrToken('')} className="mt-3 text-xs font-black text-[#003380]">Utiliser plutôt un code manuel</button>
                </div>
              ) : (
                <label className="block text-sm font-bold text-slate-700">Code d’activation
                  <input value={manualCode} onChange={(e) => setManualCode(e.target.value.toUpperCase())} autoComplete="one-time-code" placeholder="ABCD-EFGH-JKLM" className="mt-2 min-h-14 w-full rounded-2xl border border-slate-200 bg-white px-4 text-center font-mono text-lg font-black tracking-[0.12em] outline-none focus:border-[#003380] focus:ring-4 focus:ring-blue-100" />
                </label>
              )}
              {activationMessage && <p role="status" className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{activationMessage}</p>}
              <button disabled={activationBusy} className="mt-5 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[#003380] px-5 font-black text-white hover:bg-blue-900 disabled:opacity-50">{activationBusy ? <Spinner /> : <ShieldCheck size={18} />} Activer mon espace</button>
            </form>
          </section>
        ) : contexts.length > 1 && !selectedAccessId ? (
          <section className="mx-auto max-w-3xl">
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[#003380]">Vos accès</p>
            <h1 className="mt-2 text-3xl font-black">Choisissez le dossier à consulter</h1>
            <p className="mt-3 text-slate-600">Chaque contexte reste isolé. Les données ne sont jamais fusionnées.</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {contexts.map((context) => (
                <button key={context.access_id} onClick={() => setSelectedAccessId(context.access_id)} className="flex min-h-24 items-center gap-4 rounded-3xl border border-slate-200 bg-white p-5 text-left shadow-sm hover:border-blue-300 hover:shadow-md">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-[#003380]"><UserRound /></span>
                  <span className="min-w-0 flex-1"><strong className="block truncate text-base">{context.patient.display_name || 'Patient'}</strong><span className="mt-1 block text-xs font-bold text-slate-500">{relationshipLabel[context.relationship_type] || context.relationship_type}</span></span>
                  <ChevronRight className="shrink-0 text-slate-400" />
                </button>
              ))}
            </div>
          </section>
        ) : selectedContext ? (
          <section>
            <div className="flex flex-col gap-5 rounded-[30px] border border-white bg-white/80 p-5 shadow-lg shadow-slate-200/50 backdrop-blur sm:p-7 lg:flex-row lg:items-end lg:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.14em] text-[#003380]">Espace patient</p>
                <h1 className="mt-2 truncate text-3xl font-black sm:text-4xl">{selectedContext.patient.display_name || 'Patient'}</h1>
                <p className="mt-2 text-sm font-semibold text-slate-500">{relationshipLabel[selectedContext.relationship_type] || selectedContext.relationship_type} · consultation uniquement</p>
              </div>
              {contexts.length > 1 && (
                <label className="w-full text-xs font-black uppercase tracking-[0.1em] text-slate-500 lg:w-72">Contexte patient
                  <select value={selectedAccessId} onChange={(e) => setSelectedAccessId(e.target.value)} className="mt-2 min-h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm font-bold normal-case tracking-normal text-slate-800 outline-none focus:border-[#003380]">
                    {contexts.map((context) => <option key={context.access_id} value={context.access_id}>{context.patient.display_name} · {relationshipLabel[context.relationship_type] || context.relationship_type}</option>)}
                  </select>
                </label>
              )}
            </div>

            {pageMessage && <p role="status" className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">{pageMessage}</p>}

            <div className="mt-6 grid min-w-0 gap-6 lg:grid-cols-2">
              <article className="min-w-0 rounded-[28px] border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex items-center justify-between gap-3">
                  <div><p className="text-xs font-black uppercase tracking-[0.12em] text-slate-400">Lecture seule</p><h2 className="mt-1 text-xl font-black">Prochains rendez-vous</h2></div>
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-[#003380]"><CalendarDays /></span>
                </div>
                <div className="mt-5 space-y-3">
                  {dataLoading ? <p className="flex items-center gap-2 py-6 text-sm font-bold text-slate-500"><Spinner /> Chargement…</p> : appointments.length === 0 ? (
                    <p className="rounded-2xl bg-slate-50 p-5 text-sm font-semibold leading-6 text-slate-500">Aucun rendez-vous futur partagé par le cabinet.</p>
                  ) : appointments.map((appointment) => {
                    const formatted = formatAppointment(appointment.datetime_start);
                    return <div key={appointment.id} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4"><p className="font-black capitalize text-slate-800">{formatted.day}</p><p className="mt-1 text-sm font-bold text-[#003380]">{formatted.time}{appointment.duration_minutes ? ` · ${appointment.duration_minutes} min` : ''}</p><p className="mt-2 text-sm font-semibold text-slate-500">{appointment.motif || 'Consultation'}</p></div>;
                  })}
                </div>
              </article>

              <article className="min-w-0 rounded-[28px] border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex items-center justify-between gap-3">
                  <div><p className="text-xs font-black uppercase tracking-[0.12em] text-slate-400">Allow-list cabinet</p><h2 className="mt-1 text-xl font-black">Éléments partagés</h2></div>
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700"><ShieldCheck /></span>
                </div>
                <div className="mt-5 space-y-4">
                  {dataLoading ? <p className="flex items-center gap-2 py-6 text-sm font-bold text-slate-500"><Spinner /> Chargement…</p> : shares.length === 0 ? (
                    <p className="rounded-2xl bg-slate-50 p-5 text-sm font-semibold leading-6 text-slate-500">Aucun document ou média n’a été explicitement partagé.</p>
                  ) : (
                    <>
                      {documentShares.length > 0 && <div><p className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.1em] text-slate-400"><FileText size={14} /> Documents</p><div className="space-y-2">{documentShares.map((share) => <div key={share.share_id} className="rounded-2xl border border-slate-100 p-4"><p className="truncate text-sm font-black text-slate-800">{share.title || 'Document partagé'}</p><p className="mt-1 text-xs font-bold text-slate-500">{share.document_type || 'Document'} · métadonnées uniquement</p></div>)}</div></div>}
                      {mediaShares.length > 0 && <div><p className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.1em] text-slate-400"><ImageIcon size={14} /> Médias</p><div className="space-y-2">{mediaShares.map((share) => <div key={share.share_id} className="rounded-2xl border border-slate-100 p-4"><p className="text-sm font-black text-slate-800">{share.asset_type || 'Média partagé'}</p><p className="mt-1 text-xs font-bold text-slate-500">{share.mime_type || 'Fichier'} · aperçu non exposé en D1</p></div>)}</div></div>}
                    </>
                  )}
                </div>
              </article>
            </div>

            <div className="mt-6 flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50/70 p-4 text-sm font-semibold leading-6 text-blue-900"><UsersRound className="mt-0.5 shrink-0" size={18} /><span>Patient Companion n’autorise aucune modification de rendez-vous et n’ouvre aucun fichier non explicitement partagé par le cabinet.</span></div>
          </section>
        ) : (
          <section className="mx-auto max-w-xl rounded-[28px] bg-white p-7 shadow-lg"><h1 className="text-2xl font-black">Aucun accès actif</h1><p className="mt-3 text-slate-600">Votre identité est reconnue mais aucun contexte patient actif n’est disponible.</p></section>
        )}
      </div>
    </main>
  );
};

export default PatientCompanionPage;

export const patientCompanionDefaultServices = {
  ...defaultServices,
  firebaseConfigured: isPatientFirebaseConfigured,
};
