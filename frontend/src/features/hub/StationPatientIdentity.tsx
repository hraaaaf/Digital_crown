import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Nfc, QrCode, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  stationPatientSessionService,
  type StationPatientSessionCreated,
} from '../../services/stationPatientSession';

const apiErrorDetail = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (response?.status === 429) return 'Trop de tentatives. Générez une nouvelle session ou demandez de l’aide.';
    if (response?.data?.detail === 'STATION_FALLBACK_DISABLED') return 'Identification de secours désactivée par le cabinet.';
  }
  return 'Identification non confirmée. Vérifiez les informations ou demandez de l’aide.';
};

export const StationPatientIdentity = ({
  onBack,
  backLabel,
}: {
  onBack: () => void;
  backLabel: string;
}) => {
  const [session, setSession] = useState<StationPatientSessionCreated | null>(null);
  const [status, setStatus] = useState<'loading' | 'pending' | 'identified' | 'expired' | 'error'>('loading');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const [fallbackBusy, setFallbackBusy] = useState(false);
  const [birthDate, setBirthDate] = useState('');
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const start = async () => {
    setStatus('loading');
    setError('');
    setDisplayName('');
    setFallbackOpen(false);
    setBirthDate('');
    setPhone('');
    setFirstName('');
    setLastName('');
    try {
      const created = await stationPatientSessionService.create();
      setSession(created);
      setStatus('pending');
    } catch {
      setSession(null);
      setStatus('error');
      setError('Identification indisponible. Prévenez l’équipe d’accueil.');
    }
  };

  useEffect(() => {
    void start();
  }, []);

  useEffect(() => {
    if (!session || status !== 'pending') return undefined;
    let cancelled = false;
    const poll = async () => {
      try {
        const next = await stationPatientSessionService.status(session.sessionId);
        if (cancelled) return;
        if (next.status === 'identified') {
          setDisplayName(next.displayName);
          setStatus('identified');
          return;
        }
        if (next.status === 'expired') setStatus('expired');
      } catch {
        if (!cancelled) {
          setStatus('error');
          setError('Connexion à la session interrompue.');
        }
      }
    };
    const timer = window.setInterval(() => void poll(), 1500);
    void poll();
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [session, status]);

  useEffect(() => () => {
    if (session) void stationPatientSessionService.purge(session.sessionId).catch(() => undefined);
  }, [session]);

  const expiresLabel = useMemo(() => {
    if (!session) return '';
    return new Date(session.expiresAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, [session]);

  const submitFallback = async () => {
    if (!session || session.fallbackMode === 'disabled' || !birthDate) {
      setError('Identification non confirmée. Vérifiez les informations ou demandez de l’aide.');
      return;
    }
    setFallbackBusy(true);
    setError('');
    try {
      const result = await stationPatientSessionService.fallback(
        session.sessionId,
        session.fallbackMode === 'phone_dob'
          ? { birthDate, phone }
          : { birthDate, firstName, lastName },
      );
      setDisplayName(result.displayName);
      setStatus('identified');
      setFallbackOpen(false);
    } catch (fallbackError) {
      setError(apiErrorDetail(fallbackError));
    } finally {
      setFallbackBusy(false);
    }
  };

  const leave = async () => {
    if (session) await stationPatientSessionService.purge(session.sessionId).catch(() => undefined);
    onBack();
  };

  if (status === 'identified') {
    return (
      <section data-station-patient-identified className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-emerald-200 bg-card-bg p-6 text-center shadow-elite sm:p-8">
        <CheckCircle2 className="mx-auto text-emerald-600" size={42} aria-hidden="true" />
        <h2 className="mt-4 text-2xl font-black">Identité confirmée</h2>
        <p className="mt-2 text-base font-bold text-text-muted">{displayName}</p>
        <p className="mt-3 text-sm font-semibold text-text-muted">Aucune arrivée n’a encore été enregistrée.</p>
        <button type="button" onClick={() => void leave()} className="mt-6 min-h-12 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg">
          {backLabel}
        </button>
      </section>
    );
  }

  return (
    <section data-station-patient-session className="mx-auto mt-9 w-full max-w-xl rounded-elite-lg border border-border-main bg-card-bg p-6 text-center shadow-elite sm:p-8">
      {status === 'loading' && <p className="font-black">Préparation de la session sécurisée…</p>}

      {status === 'pending' && session && (
        <>
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-2 text-xs font-black text-primary">
            <ShieldCheck size={15} aria-hidden="true" /> Session privée · usage unique
          </div>
          <img src={session.qrDataUrl} alt="QR d’identification Patient Companion" className="mx-auto mt-5 aspect-square h-auto w-full max-w-56 rounded-2xl border border-border-main bg-white p-3 object-contain" />
          <p className="mt-4 text-sm font-bold">Scannez avec votre téléphone</p>
          <p className="mt-1 text-xs font-semibold text-text-muted">Le QR expire à {expiresLabel} et ne peut servir qu’une fois.</p>
          <div className="mt-4 flex items-center justify-center gap-2 rounded-2xl border border-border-main bg-main-bg px-4 py-3 text-xs font-bold text-text-muted">
            <Nfc size={18} aria-hidden="true" /> NFC utilise le même lien sécurisé, sans donnée patient.
          </div>

          {session.fallbackMode !== 'disabled' && (
            <button
              type="button"
              data-station-fallback-toggle
              onClick={() => {
                setFallbackOpen((value) => !value);
                setError('');
              }}
              className="mt-4 min-h-12 w-full rounded-elite-sm border border-border-main px-4 text-sm font-black"
            >
              Je n’ai pas mon téléphone
            </button>
          )}

          {fallbackOpen && session.fallbackMode !== 'disabled' && (
            <div data-station-fallback-form className="mt-4 rounded-2xl border border-border-main bg-main-bg p-4 text-start">
              <p className="text-xs font-black uppercase tracking-wider text-primary">Identification de secours</p>
              {session.fallbackMode === 'phone_dob' ? (
                <label className="mt-3 block text-xs font-black text-text-muted">
                  Téléphone
                  <input
                    aria-label="Téléphone"
                    inputMode="tel"
                    value={phone}
                    onChange={(event) => setPhone(event.target.value.slice(0, 32))}
                    className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                  />
                </label>
              ) : (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <label className="text-xs font-black text-text-muted">
                    Prénom
                    <input
                      aria-label="Prénom"
                      value={firstName}
                      onChange={(event) => setFirstName(event.target.value.slice(0, 100))}
                      className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                    />
                  </label>
                  <label className="text-xs font-black text-text-muted">
                    Nom
                    <input
                      aria-label="Nom"
                      value={lastName}
                      onChange={(event) => setLastName(event.target.value.slice(0, 100))}
                      className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                    />
                  </label>
                </div>
              )}
              <label className="mt-3 block text-xs font-black text-text-muted">
                Date de naissance
                <input
                  aria-label="Date de naissance"
                  type="date"
                  value={birthDate}
                  onChange={(event) => setBirthDate(event.target.value)}
                  className="mt-2 min-h-12 w-full rounded-xl border border-border-main bg-card-bg px-3 text-base font-bold text-main"
                />
              </label>
              <button
                type="button"
                disabled={fallbackBusy}
                onClick={() => void submitFallback()}
                className="mt-4 min-h-12 w-full rounded-xl bg-primary px-4 text-sm font-black text-card-bg disabled:opacity-50"
              >
                {fallbackBusy ? 'Vérification…' : 'Confirmer mon identité'}
              </button>
              <p className="mt-3 text-[11px] font-semibold text-text-muted">Les informations servent uniquement à cette vérification et ne sont pas affichées dans la file d’attente.</p>
            </div>
          )}
        </>
      )}

      {status === 'expired' && (
        <>
          <QrCode className="mx-auto text-text-muted" size={38} aria-hidden="true" />
          <p className="mt-4 font-black">Session expirée</p>
          <button type="button" onClick={() => void start()} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-card-bg">
            <RefreshCw size={16} aria-hidden="true" /> Nouveau QR
          </button>
        </>
      )}

      {error && status !== 'error' && <p role="alert" className="mt-4 font-black text-rose-700">{error}</p>}

      {status === 'error' && (
        <>
          <p role="alert" className="font-black text-rose-700">{error}</p>
          <button type="button" onClick={() => void start()} className="mt-5 inline-flex min-h-12 items-center gap-2 rounded-elite-sm border border-border-main px-5 text-sm font-black">
            <RefreshCw size={16} aria-hidden="true" /> Réessayer
          </button>
        </>
      )}

      <button type="button" onClick={() => void leave()} className="mt-5 min-h-12 w-full rounded-elite-sm border border-border-main px-5 text-sm font-black">
        {backLabel}
      </button>
    </section>
  );
};
