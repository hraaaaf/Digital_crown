import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';

/** LAB-only. All credentials/session values stay in volatile React state. */
interface Visit {
  id: string; queue_id: string; status: string; version: number; queue_sequence: number | null;
}
interface QueueEvent { visit_ref: string; type: string; version: number; occurred_at_utc: string }
interface OperatorHints { roles: string[]; explicit_permissions: string[] }
type ApiFailure = Error & { status?: number };

const API = (() => {
  const raw = import.meta.env.DEV ? String(import.meta.env.VITE_QUEUE_CORE_LAB_API_URL || '') : '';
  if (!raw) return '/api/queue-core-lab';
  try {
    const url = new URL(raw);
    if (url.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(url.hostname) &&
        url.pathname === '/api/queue-core-lab') return url.href.replace(/\/$/, '');
  } catch { /* An untrusted configured URL never receives a credential. */ }
  return '/api/queue-core-lab';
})();

async function requestJSON<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(API + path, {
    ...options, cache: 'no-store', credentials: 'omit',
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    const error = new Error(
      response.status === 401 ? 'Session refusée (401)' :
      response.status === 403 ? 'Accès non autorisé (403)' : 'Erreur ' + response.status,
    ) as ApiFailure;
    error.status = response.status;
    throw error;
  }
  return await response.json() as T;
}

const actionByStatus: Record<string, { code: string; label: string } | undefined> = {
  PLANNED: { code: 'check_in', label: 'Enregistrer arrivée' },
  WAITING: { code: 'call', label: 'Appeler' },
  CALLED: { code: 'chair', label: 'Installer au fauteuil' },
  CHAIR: { code: 'done', label: 'Terminer' },
};

function canShowAction(status: string, hints: OperatorHints | null): boolean {
  // Display hint only. The server authorizes all actions from the live session.
  const action = actionByStatus[status]?.code;
  if (!action || !hints) return false;
  if (action === 'check_in') return hints.roles.includes('reception');
  if (action === 'call') return hints.roles.includes('staff');
  if (action === 'chair') return hints.roles.includes('staff') && hints.explicit_permissions.includes('queue.chair');
  if (action === 'done') return hints.roles.includes('staff') && hints.explicit_permissions.includes('queue.done');
  return false;
}

function parseSSE(buffer: string, onEvent: (value: QueueEvent) => void): string {
  let text = buffer;
  let boundary = text.indexOf('\n\n');
  while (boundary >= 0) {
    const fields = text.slice(0, boundary).split('\n');
    text = text.slice(boundary + 2);
    const field = fields.find(line => line.startsWith('data: '));
    if (field) {
      try {
        const item = JSON.parse(field.slice(6)) as QueueEvent;
        if (typeof item.visit_ref === 'string' && typeof item.type === 'string' &&
            typeof item.version === 'number') onEvent(item);
      } catch { /* Invalid frames cannot grant access. */ }
    }
    boundary = text.indexOf('\n\n');
  }
  return text.slice(-4096);
}

export function QueueCoreLabPane() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [hints, setHints] = useState<OperatorHints | null>(null);
  const [queue, setQueue] = useState('Q1');
  const [resource, setResource] = useState('R1');
  const [visits, setVisits] = useState<Visit[]>([]);
  const [events, setEvents] = useState<QueueEvent[]>([]);
  const [message, setMessage] = useState('Laboratoire : connexion requise');
  const [streamState, setStreamState] = useState('Flux non connecté');
  const [busy, setBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const tokenRef = useRef('');

  const keepSession = (value: string) => { tokenRef.current = value; setToken(value); };
  useEffect(() => () => { abortRef.current?.abort(); }, []);

  const refresh = async (activeToken = tokenRef.current) => {
    if (!activeToken) return;
    try {
      const result = await requestJSON<{ visits: Visit[] }>(
        '/v1/queues/' + encodeURIComponent(queue) + '/snapshot',
        { headers: { Authorization: 'Bearer ' + activeToken } },
      );
      setVisits(result.visits);
      setMessage('File actualisée');
    } catch (error) {
      const failure = error as ApiFailure;
      setMessage(failure.message);
      if (failure.status === 401) {
        abortRef.current?.abort(); keepSession(''); setHints(null); setVisits([]);
      }
    }
  };

  const signIn = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true);
    try {
      const result = await requestJSON<{ token: string; roles: string[]; explicit_permissions: string[] }>(
        '/v1/operators/session',
        { method: 'POST', body: JSON.stringify({ username, password }) },
      );
      if (!result.token || typeof result.token !== 'string') throw new Error('Session invalide');
      if (!Array.isArray(result.roles) || !Array.isArray(result.explicit_permissions)) {
        throw new Error('Droits de session absents');
      }
      keepSession(result.token);
      setHints({ roles: result.roles, explicit_permissions: result.explicit_permissions });
      setPassword(''); setEvents([]); setMessage('Opérateur connecté');
      await refresh(result.token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Connexion refusée');
    } finally { setBusy(false); }
  };

  const advance = async (visit: Visit) => {
    const action = actionByStatus[visit.status];
    if (!action || !token) return;
    setBusy(true);
    try {
      const result = await requestJSON<{ status: string; version: number }>(
        '/v1/visits/' + encodeURIComponent(visit.id) + '/commands',
        {
          method: 'POST', headers: { Authorization: 'Bearer ' + token },
          body: JSON.stringify({
            command: action.code, expected_version: visit.version,
            resource_id: ['call', 'chair'].includes(action.code) ? resource : null,
          }),
        },
      );
      setMessage(visit.id + ' : ' + result.status + ' v' + result.version);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Commande refusée');
    } finally { setBusy(false); }
  };

  const stopSSE = () => {
    abortRef.current?.abort(); abortRef.current = null;
    setStreamState('Flux arrêté');
  };

  const startSSE = async () => {
    if (!tokenRef.current || abortRef.current) return;
    const signal = new AbortController();
    abortRef.current = signal;
    setStreamState('Connexion SSE…');
    try {
      const response = await fetch(
        API + '/v1/queues/' + encodeURIComponent(queue) + '/stream',
        {
          headers: { Authorization: 'Bearer ' + tokenRef.current, Accept: 'text/event-stream' },
          credentials: 'omit', cache: 'no-store', signal: signal.signal,
        },
      );
      if (!response.ok || !response.body) {
        setStreamState('SSE refusé (' + response.status + ')');
        return;
      }
      setStreamState('SSE connecté');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (!signal.signal.aborted) {
        const packet = await reader.read();
        if (packet.done) break;
        buffer = parseSSE(buffer + decoder.decode(packet.value, { stream: true }), item => {
          setEvents(previous => [...previous.slice(-49), item]);
        });
      }
      if (!signal.signal.aborted) {
        // Unexpected stream closure may mean revocation. Hide all queue data
        // immediately; a user must reauthenticate before seeing new state.
        keepSession(''); setHints(null); setVisits([]); setEvents([]);
        setMessage('Flux SSE fermé : reconnexion obligatoire');
        setStreamState('Flux SSE fermé');
      }
    } catch {
      if (!signal.signal.aborted) {
        keepSession(''); setHints(null); setVisits([]); setEvents([]);
        setMessage('Flux SSE interrompu : reconnexion obligatoire');
        setStreamState('Flux SSE interrompu');
      }
    } finally {
      if (abortRef.current === signal) abortRef.current = null;
    }
  };

  const logout = async () => {
    stopSSE();
    const old = tokenRef.current;
    keepSession(''); setHints(null); setVisits([]); setEvents([]); setPassword('');
    if (old) {
      try {
        await requestJSON('/v1/operators/logout', {
          method: 'POST', headers: { Authorization: 'Bearer ' + old },
        });
      } catch { /* Local session is already wiped. */ }
    }
    setMessage('Déconnecté');
  };

  return (
    <main data-testid="queue-core-lab" className="mx-auto max-w-5xl space-y-6 p-4 sm:p-8 text-text-main">
      <header className="space-y-2">
        <p className="text-xs font-bold uppercase tracking-wide text-text-muted">Digital Crown · Queue Core V1.5</p>
        <h1 className="text-2xl font-black">Salle d’attente — laboratoire</h1>
        <p className="text-sm text-text-muted">Données synthétiques uniquement. Aucun dossier patient ni rendez-vous clinique modifié.</p>
      </header>

      <section className="space-y-4 rounded-2xl border border-border-main bg-card p-5" aria-label="Session opérateur">
        {token ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <strong className="text-sm">Opérateur : {username}</strong>
            <button onClick={() => void logout()} className="rounded-lg border border-border-main px-4 py-2 font-semibold">
              Se déconnecter
            </button>
          </div>
        ) : (
          <form onSubmit={signIn} className="grid items-end gap-3 sm:grid-cols-3">
            <label className="grid gap-1 text-sm font-semibold">
              Identifiant opérateur
              <input aria-label="Identifiant opérateur" value={username}
                onChange={event => setUsername(event.target.value)}
                autoComplete="username" required
                className="rounded-lg border border-border-main bg-input-field p-3 text-text-main" />
            </label>
            <label className="grid gap-1 text-sm font-semibold">
              Mot de passe
              <input aria-label="Mot de passe" value={password} type="password"
                onChange={event => setPassword(event.target.value)}
                autoComplete="current-password" required
                className="rounded-lg border border-border-main bg-input-field p-3 text-text-main" />
            </label>
            <button type="submit" disabled={busy}
              className="rounded-lg bg-primary px-5 py-3 font-bold text-on-primary disabled:opacity-50">
              Se connecter
            </button>
          </form>
        )}
        <p role="status" aria-live="polite" data-testid="queue-status" className="text-sm text-text-muted">{message}</p>
      </section>

      {token && (
        <>
          <section className="space-y-4 rounded-2xl border border-border-main bg-card p-5">
            <div className="flex flex-wrap items-end gap-3">
              <label className="grid gap-1 text-sm font-semibold">File
                <input aria-label="File" value={queue} maxLength={36}
                  onChange={event => setQueue(event.target.value)}
                  className="w-24 rounded-lg border border-border-main bg-input-field p-2" />
              </label>
              <label className="grid gap-1 text-sm font-semibold">Ressource
                <input aria-label="Ressource" value={resource} maxLength={36}
                  onChange={event => setResource(event.target.value)}
                  className="w-24 rounded-lg border border-border-main bg-input-field p-2" />
              </label>
              <button onClick={() => void refresh()}
                className="rounded-lg border border-border-main px-4 py-2 font-semibold">Actualiser</button>
            </div>
            <h2 className="font-bold">Visites de la file</h2>
            <ul aria-label="Visites" className="grid gap-3 sm:grid-cols-2">
              {visits.map(visit => (
                <li key={visit.id} data-testid={'visit-' + visit.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border-main bg-background p-4">
                  <div className="min-w-0">
                    <p className="font-bold">{visit.id}</p>
                    <p className="text-sm text-text-muted">
                      État : <span data-testid={'status-' + visit.id}>{visit.status}</span> · v{visit.version}
                    </p>
                  </div>
                  {canShowAction(visit.status, hints) && (
                    <button onClick={() => void advance(visit)} disabled={busy}
                      aria-label={actionByStatus[visit.status]?.label + ' ' + visit.id}
                      className="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-on-primary disabled:opacity-50">
                      {actionByStatus[visit.status]?.label}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-3 rounded-2xl border border-border-main bg-card p-5" aria-label="Événements SSE">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="font-bold">Événements SSE</h2>
              <button onClick={() => void startSSE()}
                className="rounded-lg border border-border-main px-4 py-2 text-sm font-semibold">
                Écouter SSE
              </button>
              <button onClick={stopSSE} className="rounded-lg border border-border-main px-4 py-2 text-sm font-semibold">
                Arrêter SSE
              </button>
            </div>
            <p role="status" aria-live="polite" data-testid="stream-status"
              className="text-sm text-text-muted">{streamState}</p>
            <ol aria-label="Journal SSE" className="max-h-56 space-y-1 overflow-auto text-sm">
              {events.map((item, index) => (
                <li key={item.visit_ref + '-' + item.version + '-' + index}>
                  {item.visit_ref} · {item.type} · v{item.version}
                </li>
              ))}
            </ol>
          </section>
        </>
      )}
    </main>
  );
}

export default QueueCoreLabPane;
