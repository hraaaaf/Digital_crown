import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Database,
  Globe2,
  Loader2,
  Network,
  RefreshCw,
  Server,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react';
import { API_BASE, getRuntimeAuthToken } from '../../services/api';

type TopologyPayload = {
  status?: string;
  topologyRole?: string;
  knownTopologyRoles?: string[];
  environment?: string;
  bindHost?: string;
  port?: number;
  scheme?: string;
  lanExposed?: boolean;
  tlsEnabled?: boolean;
  tlsReady?: boolean;
  connectionUrl?: string | null;
  remediation?: string | null;
};

type ProbeResult = {
  baseUrl: string;
  latencyMs: number;
  backendOk: boolean;
  databaseOk: boolean;
  authOk: boolean | null;
  topology: TopologyPayload | null;
  error: string | null;
  crossOriginLimited: boolean;
};

const isLoopback = (hostname: string) => {
  const normalized = hostname.toLowerCase().replace(/^\[|\]$/g, '');
  return normalized === 'localhost'
    || normalized === '127.0.0.1'
    || normalized.startsWith('127.')
    || normalized === '::1';
};

const isPrivateLanHost = (hostname: string) => {
  const normalized = hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (isLoopback(normalized) || normalized.endsWith('.local')) return true;
  if (/^10(?:\.\d{1,3}){3}$/.test(normalized)) return true;
  if (/^192\.168(?:\.\d{1,3}){2}$/.test(normalized)) return true;
  const private172 = normalized.match(/^172\.(\d{1,3})(?:\.\d{1,3}){2}$/);
  if (private172) {
    const secondOctet = Number(private172[1]);
    if (secondOctet >= 16 && secondOctet <= 31) return true;
  }
  return /^(?:fc|fd)[0-9a-f]{2}:/i.test(normalized) || /^fe[89ab][0-9a-f]:/i.test(normalized);
};

const normalizeTarget = (raw: string): { baseUrl: string | null; error: string | null } => {
  const trimmed = raw.trim();
  if (!trimmed) return { baseUrl: null, error: 'Saisissez l’adresse du serveur cabinet.' };

  const candidate = /^[a-z][a-z0-9+.-]*:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return { baseUrl: null, error: 'Adresse invalide. Exemple : https://192.168.1.20:8005' };
  }

  if (!['http:', 'https:'].includes(parsed.protocol)) {
    return { baseUrl: null, error: 'Seules les adresses HTTP/HTTPS sont acceptées.' };
  }
  if (parsed.username || parsed.password) {
    return { baseUrl: null, error: 'Ne mettez jamais d’identifiant ou mot de passe dans l’adresse.' };
  }

  const hostname = parsed.hostname;
  if (!isPrivateLanHost(hostname)) {
    return { baseUrl: null, error: 'Utilisez uniquement une adresse locale du cabinet (IP privée ou nom .local).' };
  }
  if (parsed.protocol === 'http:' && !isLoopback(hostname)) {
    return { baseUrl: null, error: 'HTTPS est obligatoire pour une adresse LAN. HTTP est accepté uniquement en local.' };
  }

  const port = parsed.port || '8005';
  if (port !== '8005') {
    return { baseUrl: null, error: 'Digital Crown utilise le port cabinet 8005.' };
  }

  return { baseUrl: `${parsed.protocol}//${parsed.hostname}:8005`, error: null };
};

const remediationCopy = (result: ProbeResult | null) => {
  if (!result) return 'Lancez un diagnostic pour vérifier le serveur, la base et le transport réseau.';
  if (result.error) return result.error;
  if (!result.backendOk) return 'Backend injoignable. Vérifiez que Digital Crown est démarré, l’adresse saisie et le pare-feu du poste serveur.';
  if (!result.databaseOk) return 'Backend joignable mais base indisponible. Vérifiez PostgreSQL puis relancez le diagnostic.';
  if (result.authOk === false) return 'Serveur et base disponibles, mais la session de ce poste n’est pas authentifiée. Ouvrez le serveur puis connectez-vous.';
  if (result.authOk === null && result.backendOk && result.databaseOk) {
    return 'Serveur joignable sans credential. Ouvrez cette adresse pour vérifier l’authentification et terminer le diagnostic sur cette autorité.';
  }
  if (result.topology?.remediation === 'LAN_DISABLED_LOOPBACK_ONLY') {
    return 'Serveur limité à la machine locale. Pour un poste annexe, configurez explicitement une adresse LAN et HTTPS/TLS sur le serveur.';
  }
  if (result.topology?.remediation === 'TLS_REQUIRED_FOR_LAN') {
    return 'Exposition LAN détectée sans TLS prêt. Configurez le certificat et la clé HTTPS avant toute connexion de poste annexe.';
  }
  if (result.topology?.lanExposed && result.topology?.tlsReady) {
    return 'Serveur LAN prêt : backend, base de données et transport HTTPS répondent correctement.';
  }
  return 'Serveur local prêt. Pour connecter un autre poste, utilisez l’adresse LAN HTTPS publiée par le serveur cabinet.';
};

const StatusPill = ({ ok, label }: { ok: boolean; label: string }) => (
  <span className={`inline-flex items-center gap-1.5 rounded-elite-sm border px-2.5 py-1 text-xs font-black ${ok ? 'border-primary/20 bg-primary/5 text-primary' : 'border-border-main bg-main-bg text-text-muted'}`}>
    {ok ? <CheckCircle2 size={14} aria-hidden="true" /> : <TriangleAlert size={14} aria-hidden="true" />}
    {label}
  </span>
);

export const ControlCenterTopologyPanel = () => {
  const [target, setTarget] = useState(API_BASE);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ProbeResult | null>(null);
  const [inputError, setInputError] = useState('');

  const normalized = useMemo(() => normalizeTarget(target), [target]);

  const runProbe = useCallback(async (rawTarget: string) => {
    const parsed = normalizeTarget(rawTarget);
    if (!parsed.baseUrl) {
      setInputError(parsed.error || 'Adresse invalide.');
      setResult(null);
      return;
    }

    setInputError('');

    const currentBase = normalizeTarget(API_BASE).baseUrl;
    const isCurrentAuthority = parsed.baseUrl === currentBase;
    if (!isCurrentAuthority) {
      setResult({
        baseUrl: parsed.baseUrl,
        latencyMs: 0,
        backendOk: false,
        databaseOk: false,
        authOk: null,
        topology: null,
        error: 'Aucune requête n’est envoyée à une origine distante avant votre navigation explicite. Ouvrez ce serveur pour exécuter le diagnostic directement sur son origine.',
        crossOriginLimited: true,
      });
      return;
    }

    setBusy(true);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 6_000);
    const started = performance.now();

    try {
      const authToken = getRuntimeAuthToken();
      const [topologyResponse, dbResponse, authResponse] = await Promise.all([
        fetch(`${parsed.baseUrl}/api/health/topology`, {
          credentials: 'omit',
          cache: 'no-store',
          signal: controller.signal,
        }),
        fetch(`${parsed.baseUrl}/api/health/db`, {
          credentials: 'omit',
          cache: 'no-store',
          signal: controller.signal,
        }),
        fetch(`${parsed.baseUrl}/api/clinics/me`, {
          credentials: 'include',
          cache: 'no-store',
          signal: controller.signal,
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : undefined,
        }),
      ]);
      const topology = await topologyResponse.json().catch(() => null) as TopologyPayload | null;
      setResult({
        baseUrl: parsed.baseUrl,
        latencyMs: Math.max(1, Math.round(performance.now() - started)),
        backendOk: topologyResponse.ok,
        databaseOk: dbResponse.ok,
        authOk: authResponse.ok,
        topology,
        error: null,
        crossOriginLimited: false,
      });
    } catch (error) {
      setResult({
        baseUrl: parsed.baseUrl,
        latencyMs: Math.max(1, Math.round(performance.now() - started)),
        backendOk: false,
        databaseOk: false,
        authOk: null,
        topology: null,
        error: error instanceof DOMException && error.name === 'AbortError'
          ? 'Délai dépassé. Vérifiez que le serveur est démarré et joignable sur le réseau local.'
          : 'Le navigateur ne peut pas vérifier cette cible depuis l’autorité actuelle. Ouvrez cette adresse pour terminer le diagnostic directement sur ce serveur.',
        crossOriginLimited: true,
      });
    } finally {
      window.clearTimeout(timeout);
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void runProbe(API_BASE);
  }, [runProbe]);

  const currentBase = normalizeTarget(API_BASE).baseUrl;
  const targetBase = normalized.baseUrl;
  const isCurrentTarget = Boolean(targetBase && targetBase === currentBase);
  const canOpen = Boolean(targetBase && !normalized.error && !isCurrentTarget);
  const networkVerified = Boolean(result?.backendOk && result?.databaseOk);
  const currentAuthenticated = Boolean(isCurrentTarget && networkVerified && result?.authOk === true);
  const annexReady = Boolean(
    currentAuthenticated
    && result?.topology?.lanExposed
    && result?.topology?.tlsReady
    && result?.topology?.connectionUrl,
  );

  const openValidatedServer = () => {
    if (!canOpen || !targetBase) return;
    window.location.assign(`${targetBase}/control-center`);
  };

  return (
    <section data-control-center-topology className="relative z-10 mx-auto w-full max-w-5xl">
      <div className="rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite sm:p-6 lg:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex h-14 w-14 items-center justify-center rounded-elite-sm bg-primary/10 text-primary">
              <Network size={28} aria-hidden="true" />
            </div>
            <p className="mt-4 text-xs font-black uppercase tracking-widest text-primary">Digital Crown · Technique</p>
            <h1 className="mt-2 font-outfit text-3xl font-black tracking-tight sm:text-4xl">Connexion du poste au cabinet</h1>
            <p className="mt-2 text-sm font-semibold leading-relaxed text-text-muted">
              Vérifiez le serveur de ce poste ou saisissez l’adresse LAN du cabinet. Aucun identifiant ni donnée patient n’est envoyé à une autre origine avant votre action explicite.
            </p>
          </div>
          <StatusPill
            ok={networkVerified}
            label={
              annexReady
                ? 'Prêt pour poste annexe'
                : currentAuthenticated
                  ? 'Serveur local vérifié'
                  : networkVerified
                    ? 'Serveur joignable'
                    : 'À vérifier'
            }
          />
        </div>

        <div className="mt-5 rounded-elite-sm border border-border-main bg-main-bg p-4">
          <label className="block text-xs font-black uppercase tracking-wide text-text-muted" htmlFor="cabinet-server-target">
            Adresse du serveur cabinet
          </label>
          <div className="mt-2 grid gap-3 lg:grid-cols-[1fr_auto]">
            <input
              id="cabinet-server-target"
              data-control-center-target
              value={target}
              onChange={(event) => {
                setTarget(event.target.value);
                setInputError('');
                setResult(null);
              }}
              inputMode="url"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              aria-describedby="cabinet-server-help"
              aria-invalid={Boolean(inputError || normalized.error)}
              className="min-h-12 w-full rounded-elite-sm border border-border-main bg-card-bg px-4 text-sm font-bold text-main outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              placeholder="https://192.168.1.20:8005"
            />
            <button
              type="button"
              data-control-center-probe
              disabled={busy}
              onClick={() => void runProbe(target)}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-elite-sm bg-primary px-5 text-sm font-black text-on-primary transition-elite focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50"
            >
              {busy ? <Loader2 className="animate-spin" size={17} aria-hidden="true" /> : <RefreshCw size={17} aria-hidden="true" />}
              {busy ? 'Vérification…' : result && isCurrentTarget ? 'Relancer le diagnostic' : 'Vérifier maintenant'}
            </button>
          </div>
          <p id="cabinet-server-help" className="mt-2 text-xs font-semibold text-text-muted">
            Serveur actuellement ouvert : <span className="font-black text-main">{API_BASE}</span>
          </p>
          {(inputError || normalized.error) && <p role="alert" className="mt-3 text-sm font-black text-danger">{inputError || normalized.error}</p>}
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-elite-sm border border-border-main bg-main-bg p-3.5">
            <Server className="text-primary" size={20} aria-hidden="true" />
            <p className="mt-2 text-xs font-black uppercase tracking-wide text-text-muted">Backend</p>
            <p data-control-center-backend className="mt-1 text-lg font-black">{result?.backendOk ? 'Joignable' : busy ? 'Test…' : 'Non vérifié'}</p>
          </article>
          <article className="rounded-elite-sm border border-border-main bg-main-bg p-3.5">
            <Database className="text-primary" size={20} aria-hidden="true" />
            <p className="mt-2 text-xs font-black uppercase tracking-wide text-text-muted">Base de données</p>
            <p data-control-center-db className="mt-1 text-lg font-black">{result?.databaseOk ? 'Disponible' : busy ? 'Test…' : 'Non vérifiée'}</p>
          </article>
          <article className="rounded-elite-sm border border-border-main bg-main-bg p-3.5">
            <ShieldCheck className="text-primary" size={20} aria-hidden="true" />
            <p className="mt-2 text-xs font-black uppercase tracking-wide text-text-muted">Transport</p>
            <p data-control-center-transport className="mt-1 text-lg font-black">
              {result?.topology?.tlsReady ? 'Connexion sécurisée' : result?.topology?.lanExposed ? 'Action requise' : 'Local'}
            </p>
          </article>
          <article className="rounded-elite-sm border border-border-main bg-main-bg p-3.5">
            <ShieldCheck className="text-primary" size={20} aria-hidden="true" />
            <p className="mt-2 text-xs font-black uppercase tracking-wide text-text-muted">Session</p>
            <p data-control-center-auth className="mt-1 text-lg font-black">
              {result?.authOk === true ? 'Authentifiée' : result?.authOk === false ? 'Connexion requise' : 'Après ouverture'}
            </p>
          </article>
        </div>

        {result?.topology && (
          <details data-control-center-topology-details className="mt-4 rounded-elite-sm border border-border-main bg-main-bg p-3.5 text-sm">
            <summary className="cursor-pointer font-black text-main outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
              Détails techniques
              <span className="ml-2 font-semibold text-text-muted">· {result.latencyMs} ms</span>
            </summary>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div><span className="font-bold text-text-muted">Rôle</span><p className="mt-1 font-black">{result.topology.topologyRole || '—'}</p></div>
              <div><span className="font-bold text-text-muted">Adresse bind</span><p className="mt-1 font-black">{result.topology.bindHost || '—'}</p></div>
              <div><span className="font-bold text-text-muted">Port</span><p className="mt-1 font-black">{result.topology.port || '—'}</p></div>
              <div><span className="font-bold text-text-muted">Mode réseau</span><p className="mt-1 font-black">{result.topology.lanExposed ? 'LAN' : 'Local uniquement'}</p></div>
              <div className="sm:col-span-2 lg:col-span-4">
                <span className="font-bold text-text-muted">URL poste annexe</span>
                <p data-control-center-connection-url className="mt-1 break-all font-black">
                  {result.topology.connectionUrl || 'Non publiée — serveur limité au loopback'}
                </p>
              </div>
            </div>
          </details>
        )}

        <div data-control-center-remediation role="status" aria-live="polite" className="mt-4 rounded-elite-sm border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-start gap-3">
            <Globe2 className="mt-0.5 shrink-0 text-primary" size={20} aria-hidden="true" />
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-primary">Diagnostic & prochaine action</p>
              <p className="mt-2 text-sm font-bold leading-relaxed text-main">{remediationCopy(result)}</p>
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-end">
          {!isCurrentTarget && (
            <button
              type="button"
              onClick={() => window.location.assign('/hub?select=1')}
              className="inline-flex min-h-12 items-center justify-center rounded-elite-sm border border-border-main px-5 text-sm font-black text-main transition-elite hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Retour au Hub
            </button>
          )}
          <button
            type="button"
            data-control-center-open
            onClick={() => {
              if (isCurrentTarget) window.location.assign('/hub?select=1');
              else openValidatedServer();
            }}
            disabled={!isCurrentTarget && !canOpen}
            className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-elite-sm border px-5 text-sm font-black transition-elite focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${isCurrentTarget || canOpen ? 'border-primary bg-primary text-on-primary' : 'border-border-main bg-main-bg text-text-muted'}`}
          >
            {isCurrentTarget ? 'Continuer vers le Hub' : 'Ouvrir et vérifier'} <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
    </section>
  );
};
