import localforage from 'localforage';

/** Mobile ZKA persistence: credentials, encrypted local vault, bridge context and offline queue. */
let storageConfigured = false;

function mobileStore() {
  if (!storageConfigured) {
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
const STORE_BRIDGE_CONTEXT_ID = 'zka_bridge_context';
const STORE_ACTION_QUEUE_ID = 'zka_action_queue_v2';
const LEGACY_ACTION_QUEUE_ID = 'zka_action_queue';
const STORE_BIOMETRIC_VAULT_ID = 'zka_biometric_vault_v1';

export interface ZKACredentials {
  publicId: string;
  masterKey: string;
  access_token: string;
  refresh_token?: string;
  device_id?: string;
  api_base_url: string;
}

export interface MobileBridgeContext {
  type: string;
  key: string;
  label?: string;
  state: 'ready' | 'unavailable';
  reason?: string | null;
  cabinetPublicId?: string;
  deviceId?: string;
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

interface SnapshotEntry {
  data: any;
  saved_at: number;
}

interface BiometricVaultPayload {
  masterKey: string;
  snapshot: SnapshotEntry | null;
  bridgeContext: MobileBridgeContext | null;
  actionQueue: QueuedAction[];
}

export interface BiometricVaultEnvelope {
  version: 1;
  credential_id: string;
  prf_salt: string;
  publicId: string;
  deviceId: string;
  iv: string;
  ciphertext: string;
  has_snapshot: boolean;
}

let refreshInFlight: Promise<ZKACredentials | null> | null = null;
let biometricAccessToken: string | null = null;
let unlockedVault: { key: CryptoKey; payload: BiometricVaultPayload; envelope: BiometricVaultEnvelope } | null = null;

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = '';
  for (const value of bytes) binary += String.fromCharCode(value);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function base64UrlToBytes(value: string): Uint8Array<ArrayBuffer> {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  const binary = atob(padded);
  const output = new Uint8Array(new ArrayBuffer(binary.length));
  for (let index = 0; index < binary.length; index += 1) output[index] = binary.charCodeAt(index);
  return output;
}

export function resolveMobileApiBaseUrl(stored: string): string {
  const normalized = stored.endsWith('/') ? stored.slice(0, -1) : stored;
  if (typeof window === 'undefined') return normalized;
  const hostname = window.location.hostname;
  if (hostname === 'digitalcrown.local' || hostname.endsWith('.digitalcrown.local')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
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

async function rawVault(): Promise<BiometricVaultEnvelope | null> {
  return mobileStore().getItem<BiometricVaultEnvelope>(STORE_BIOMETRIC_VAULT_ID);
}

async function importPrfKey(prfOutput: ArrayBuffer | Uint8Array): Promise<CryptoKey> {
  const source = prfOutput instanceof Uint8Array ? prfOutput : new Uint8Array(prfOutput);
  if (source.byteLength !== 32) throw new Error('Sortie PRF invalide.');
  const bytes = new Uint8Array(new ArrayBuffer(source.byteLength));
  bytes.set(source);
  return crypto.subtle.importKey('raw', bytes, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

async function encryptVaultPayload(key: CryptoKey, payload: BiometricVaultPayload): Promise<{ iv: string; ciphertext: string }> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const clear = new TextEncoder().encode(JSON.stringify(payload));
  const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, clear);
  return { iv: bytesToBase64Url(iv), ciphertext: bytesToBase64Url(new Uint8Array(encrypted)) };
}

async function decryptVaultPayload(key: CryptoKey, envelope: BiometricVaultEnvelope): Promise<BiometricVaultPayload> {
  const clear = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64UrlToBytes(envelope.iv) },
    key,
    base64UrlToBytes(envelope.ciphertext),
  );
  const payload = JSON.parse(new TextDecoder().decode(clear)) as BiometricVaultPayload;
  if (!/^[0-9a-fA-F]{64}$/.test(payload.masterKey)) throw new Error('Coffre biométrique corrompu.');
  if (!Array.isArray(payload.actionQueue)) throw new Error('Coffre biométrique corrompu.');
  return payload;
}

async function persistUnlockedVault(): Promise<void> {
  if (!unlockedVault) throw new Error('Coffre biométrique verrouillé.');
  const encrypted = await encryptVaultPayload(unlockedVault.key, unlockedVault.payload);
  const envelope: BiometricVaultEnvelope = {
    ...unlockedVault.envelope,
    ...encrypted,
    has_snapshot: unlockedVault.payload.snapshot !== null,
  };
  await mobileStore().setItem(STORE_BIOMETRIC_VAULT_ID, envelope);
  unlockedVault.envelope = envelope;
}

async function sanitizePlaintextCopies(creds: ZKACredentials): Promise<void> {
  const envelope = await rawVault();
  if (!envelope) return;
  if (creds.masterKey) {
    await mobileStore().setItem(STORE_CREDENTIALS_ID, { ...creds, masterKey: '' });
  }
  await mobileStore().removeItem(STORE_SNAPSHOT_ID);
  await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
  await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
  await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
}

async function clearSessionData(): Promise<void> {
  await mobileStore().removeItem(STORE_CREDENTIALS_ID);
  await mobileStore().removeItem(STORE_SNAPSHOT_ID);
  await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
  await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
  await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
  await mobileStore().removeItem(STORE_BIOMETRIC_VAULT_ID);
  biometricAccessToken = null;
  unlockedVault = null;
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
      const response = await fetch(`${resolveMobileApiBaseUrl(creds.api_base_url)}/api/mobile/refresh-token`, {
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
      return creds;
    }
  })().finally(() => { refreshInFlight = null; });

  return refreshInFlight;
}

export const MobileStorage = {
  async saveCredentials(creds: ZKACredentials): Promise<void> {
    if (!/^[0-9a-fA-F]{16}$/.test(creds.publicId)) throw new Error('ID Cabinet invalide.');
    const existingVault = await rawVault();
    if (!/^[0-9a-fA-F]{64}$/.test(creds.masterKey) && !(existingVault && creds.masterKey === '')) {
      throw new Error('Clé Maître invalide.');
    }
    if (!creds.access_token || !creds.refresh_token || !creds.device_id) {
      throw new Error('Session mobile durable incomplète.');
    }

    const previous = await rawCredentials();
    const scopeChanged = !previous || previous.publicId !== creds.publicId || previous.device_id !== creds.device_id;
    if (scopeChanged) {
      await mobileStore().removeItem(STORE_SNAPSHOT_ID);
      await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
      await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
      await mobileStore().removeItem(STORE_BIOMETRIC_VAULT_ID);
      unlockedVault = null;
      biometricAccessToken = null;
    }
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
    return this.getCredentials();
  },

  async saveLastSnapshot(data: any): Promise<void> {
    const envelope = await rawVault();
    if (envelope) {
      if (!unlockedVault) throw new Error('Coffre biométrique verrouillé.');
      unlockedVault.payload.snapshot = { data, saved_at: Date.now() };
      await persistUnlockedVault();
      return;
    }
    await mobileStore().setItem(STORE_SNAPSHOT_ID, { data, saved_at: Date.now() });
  },

  async getLastSnapshot(): Promise<any | null> {
    const envelope = await rawVault();
    if (envelope) return unlockedVault?.payload.snapshot?.data ?? null;
    const entry = await mobileStore().getItem<SnapshotEntry>(STORE_SNAPSHOT_ID);
    return entry?.data ?? null;
  },

  async saveBridgeContext(context: MobileBridgeContext): Promise<void> {
    const creds = await rawCredentials();
    if (!creds?.device_id) throw new Error('Session mobile non appairée.');
    if (!context.key || !context.type) throw new Error('Contexte mobile invalide.');
    const scoped = { ...context, cabinetPublicId: creds.publicId, deviceId: creds.device_id };
    if (await rawVault()) {
      if (!unlockedVault) throw new Error('Coffre biométrique verrouillé.');
      unlockedVault.payload.bridgeContext = scoped;
      await persistUnlockedVault();
      return;
    }
    await mobileStore().setItem(STORE_BRIDGE_CONTEXT_ID, scoped);
  },

  async getBridgeContext(): Promise<MobileBridgeContext | null> {
    const creds = await rawCredentials();
    if (!creds?.device_id) return null;
    const context = (await rawVault())
      ? unlockedVault?.payload.bridgeContext ?? null
      : await mobileStore().getItem<MobileBridgeContext>(STORE_BRIDGE_CONTEXT_ID);
    if (!context) return null;
    if (context.cabinetPublicId !== creds.publicId || context.deviceId !== creds.device_id) {
      await this.clearBridgeContext();
      return null;
    }
    return context;
  },

  async clearBridgeContext(): Promise<void> {
    if (await rawVault()) {
      if (!unlockedVault) return;
      unlockedVault.payload.bridgeContext = null;
      await persistUnlockedVault();
      return;
    }
    await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
  },

  async getCredentials(): Promise<ZKACredentials | null> {
    let creds = await rawCredentials();
    if (!creds) return null;
    const envelope = await rawVault();
    if (envelope) {
      await sanitizePlaintextCopies(creds);
      creds = { ...creds, masterKey: unlockedVault?.payload.masterKey ?? '' };
    }
    if (!creds.refresh_token || !creds.device_id) return { ...creds, api_base_url: resolveMobileApiBaseUrl(creds.api_base_url) };

    const expiry = accessTokenExpiryMs(creds.access_token);
    if (expiry !== null && expiry <= Date.now() + 60_000 && (typeof navigator === 'undefined' || navigator.onLine !== false)) {
      const refreshed = await refreshCredentialsInternal(creds);
      if (!refreshed) return null;
      creds = refreshed;
    }
    return { ...creds, api_base_url: resolveMobileApiBaseUrl(creds.api_base_url) };
  },

  async refreshCredentials(): Promise<ZKACredentials | null> {
    const creds = await rawCredentials();
    if (!creds) return null;
    return refreshCredentialsInternal(creds);
  },

  async clearCredentials(): Promise<void> {
    await mobileStore().removeItem(STORE_CREDENTIALS_ID);
    await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
    await mobileStore().removeItem(STORE_BIOMETRIC_VAULT_ID);
    unlockedVault = null;
    biometricAccessToken = null;
    try { localStorage.removeItem('token'); localStorage.removeItem('refresh_token'); } catch { /* ignore */ }
  },

  async clearAll(): Promise<void> {
    await clearSessionData();
  },

  async isPaired(): Promise<boolean> {
    const creds = await this.getCredentials();
    if (!creds) return false;
    const vault = await rawVault();
    const masterReady = /^[0-9a-fA-F]{64}$/.test(creds.masterKey) || vault !== null;
    return !!(creds.publicId && masterReady && creds.access_token && creds.refresh_token && creds.device_id);
  },

  async hasCachedSnapshot(): Promise<boolean> {
    const vault = await rawVault();
    if (vault) return vault.has_snapshot;
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
    if (await rawVault()) {
      if (!unlockedVault) throw new Error('Coffre biométrique verrouillé.');
      unlockedVault.payload.actionQueue = queue;
      await persistUnlockedVault();
      return id;
    }
    await mobileStore().setItem(STORE_ACTION_QUEUE_ID, queue);
    return id;
  },

  async getActionQueue(): Promise<QueuedAction[]> {
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
    const creds = await rawCredentials();
    if (!creds?.device_id) return [];
    const queue: QueuedAction[] = (await rawVault())
      ? unlockedVault?.payload.actionQueue ?? []
      : await mobileStore().getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    return queue.filter(a => a.cabinetPublicId === creds.publicId && a.deviceId === creds.device_id);
  },

  async clearActionQueue(): Promise<void> {
    if (await rawVault()) {
      if (!unlockedVault) return;
      unlockedVault.payload.actionQueue = [];
      await persistUnlockedVault();
    } else {
      await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
    }
    await mobileStore().removeItem(LEGACY_ACTION_QUEUE_ID);
  },

  async removeActionFromQueue(id: string): Promise<void> {
    if (await rawVault()) {
      if (!unlockedVault) return;
      unlockedVault.payload.actionQueue = unlockedVault.payload.actionQueue.filter(a => a.id !== id);
      await persistUnlockedVault();
      return;
    }
    const queue: QueuedAction[] = await mobileStore().getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [];
    await mobileStore().setItem(STORE_ACTION_QUEUE_ID, queue.filter(a => a.id !== id));
  },

  setBiometricAccessToken(token: string | null): void {
    biometricAccessToken = token;
  },

  getBiometricAccessToken(): string | null {
    return biometricAccessToken;
  },

  clearBiometricAccessToken(): void {
    biometricAccessToken = null;
  },

  async getBiometricVaultEnvelope(): Promise<BiometricVaultEnvelope | null> {
    return rawVault();
  },

  async isBiometricVaultUnlocked(): Promise<boolean> {
    return unlockedVault !== null;
  },

  async sealBiometricVault(input: { credentialId: string; prfSalt: string; prfOutput: ArrayBuffer | Uint8Array }): Promise<void> {
    const creds = await rawCredentials();
    if (!creds?.device_id || !/^[0-9a-fA-F]{64}$/.test(creds.masterKey)) {
      throw new Error('Clé maître indisponible pour le scellement biométrique.');
    }
    const key = await importPrfKey(input.prfOutput);
    const payload: BiometricVaultPayload = {
      masterKey: creds.masterKey,
      snapshot: await mobileStore().getItem<SnapshotEntry>(STORE_SNAPSHOT_ID),
      bridgeContext: await mobileStore().getItem<MobileBridgeContext>(STORE_BRIDGE_CONTEXT_ID),
      actionQueue: await mobileStore().getItem<QueuedAction[]>(STORE_ACTION_QUEUE_ID) || [],
    };
    const encrypted = await encryptVaultPayload(key, payload);
    const envelope: BiometricVaultEnvelope = {
      version: 1,
      credential_id: input.credentialId,
      prf_salt: input.prfSalt,
      publicId: creds.publicId,
      deviceId: creds.device_id,
      ...encrypted,
      has_snapshot: payload.snapshot !== null,
    };
    await mobileStore().setItem(STORE_BIOMETRIC_VAULT_ID, envelope);
    unlockedVault = { key, payload, envelope };
    await sanitizePlaintextCopies(creds);
  },

  async unlockBiometricVault(prfOutput: ArrayBuffer | Uint8Array): Promise<void> {
    const envelope = await rawVault();
    const creds = await rawCredentials();
    if (!envelope || !creds?.device_id) throw new Error('Coffre biométrique introuvable.');
    if (envelope.publicId !== creds.publicId || envelope.deviceId !== creds.device_id) {
      throw new Error('Coffre biométrique incompatible avec cet appareil.');
    }
    const key = await importPrfKey(prfOutput);
    const payload = await decryptVaultPayload(key, envelope);
    unlockedVault = { key, payload, envelope };
    await sanitizePlaintextCopies(creds);
  },

  lockBiometricVault(): void {
    unlockedVault = null;
    biometricAccessToken = null;
  },

  async disableBiometricVault(): Promise<void> {
    if (!unlockedVault) throw new Error('Coffre biométrique verrouillé.');
    const creds = await rawCredentials();
    if (!creds?.device_id) throw new Error('Session mobile non appairée.');
    const payload = unlockedVault.payload;
    await mobileStore().setItem(STORE_CREDENTIALS_ID, { ...creds, masterKey: payload.masterKey });
    if (payload.snapshot) await mobileStore().setItem(STORE_SNAPSHOT_ID, payload.snapshot);
    else await mobileStore().removeItem(STORE_SNAPSHOT_ID);
    if (payload.bridgeContext) await mobileStore().setItem(STORE_BRIDGE_CONTEXT_ID, payload.bridgeContext);
    else await mobileStore().removeItem(STORE_BRIDGE_CONTEXT_ID);
    if (payload.actionQueue.length) await mobileStore().setItem(STORE_ACTION_QUEUE_ID, payload.actionQueue);
    else await mobileStore().removeItem(STORE_ACTION_QUEUE_ID);
    await mobileStore().removeItem(STORE_BIOMETRIC_VAULT_ID);
    unlockedVault = null;
    biometricAccessToken = null;
  },
};
