import localforage from 'localforage';

localforage.config({
  driver: localforage.INDEXEDDB,
  name: 'digital-crown-zka',
  version: 1.0,
  storeName: 'secure_keys',
});

const STORE_CREDENTIALS_ID = 'zka_credentials';
const STORE_SNAPSHOT_ID = 'zka_last_snapshot';
const ACTION_QUEUE_KEY = 'zka_action_queue_v2';
const LEGACY_ACTION_QUEUE_KEY = 'zka_action_queue';

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
  idempotencyKey: string;
  cabinetPublicId: string;
  url: string;
  method: string;
  body?: unknown;
  timestamp: number;
}

function actionId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const MobileStorage = {
  async saveCredentials(creds: ZKACredentials): Promise<void> {
    if (!/^[0-9a-fA-F]{16}$/.test(creds.publicId)) throw new Error('ID Cabinet invalide.');
    if (!/^[0-9a-fA-F]{64}$/.test(creds.masterKey)) throw new Error('Clé Maître invalide.');
    if (!creds.access_token) throw new Error('Token mobile manquant.');
    const existing = await localforage.getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
    if (existing?.publicId && existing.publicId !== creds.publicId) {
      await localforage.removeItem(STORE_SNAPSHOT_ID);
      await localforage.removeItem(ACTION_QUEUE_KEY);
      await localforage.removeItem(LEGACY_ACTION_QUEUE_KEY);
    }
    await localforage.setItem(STORE_CREDENTIALS_ID, creds);
    try { await navigator.storage?.persist?.(); } catch { /* best effort */ }
  },

  async updateTokens(accessToken: string, refreshToken?: string, deviceId?: string): Promise<ZKACredentials | null> {
    const current = await this.getCredentials();
    if (!current) return null;
    const next: ZKACredentials = {
      ...current,
      access_token: accessToken,
      refresh_token: refreshToken ?? current.refresh_token,
      device_id: deviceId ?? current.device_id,
    };
    await this.saveCredentials(next);
    return next;
  },

  async saveLastSnapshot(data: unknown): Promise<void> {
    await localforage.setItem(STORE_SNAPSHOT_ID, { data, saved_at: Date.now() });
  },

  async getLastSnapshot(): Promise<unknown | null> {
    const entry = await localforage.getItem<{ data: unknown; saved_at: number }>(STORE_SNAPSHOT_ID);
    return entry?.data ?? null;
  },

  async getCredentials(): Promise<ZKACredentials | null> {
    return localforage.getItem<ZKACredentials>(STORE_CREDENTIALS_ID);
  },

  async clearCredentials(): Promise<void> {
    await localforage.removeItem(STORE_CREDENTIALS_ID);
  },

  async clearAll(): Promise<void> {
    await localforage.removeItem(STORE_CREDENTIALS_ID);
    await localforage.removeItem(STORE_SNAPSHOT_ID);
    await localforage.removeItem(ACTION_QUEUE_KEY);
    await localforage.removeItem(LEGACY_ACTION_QUEUE_KEY);
  },

  async isPaired(): Promise<boolean> {
    const creds = await this.getCredentials();
    return !!(creds?.publicId && creds?.masterKey && creds?.access_token);
  },

  async hasCachedSnapshot(): Promise<boolean> {
    return (await this.getLastSnapshot()) !== null;
  },

  async enqueueAction(url: string, method: string, body?: unknown): Promise<void> {
    const creds = await this.getCredentials();
    if (!creds?.publicId) throw new Error('Cabinet mobile non appairé.');
    const queue = await this.getActionQueue();
    const id = actionId();
    queue.push({
      id,
      idempotencyKey: id,
      cabinetPublicId: creds.publicId,
      url,
      method,
      body,
      timestamp: Date.now(),
    });
    await localforage.setItem(ACTION_QUEUE_KEY, queue);
  },

  async getActionQueue(): Promise<QueuedAction[]> {
    return (await localforage.getItem<QueuedAction[]>(ACTION_QUEUE_KEY)) || [];
  },

  async clearActionQueue(): Promise<void> {
    await localforage.removeItem(ACTION_QUEUE_KEY);
  },

  async removeActionFromQueue(id: string): Promise<void> {
    const queue = await this.getActionQueue();
    await localforage.setItem(ACTION_QUEUE_KEY, queue.filter((action) => action.id !== id));
  },
};
