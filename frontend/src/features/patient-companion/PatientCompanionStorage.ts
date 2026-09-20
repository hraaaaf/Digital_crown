const DB_NAME = 'digital-crown-patient-companion';
const DB_VERSION = 1;
const STORE = 'vault';
const DEVICE_KEY_ID = 'device-aes-key';
const STATE_ID = 'companion-state';

export type PatientCompanionContext = {
  access_id: string;
  relationship_type: string;
  patient: {
    display_name?: string;
    prenom?: string;
    nom?: string;
  };
};

export type PatientRemoteTransportBinding = {
  version: 1;
  keysetId: string;
  signingKid: string;
  encryptionKid: string;
  cabinetSigningKid: string;
  cabinetSigningPublicJwk: JsonWebKey;
  cabinetEncryptionKid: string;
  cabinetEncryptionPublicJwk: JsonWebKey;
};

export type PatientPairing = {
  accessToken: string;
  context: PatientCompanionContext;
  pairedAt: string;
  expiresAt?: string;
  remoteTransport?: PatientRemoteTransportBinding;
};

export type PatientAppointment = {
  datetime_start: string;
  duration_minutes?: number | null;
  motif: string;
  status: string;
  scheduling_type?: string | null;
};

export type PatientShare = {
  share_id: string;
  resource_type: 'document' | 'media';
  title?: string | null;
  document_type?: string | null;
  asset_type?: string | null;
  mime_type?: string | null;
  captured_at?: string | null;
  created_at?: string | null;
};

export type PatientWalletSnapshot = {
  version: 1;
  accessId: string;
  syncedAt: string;
  appointments: PatientAppointment[];
  shares: PatientShare[];
};

export type PatientCompanionVaultState = {
  version: 1;
  activeAccessId: string | null;
  pairings: PatientPairing[];
  cache: Record<string, PatientWalletSnapshot>;
};

type VaultEnvelope = {
  version: 1;
  iv: string;
  ciphertext: string;
};

function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (const value of bytes) binary += String.fromCharCode(value);
  return btoa(binary);
}

function base64ToBytes(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const output = new Uint8Array(new ArrayBuffer(binary.length));
  for (let index = 0; index < binary.length; index += 1) output[index] = binary.charCodeAt(index);
  return output;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Coffre Patient Companion indisponible.'));
  });
}

async function readValue<T>(key: string): Promise<T | null> {
  const db = await openDb();
  try {
    return await new Promise<T | null>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const request = tx.objectStore(STORE).get(key);
      request.onsuccess = () => resolve((request.result as T | undefined) ?? null);
      request.onerror = () => reject(request.error || new Error('Lecture du coffre impossible.'));
    });
  } finally {
    db.close();
  }
}

async function writeValue(key: string, value: unknown): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Écriture du coffre impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Écriture du coffre interrompue.'));
    });
  } finally {
    db.close();
  }
}

async function deleteValue(key: string): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Suppression du coffre impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Suppression du coffre interrompue.'));
    });
  } finally {
    db.close();
  }
}

async function getOrCreateDeviceKey(): Promise<CryptoKey> {
  const existing = await readValue<CryptoKey>(DEVICE_KEY_ID);
  if (existing) return existing;
  const key = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
  await writeValue(DEVICE_KEY_ID, key);
  return key;
}

async function encryptState(state: PatientCompanionVaultState): Promise<VaultEnvelope> {
  const key = await getOrCreateDeviceKey();
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const clear = new TextEncoder().encode(JSON.stringify(state));
  const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, clear);
  return {
    version: 1,
    iv: bytesToBase64(iv),
    ciphertext: bytesToBase64(new Uint8Array(encrypted)),
  };
}

async function decryptState(envelope: VaultEnvelope): Promise<PatientCompanionVaultState> {
  const key = await readValue<CryptoKey>(DEVICE_KEY_ID);
  if (!key) throw new Error('Clé locale Patient Companion introuvable.');
  const clear = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(envelope.iv) },
    key,
    base64ToBytes(envelope.ciphertext),
  );
  const state = JSON.parse(new TextDecoder().decode(clear)) as PatientCompanionVaultState;
  if (state.version !== 1 || !Array.isArray(state.pairings)) throw new Error('Coffre Patient Companion invalide.');
  return state;
}

function decodeJwtExpiry(rawToken: string): string {
  try {
    const [, payload] = rawToken.split('.');
    if (!payload) throw new Error('payload missing');
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(payload.length / 4) * 4, '=');
    const decoded = JSON.parse(atob(normalized)) as { exp?: number };
    if (!decoded.exp || !Number.isFinite(decoded.exp)) throw new Error('exp missing');
    return new Date(decoded.exp * 1000).toISOString();
  } catch {
    throw new Error('Session Patient Companion invalide.');
  }
}

function normalizePairing(pairing: PatientPairing): PatientPairing {
  return {
    ...pairing,
    expiresAt: pairing.expiresAt || decodeJwtExpiry(pairing.accessToken),
  };
}

function migrateState(state: PatientCompanionVaultState): PatientCompanionVaultState {
  return {
    ...state,
    pairings: state.pairings.map(pairing => {
      if (pairing.expiresAt) return pairing;
      try {
        return normalizePairing(pairing);
      } catch {
        return pairing;
      }
    }),
    cache: state.cache || {},
  };
}

const emptyState = (): PatientCompanionVaultState => ({
  version: 1,
  activeAccessId: null,
  pairings: [],
  cache: {},
});

export const PatientCompanionStorage = {
  async load(): Promise<PatientCompanionVaultState> {
    const envelope = await readValue<VaultEnvelope>(STATE_ID);
    return envelope ? migrateState(await decryptState(envelope)) : emptyState();
  },

  async savePairing(pairing: PatientPairing): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    const normalized = normalizePairing(pairing);
    const pairings = [
      ...current.pairings.filter(item => item.context.access_id !== normalized.context.access_id),
      normalized,
    ];
    const next: PatientCompanionVaultState = {
      ...current,
      activeAccessId: normalized.context.access_id,
      pairings,
    };
    await writeValue(STATE_ID, await encryptState(next));
    try { await navigator.storage?.persist?.(); } catch { /* best effort */ }
    return next;
  },

  async setActive(accessId: string): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const next = { ...current, activeAccessId: accessId };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async saveWallet(snapshot: PatientWalletSnapshot): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === snapshot.accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const next: PatientCompanionVaultState = {
      ...current,
      cache: { ...current.cache, [snapshot.accessId]: snapshot },
    };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async clear(): Promise<void> {
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.deleteDatabase(DB_NAME);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error || new Error('Suppression du coffre Patient Companion impossible.'));
      request.onblocked = () => reject(new Error('Suppression du coffre Patient Companion bloquée.'));
    });
  },
};
