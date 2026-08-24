from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    src = p.read_text()
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}")
    p.write_text(src.replace(old, new))


# ---------------------------------------------------------------------------
# One service worker only: Workbox owns the scope and never caches APIs.
# ---------------------------------------------------------------------------
replace_once(
    "frontend/src/main.tsx",
    """if ('serviceWorker' in navigator) {
  // Enregistre le SW Workbox (cache statique, pwa-sw.js) et le SW mobile custom (sw.js)
  registerSW({ immediate: true })
  navigator.serviceWorker.register('/sw.js').catch(() => {/* sw.js absent en dev Vite — normal */})
}
""",
    """if ('serviceWorker' in navigator) {
  // Un seul Service Worker Workbox pour le shell statique. Les données métier
  // et mutations offline restent exclusivement dans MobileStorage.
  registerSW({ immediate: true })
}
""",
)

replace_once(
    "frontend/vite.config.ts",
    """      filename: 'pwa-sw.js', // Nom distinct pour ne pas écraser public/sw.js (mobile custom SW)
""",
    """      filename: 'pwa-sw.js',
""",
)
replace_once(
    "frontend/vite.config.ts",
    """        // Pas de BackgroundSync Workbox : la file offline est gérée par MobileStorage (localforage)
        runtimeCaching: [
          {
            urlPattern: /^https?:\\/\\/.*\\/api\\/mobile\\/snapshot.*/i,
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'api-snapshot-cache',
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [0, 200] }
            }
          }
        ]
""",
    """        // Zéro cache API dans le SW : MobileStorage est la source offline métier unique.
        runtimeCaching: []
""",
)

sw = Path("frontend/public/sw.js")
if not sw.exists():
    raise SystemExit("frontend/public/sw.js missing before M6.2 removal")
sw.unlink()


# ---------------------------------------------------------------------------
# One app-level offline queue, scoped to the paired cabinet + device.
# ---------------------------------------------------------------------------
Path("frontend/src/services/zka/MobileStorage.ts").write_text("""import localforage from 'localforage';

/** Mobile ZKA persistence: credentials, last snapshot and the single offline queue. */
localforage.config({
  driver: localforage.INDEXEDDB,
  name: 'digital-crown-zka',
  version: 1.0,
  storeName: 'secure_keys',
});

const STORE_CREDENTIALS_ID = 'zka_credentials';
const STORE_SNAPSHOT_ID = 'zka_last_snapshot';
const STORE_ACTION_QUEUE_ID = 'zka_action_queue_v2';
const LEGACY_ACTION_QUEUE_ID = 'zka_action_queue';

export interface ZKACredentials {
  publicId: string;
  masterKey: string;
  access_token: string;
  refresh_token?: string;
  device_id?: string;
  api_base_url: string;
}

export interface QueuedAction {
  id: string;
  url: string;
  method: string;
  body?: any;
  timestamp: number;
  cabinetPublicId: string;
  deviceId: string;
}

let refreshInFlight: Promise<ZKACredentials | null> | null = null;

function resolveApiBaseUrl(stored: string): string {
  const normalized = stored.endsWith('/') ? stored.slice(0, -1) : stored;
  if (typeof window === 'undefined') return normalized;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return normalized;
  if (normalized.includes('localhost') || normalized.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return normalized;
}

function accessTokenExpiryMs(token: string): number | null {
  try {
    const segment = token.split('.')[1];
    if (!segment || typeof atob !== 'function') return null;
    const normalized = segment.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    const payload = JSON.parse(atob(padded));
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

async function rawCredentials(): Promise<ZKACredentials | null> {
  return localforage.getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
}

async function clearSessionData(): Promise<void> {
  await localforage.removeItem(STORE_CREDENTIALS_ID);
  await localforage.removeItem(STORE_SNAPSHOT_ID);
  await localforage.removeItem(STORE_ACTION_QUEUE_ID);
  await localforage.removeItem(LEGACY_ACTION_QUEUE_ID);
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
  } catch { /* ignore */ }
}

async function invalidateMobileSession(): Promise<null> {
  await clearSessionData();
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/mobile') && window.location.pathname !== '/mobile/onboarding') {
    window.location.replace('/mobile/onboarding');
  }
  return null;
}

async function refreshCredentialsInternal(creds: ZKACredentials): Promise<ZKACredentials | null> {
  if (!creds.refresh_token || !creds.device_id) return null;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const response = await fetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/refresh-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: creds.refresh_token }),
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) return invalidateMobileSession();
        return creds;
      }
      const payload = await response.json();
      if (!payload.access_token || !payload.refresh_token || payload.device_id !== creds.device_id) {
        return invalidateMobileSession();
      }
      return MobileStorage.updateTokens(payload.access_token, payload.refresh_token, payload.device_id);
    } catch {
      // Réseau indisponible : conserver la session locale. Ne jamais transformer
      // une panne réseau en révocation.
      return creds;
    }
  })().finally(() => { refreshInFlight = null; });

  return refreshInFlight;
}

export const MobileStorage = {
  async saveCredentials(creds: ZKACredentials): Promise<void> {
    if (!/^[0-9a-fA-F]{16}$/.test(creds.publicId)) throw new Error('ID Cabinet invalide.');
    if (!/^[0-9a-fA-F]{64}$/.test(creds.masterKey)) throw new Error('Clé Maître invalide.');
    if (!creds.access_token || !creds.refresh_token || !creds.device_id) {
      throw new Error('Session mobile durable incomplète.');
    }

    const previous = await rawCredentials();
    const scopeChanged = !previous || previous.publicId !== creds.publicId || previous.device_id !== creds.device_id;
    if (scopeChanged) {
      await localforage.removeItem(STORE_SNAPSHOT_ID);
      await localforage.removeItem(STORE_ACTION_QUEUE_ID);
    }
    // L'ancienne queue n'est jamais rejouée car elle n'était pas tenant/device-bound.
    await localforage.removeItem(LEGACY_ACTION_QUEUE_ID);

    await localforage.setItem(STORE_CREDENTIALS_ID, creds);
    try { localStorage.setItem('token', creds.access_token); } catch { /* ignore */ }
    try { await navigator.storage?.persist?.(); } catch { /* ignore */ }
  },

  async updateTokens(accessToken: string, refreshToken: string, deviceId: string): Promise<ZKACredentials | null> {
    const current = await rawCredentials();
    if (!current || current.device_id !== deviceId) return null;
    const next: ZKACredentials = {
      ...current,
      access_token: accessToken,
      refresh_token: refreshToken,
      device_id: deviceId,
    };
    await this.saveCredentials(next);
    return next;
  },

  async saveLastSnapshot(data: any): Promise<void> {
    await localforage.setItem(STORE_SNAPSHOT_ID, { data, saved_at: Date.now() });
  },

  async getLastSnapshot(): Promise<any | null> {
    const entry = await localforage.getItem<{ data: any; saved_at: number }>(STORE_SNAPSHOT_ID);
    return entry?.data ?? null;
  },

  async getCredentials(): Promise<ZKACredentials | null> {
    const creds = await rawCredentials();
    if (!creds) return null;
    if (!creds.refresh_token || !creds.device_id) return creds;

    const expiry = accessTokenExpiryMs(creds.access_token);
    if (expiry !== null && expiry > Date.now() + 60_000) return creds;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return creds;
    return refreshCredentialsInternal(creds);
  },

  async refreshCredentials(): Promise<ZKACredentials | null> {
    const creds = await rawCredentials();
    if (!creds) return null;
    return refreshCredentialsInternal(creds);
  },

  async clearCredentials(): Promise<void> {
    await localforage.removeItem(STORE_CREDENTIALS_ID);
    try { localStorage.removeItem('token'); localStorage.removeItem('refresh_token'); } catch { /* ignore */ }
  },

  async clearAll(): Promise<void> {
    await clearSessionData();
  },

  async isPaired(): Promise<boolean> {
    const creds = await this.getCredentials();
    return !!(creds?.publicId && creds?.masterKey && creds?.access_token && creds?.refresh_token && creds?.device_id);
  },

  async hasCachedSnapshot(): Promise<boolean> {
    return (await this.getLastSnapshot()) !== null;
  },

  async enqueueAction(url: string, method: string, body?: any, actionId?: string): Promise<string> {
    const creds = await rawCredentials();
    if (!creds?.device_id) throw new Error('Session mobile non appairée.');
    await localforage.removeItem(LEGACY_ACTION_QUEUE_ID);
    const queue = await this.getActionQueue();
    const id = actionId || (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
    const action: QueuedAction = {
      id,
      url,
      method,
      body,
      timestamp: Date.now(),
      cabinetPublicId: creds.publicId,
      deviceId: creds.device_id,
    };
    queue.push(action);
    await localforage.setItem(STORE_ACTION_QUEUE_ID, queue);
    return id;
  },

  async getActionQueue(): Promise<QueuedAction[]> {
    await localforage.removeItem(LEGACY_ACTION_QUEUE_ID);
    const creds = await rawCredentials();
    if (!creds?.device_id) return [];
    const queue = await localforage.getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    return queue.filter(a => a.cabinetPublicId === creds.publicId && a.deviceId === creds.device_id);
  },

  async clearActionQueue(): Promise<void> {
    await localforage.removeItem(STORE_ACTION_QUEUE_ID);
    await localforage.removeItem(LEGACY_ACTION_QUEUE_ID);
  },

  async removeActionFromQueue(id: string): Promise<void> {
    const queue = await localforage.getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    await localforage.setItem(STORE_ACTION_QUEUE_ID, queue.filter(a => a.id !== id));
  },
};
""")

Path("frontend/src/services/zka/mobileFetch.ts").write_text("""import { MobileStorage } from './MobileStorage';

function withMobileAuth(init: RequestInit, token: string): RequestInit {
  const headers = new Headers(init.headers ?? {});
  headers.set('Authorization', `Bearer ${token}`);
  return { ...init, headers };
}

/** Native fetch for paired mobile routes with one device-bound refresh retry on 401. */
export async function mobileFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const creds = await MobileStorage.getCredentials();
  if (!creds) throw new Error('Non appairé');

  const first = await fetch(input, withMobileAuth(init, creds.access_token));
  if (first.status !== 401) return first;

  const refreshed = await MobileStorage.refreshCredentials();
  if (!refreshed || refreshed.access_token === creds.access_token) return first;
  return fetch(input, withMobileAuth(init, refreshed.access_token));
}
""")


# ---------------------------------------------------------------------------
# Shared Axios client must never send a mobile token to /auth/refresh.
# ---------------------------------------------------------------------------
replace_once(
    "frontend/src/services/api.ts",
    "import toast from 'react-hot-toast';\n",
    "import toast from 'react-hot-toast';\nimport { MobileStorage } from './zka/MobileStorage';\n",
)
replace_once(
    "frontend/src/services/api.ts",
    """    // Auto-refresh/Sync on 401
    if (status === 401 && !original._retried && !original.url?.includes('/auth/')) {
""",
    """    // Une session mobile a un refresh device-bound distinct du refresh web.
    if (status === 401 && window.location.pathname.startsWith('/mobile') && !original._mobileRetried) {
      original._mobileRetried = true;
      const previousToken = localStorage.getItem('token');
      const refreshed = await MobileStorage.refreshCredentials();
      if (refreshed?.access_token && refreshed.access_token !== previousToken) {
        localStorage.setItem('token', refreshed.access_token);
        original.headers = original.headers ?? {};
        original.headers['Authorization'] = `Bearer ${refreshed.access_token}`;
        return api(original);
      }
      return Promise.reject(error);
    }

    // Auto-refresh/Sync web on 401
    if (status === 401 && !window.location.pathname.startsWith('/mobile') && !original._retried && !original.url?.includes('/auth/')) {
""",
)


# ---------------------------------------------------------------------------
# Dedicated mobile views use the same refresh-aware native client.
# ---------------------------------------------------------------------------
replace_once(
    "frontend/src/features/mobile/Dashboard/views/DentistsView.tsx",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\n",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\nimport { mobileFetch } from '../../../../services/zka/mobileFetch';\n",
)
replace_once(
    "frontend/src/features/mobile/Dashboard/views/DentistsView.tsx",
    "const res = await fetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/dentists`, {",
    "const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/dentists`, {",
)

replace_once(
    "frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\n",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\nimport { mobileFetch } from '../../../../services/zka/mobileFetch';\n",
)
replace_once(
    "frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx",
    "const res = await fetch(`${resolveApiBaseUrl(creds.api_base_url)}${path}`, {",
    "const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}${path}`, {",
)
replace_once(
    "frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx",
    """  // Le JWT mobile (365j, type=mobile) est accepté par get_current_user() au même
  // titre que le cookie desktop (backend/routers/auth.py) — verify_superadmin()
  // ne regarde que l'email résolu, donc les endpoints /api/superadmin/* existants
  // fonctionnent tels quels depuis le mobile, sans nouvelle route backend.
""",
    """  // Les endpoints SuperAdmin partagés réutilisent le JWT mobile user/device-bound.
  // mobileFetch renouvelle ce JWT via /api/mobile/refresh-token, jamais via /auth/refresh.
""",
)


# ---------------------------------------------------------------------------
# Dashboard: HTTP errors are real errors; only network exceptions are queued.
# ---------------------------------------------------------------------------
replace_once(
    "frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\n",
    "import { MobileStorage } from '../../../../services/zka/MobileStorage';\nimport { mobileFetch } from '../../../../services/zka/mobileFetch';\n",
)

hook = Path("frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts")
hsrc = hook.read_text().replace("await fetch(", "await mobileFetch(")

old_snapshot = """      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/snapshot?target_date=${selectedDate}`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `Erreur ${res.status}`);

      const rawRes = await res.json();
"""
new_snapshot = """      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/snapshot?target_date=${selectedDate}`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))).detail ?? `Erreur ${res.status}`;
        if (res.status === 401 || res.status === 403) {
          setError('Session mobile expirée ou révoquée');
          setSyncStatus('error');
          return;
        }
        setError(detail);
        setSyncStatus('error');
        return;
      }

      const rawRes = await res.json();
"""
if hsrc.count(old_snapshot) != 1:
    raise SystemExit(f"snapshot block count={hsrc.count(old_snapshot)}")
hsrc = hsrc.replace(old_snapshot, new_snapshot)

old_sync = """    for (const action of queue) {
      try {
        await mobileFetch(action.url, {
          method: action.method,
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${creds.access_token}`
          },
          body: action.body ? JSON.stringify(action.body) : undefined
        });
        await MobileStorage.removeActionFromQueue(action.id);
      } catch (err) {
        hasError = true;
      }
    }
"""
new_sync = """    for (const action of queue) {
      try {
        const res = await mobileFetch(action.url, {
          method: action.method,
          headers: {
            'Content-Type': 'application/json',
            'X-Mobile-Action-Id': action.id,
          },
          body: action.body ? JSON.stringify(action.body) : undefined,
        });
        if (!res.ok) {
          hasError = true;
          toast.error(`Synchronisation refusée (${res.status})`);
          break;
        }
        await MobileStorage.removeActionFromQueue(action.id);
      } catch {
        hasError = true;
        break;
      }
    }
"""
if hsrc.count(old_sync) != 1:
    raise SystemExit(f"sync block count={hsrc.count(old_sync)}")
hsrc = hsrc.replace(old_sync, new_sync)

old_status = """  const handleStatusChange = async (id: number, status: ApptStatus) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ status }),
      });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    } catch {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, 'PATCH', { status });
      setQueuedActionsCount(prev => prev + 1);
      toast('Mise à jour mise en attente (hors ligne)', { icon: '🔄' });
      
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    }
  };
"""
new_status = """  const handleStatusChange = async (id: number, status: ApptStatus) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    const actionId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${id}-status`;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-Mobile-Action-Id': actionId },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        toast.error(`Mise à jour refusée (${res.status})`);
        return;
      }
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    } catch {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, 'PATCH', { status }, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Mise à jour mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    }
  };
"""
if hsrc.count(old_status) != 1:
    raise SystemExit(f"status block count={hsrc.count(old_status)}")
hsrc = hsrc.replace(old_status, new_status)

old_delete = """  const handleDeleteAppt = async (id: number) => {
    if (!window.confirm(\"Supprimer ce rendez-vous ?\")) return;
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${creds.access_token}` }
      });
      fetchSnapshot();
      toast.success(\"Rendez-vous supprimé\");
    } catch (err) {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'DELETE');
      setQueuedActionsCount(prev => prev + 1);
      toast('Suppression mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.filter(a => a.id !== id),
      } : prev);
    }
  };
"""
new_delete = """  const handleDeleteAppt = async (id: number) => {
    if (!window.confirm(\"Supprimer ce rendez-vous ?\")) return;
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    const actionId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${id}-delete`;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'DELETE',
        headers: { 'X-Mobile-Action-Id': actionId },
      });
      if (!res.ok) {
        toast.error(`Suppression refusée (${res.status})`);
        return;
      }
      fetchSnapshot();
      toast.success(\"Rendez-vous supprimé\");
    } catch {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'DELETE', undefined, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Suppression mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.filter(a => a.id !== id),
      } : prev);
    }
  };
"""
if hsrc.count(old_delete) != 1:
    raise SystemExit(f"delete block count={hsrc.count(old_delete)}")
hsrc = hsrc.replace(old_delete, new_delete)

old_reschedule = """  const handleRescheduleAppt = async (id: number, newDate: string, newTime: string) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ datetime_start: `${newDate}T${newTime}:00` }),
      });
      fetchSnapshot();
      toast.success(\"Rendez-vous déplacé\");
    } catch (err) {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'PATCH', { datetime_start: `${newDate}T${newTime}:00` });
      setQueuedActionsCount(prev => prev + 1);
      toast('Déplacement mis en attente (hors ligne)', { icon: '🔄' });
    }
  };
"""
new_reschedule = """  const handleRescheduleAppt = async (id: number, newDate: string, newTime: string) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ datetime_start: `${newDate}T${newTime}:00` }),
      });
      if (!res.ok) {
        toast.error('Déplacement mobile indisponible — utilisez l’agenda principal.');
        return;
      }
      fetchSnapshot();
      toast.success(\"Rendez-vous déplacé\");
    } catch {
      // La route de déplacement mobile n'est pas encore canonique (M6.3) :
      // ne jamais mettre en queue une opération que le serveur ne sait pas rejouer.
      toast.error('Déplacement impossible hors ligne.');
    }
  };
"""
if hsrc.count(old_reschedule) != 1:
    raise SystemExit(f"reschedule block count={hsrc.count(old_reschedule)}")
hsrc = hsrc.replace(old_reschedule, new_reschedule)

old_lab = """    try {
      window.location.href = whatsappUri;
    } catch (e) {
      console.error('Échec de redirection WhatsApp', e);
    } finally {
      setLabJobs(prev => prev.map(j => j.id === job.id ? { ...j, status: LabJobStatus.SENT } : j));
      patchLabJobStatus(job.id, { status: LabJobStatus.SENT }).catch((err: any) => console.error('Erreur API:', err));
    }
"""
new_lab = """    try {
      window.location.href = whatsappUri;
      await patchLabJobStatus(job.id, { status: LabJobStatus.SENT });
      setLabJobs(prev => prev.map(j => j.id === job.id ? { ...j, status: LabJobStatus.SENT } : j));
    } catch (e) {
      console.error('Échec WhatsApp ou persistance Labo', e);
      toast.error('WhatsApp ouvert, mais statut Labo non confirmé.');
    }
"""
if hsrc.count(old_lab) != 1:
    raise SystemExit(f"lab block count={hsrc.count(old_lab)}")
hsrc = hsrc.replace(old_lab, new_lab)
hook.write_text(hsrc)


# ---------------------------------------------------------------------------
# Backend DELETE is tenant-scoped and idempotent for replay after lost response.
# ---------------------------------------------------------------------------
replace_once(
    "backend/routers/mobile_legacy.py",
    """    if not apt:
        raise HTTPException(status_code=404, detail='Introuvable')
    db.delete(apt)
    db.commit()
    return {'status': 'deleted'}
""",
    """    if not apt:
        # Idempotent replay: an already-absent tenant-scoped RDV is already deleted.
        return {'status': 'deleted', 'already_absent': True}
    db.delete(apt)
    db.commit()
    return {'status': 'deleted', 'already_absent': False}
""",
)

replace_once(
    "backend/tests/test_mobile_router.py",
    """    def test_delete_nonexistent_appointment(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.delete(
            "/api/mobile/appointments/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404
""",
    """    def test_delete_nonexistent_appointment_is_idempotent(self, client, db, dentiste):
        token = _make_mobile_jwt(db, dentiste)
        r = client.delete(
            "/api/mobile/appointments/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json() == {"status": "deleted", "already_absent": True}
""",
)


# ---------------------------------------------------------------------------
# Source-level truth gate matching the repository's existing Vitest pattern.
# ---------------------------------------------------------------------------
Path("frontend/src/test/mobileM62OfflineTruth.test.ts").write_text("""import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const read = (p: string) => fs.readFileSync(path.join(root, p), 'utf8');

describe('Mobile M6.2 offline truth', () => {
  it('uses one Workbox service worker and never caches mobile APIs', () => {
    const main = read('src/main.tsx');
    const vite = read('vite.config.ts');
    expect(main).not.toContain("serviceWorker.register('/sw.js')");
    expect(vite).toContain('runtimeCaching: []');
    expect(vite).not.toContain('api-snapshot-cache');
    expect(fs.existsSync(path.join(root, 'public/sw.js'))).toBe(false);
  });

  it('scopes the single app queue to cabinet and device', () => {
    const storage = read('src/services/zka/MobileStorage.ts');
    expect(storage).toContain("zka_action_queue_v2");
    expect(storage).toContain('cabinetPublicId');
    expect(storage).toContain('deviceId');
    expect(storage).toContain('LEGACY_ACTION_QUEUE_ID');
  });

  it('requires HTTP success before removing queued actions or showing mutation success', () => {
    const hook = read('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
    expect(hook).toContain("'X-Mobile-Action-Id': action.id");
    expect(hook).toContain('if (!res.ok)');
    expect(hook).toContain('await MobileStorage.removeActionFromQueue(action.id)');
    expect(hook).not.toContain("toast('Déplacement mis en attente (hors ligne)'");
  });

  it('does not mark a lab job SENT from a finally block', () => {
    const hook = read('src/features/mobile/Dashboard/hooks/useMobileDashboard.ts');
    const start = hook.indexOf('const handleWhatsAppSend');
    const end = hook.indexOf('const fetchSignatureDocs', start);
    const block = hook.slice(start, end);
    expect(block).toContain('await patchLabJobStatus');
    expect(block).not.toContain('finally');
  });

  it('routes mobile 401 refresh through the paired-device endpoint', () => {
    const api = read('src/services/api.ts');
    const mobileFetch = read('src/services/zka/mobileFetch.ts');
    expect(api).toContain('MobileStorage.refreshCredentials()');
    expect(api).toContain("!window.location.pathname.startsWith('/mobile')");
    expect(mobileFetch).toContain('first.status !== 401');
    expect(mobileFetch).toContain('MobileStorage.refreshCredentials()');
  });
});
""")

# Structural invariants before any staging commit.
assert not Path("frontend/public/sw.js").exists()
assert "serviceWorker.register('/sw.js')" not in Path("frontend/src/main.tsx").read_text()
assert "runtimeCaching: []" in Path("frontend/vite.config.ts").read_text()
assert "api-snapshot-cache" not in Path("frontend/vite.config.ts").read_text()
assert "zka_action_queue_v2" in Path("frontend/src/services/zka/MobileStorage.ts").read_text()
assert "X-Mobile-Action-Id" in Path("frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts").read_text()
assert "datetime_end" not in Path("backend/routers/mobile_legacy.py").read_text()[Path("backend/routers/mobile_legacy.py").read_text().index("@router.post('/appointments')"):Path("backend/routers/mobile_legacy.py").read_text().index("@router.delete('/appointments/{appointment_id}')")]
