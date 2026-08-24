import localforage from 'localforage';

/** Mobile ZKA persistence: credentials, last snapshot and the single offline queue. */
let storageConfigured = false;

function mobileStore() {
  if (!storageConfigured) {
    // IndexedDB reste obligatoire pour les secrets mobiles. La configuration est
    // volontairement lazy : importer api.ts ne doit pas initialiser un driver de
    // stockage dans les contextes qui n'utilisent pas l'app mobile (SSR/tests).
    localforage.config({
      driver: localforage.INDEXEDDB,
      name: 'digital-crown-zka',
      version: 1.0,
      storeName: 'secure_keys',
    });
    storageConfigured = true;
  }
  return localforage;
}

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
  return mobileStore().getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
}

async function clearSessionData(): Promise<void> {
  await mobileStore().removeItem(STORE_CREDENTIALS_ID);
  await mobileStore().removeItem(STORE_SNAPSHOT_ID);
  await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
  await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
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
      await mobileStore().removeItem(STORE_SNAPSHOT_ID);
      await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
    }
    // L'ancienne queue n'est jamais rejouée car elle n'était pas tenant/device-bound.
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);

    await mobileStore().setItem(STORE_CREDENTIALS_ID, creds);
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
    await mobileStore().setItem(STORE_SNAPSHOT_ID, { data, saved_at: Date.now() });
  },

  async getLastSnapshot(): Promise<any | null> {
    const entry = await mobileStore().getItem<{ data: any; saved_at: number }>(STORE_SNAPSHOT_ID);
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
    await mobileStore().removeItem(STORE_CREDENTIALS_ID);
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
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
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
    await mobileStore().setItem(STORE_ACTION_QUEUE_ID, queue);
    return id;
  },

  async getActionQueue(): Promise<QueuedAction[]> {
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
    const creds = await rawCredentials();
    if (!creds?.device_id) return [];
    const queue = await mobileStore().getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    return queue.filter(a => a.cabinetPublicId === creds.publicId && a.deviceId === creds.device_id);
  },

  async clearActionQueue(): Promise<void> {
    await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
  },

  async removeActionFromQueue(id: string): Promise<void> {
    const queue = await mobileStore().getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    await mobileStore().setItem(STORE_ACTION_QUEUE_ID, queue.filter(a => a.id !== id));
  },
};
