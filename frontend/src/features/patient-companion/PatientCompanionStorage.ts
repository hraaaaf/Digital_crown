const DB_NAME = 'digital-crown-patient-companion';
const DB_VERSION = 2;
const STORE = 'vault';
const MEDIA_STORE = 'media';
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

export type PatientRelayBinding = {
  protocolVersion: 'dc-relay-v1';
  relayUrl: string;
  cabinetInboxId: string;
  cabinetWriteCapability: string;
  patientInboxId: string;
  patientReadCapability: string;
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
  relay?: PatientRelayBinding;
};

export type PatientPairing = {
  accessToken: string;
  context: PatientCompanionContext;
  pairedAt: string;
  expiresAt?: string;
  remoteTransport?: PatientRemoteTransportBinding;
};

export type PatientAppointment = {
  appointment_ref?: string;
  datetime_start: string;
  duration_minutes?: number | null;
  motif: string;
  status: string;
  scheduling_type?: string | null;
};

export type PatientAgendaRequestState = {
  id: string;
  operation: 'agenda.create' | 'agenda.reschedule' | 'agenda.cancel';
  state: 'local_queued' | 'remote_pending' | 'confirmed' | 'rejected';
  appointmentRef?: string;
  slotRef?: string;
  createdAt: string;
  updatedAt: string;
  errorCode?: string;
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

export type PatientEmergencyPhotoQueueState = {
  uploadId: string;
  state: 'local_pending' | 'remote_uploading' | 'remote_pending_ack' | 'received' | 'rejected';
  byteSize: number;
  capturedAt: string;
  createdAt: string;
  updatedAt: string;
  errorCode?: string;
};

export type PatientWalletSnapshot = {
  version: 1;
  accessId: string;
  syncedAt: string;
  appointments: PatientAppointment[];
  shares: PatientShare[];
  agendaRequests?: PatientAgendaRequestState[];
  emergencyPhotos?: PatientEmergencyPhotoQueueState[];
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
      if (!db.objectStoreNames.contains(MEDIA_STORE)) db.createObjectStore(MEDIA_STORE);
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

type MediaEnvelope = {
  version: 1;
  iv: Uint8Array<ArrayBuffer>;
  ciphertext: ArrayBuffer;
};

async function readMediaValue<T>(key: string): Promise<T | null> {
  const db = await openDb();
  try {
    return await new Promise<T | null>((resolve, reject) => {
      const tx = db.transaction(MEDIA_STORE, 'readonly');
      const request = tx.objectStore(MEDIA_STORE).get(key);
      request.onsuccess = () => resolve((request.result as T | undefined) ?? null);
      request.onerror = () => reject(request.error || new Error('Lecture média locale impossible.'));
    });
  } finally {
    db.close();
  }
}

async function writeMediaValue(key: string, value: unknown): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(MEDIA_STORE, 'readwrite');
      tx.objectStore(MEDIA_STORE).put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Écriture média locale impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Écriture média locale interrompue.'));
    });
  } finally {
    db.close();
  }
}

async function deleteMediaValue(key: string): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(MEDIA_STORE, 'readwrite');
      tx.objectStore(MEDIA_STORE).delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Suppression média locale impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Suppression média locale interrompue.'));
    });
  } finally {
    db.close();
  }
}

const emergencyMediaKey = (uploadId: string) => `pc07:${uploadId}`;
const emergencyMediaAad = (accessId: string, uploadId: string) =>
  new TextEncoder().encode(`digital-crown-pc07-media-v1:${accessId}:${uploadId}`);

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

  async saveAppointments(accessId: string, appointments: PatientAppointment[]): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const existing = current.cache[accessId];
    const snapshot: PatientWalletSnapshot = existing || {
      version: 1,
      accessId,
      syncedAt: new Date(0).toISOString(),
      appointments: [],
      shares: [],
    };
    const next: PatientCompanionVaultState = {
      ...current,
      cache: {
        ...current.cache,
        [accessId]: {
          ...snapshot,
          appointments,
          syncedAt: new Date().toISOString(),
        },
      },
    };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async saveAgendaRequests(accessId: string, agendaRequests: PatientAgendaRequestState[]): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const existing = current.cache[accessId];
    const snapshot: PatientWalletSnapshot = existing || {
      version: 1,
      accessId,
      syncedAt: new Date(0).toISOString(),
      appointments: [],
      shares: [],
    };
    const next: PatientCompanionVaultState = {
      ...current,
      cache: {
        ...current.cache,
        [accessId]: { ...snapshot, agendaRequests },
      },
    };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async saveEmergencyPhotoQueue(
    accessId: string,
    emergencyPhotos: PatientEmergencyPhotoQueueState[],
  ): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const existing = current.cache[accessId];
    const snapshot: PatientWalletSnapshot = existing || {
      version: 1,
      accessId,
      syncedAt: new Date(0).toISOString(),
      appointments: [],
      shares: [],
    };
    const next: PatientCompanionVaultState = {
      ...current,
      cache: {
        ...current.cache,
        [accessId]: { ...snapshot, emergencyPhotos },
      },
    };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async saveWallet(snapshot: PatientWalletSnapshot): Promise<PatientCompanionVaultState> {
    const current = await this.load();
    if (!current.pairings.some(item => item.context.access_id === snapshot.accessId)) {
      throw new Error('Contexte Patient Companion inconnu.');
    }
    const previous = current.cache[snapshot.accessId];
    const mergedSnapshot: PatientWalletSnapshot = {
      ...snapshot,
      ...(snapshot.agendaRequests === undefined && previous?.agendaRequests
        ? { agendaRequests: previous.agendaRequests }
        : {}),
      ...(snapshot.emergencyPhotos === undefined && previous?.emergencyPhotos
        ? { emergencyPhotos: previous.emergencyPhotos }
        : {}),
    };
    const next: PatientCompanionVaultState = {
      ...current,
      cache: { ...current.cache, [snapshot.accessId]: mergedSnapshot },
    };
    await writeValue(STATE_ID, await encryptState(next));
    return next;
  },

  async saveEmergencyPhotoBytes(accessId: string, uploadId: string, bytes: Uint8Array<ArrayBuffer>): Promise<void> {
    if (!bytes.byteLength) throw new Error('Photo locale vide.');
    const key = await getOrCreateDeviceKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv, additionalData: emergencyMediaAad(accessId, uploadId) },
      key,
      bytes,
    );
    const envelope: MediaEnvelope = { version: 1, iv, ciphertext };
    await writeMediaValue(emergencyMediaKey(uploadId), envelope);
    try { await navigator.storage?.persist?.(); } catch { /* best effort */ }
  },

  async readEmergencyPhotoBytes(accessId: string, uploadId: string): Promise<Uint8Array<ArrayBuffer> | null> {
    const envelope = await readMediaValue<MediaEnvelope>(emergencyMediaKey(uploadId));
    if (!envelope) return null;
    if (envelope.version !== 1) throw new Error('Média Patient Companion invalide.');
    const key = await readValue<CryptoKey>(DEVICE_KEY_ID);
    if (!key) throw new Error('Clé locale Patient Companion introuvable.');
    const clear = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: envelope.iv,
        additionalData: emergencyMediaAad(accessId, uploadId),
      },
      key,
      envelope.ciphertext,
    );
    return new Uint8Array(clear);
  },

  async deleteEmergencyPhotoBytes(uploadId: string): Promise<void> {
    await deleteMediaValue(emergencyMediaKey(uploadId));
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
