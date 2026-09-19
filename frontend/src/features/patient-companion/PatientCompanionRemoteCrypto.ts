import {
  CompactEncrypt,
  CompactSign,
  compactDecrypt,
  compactVerify,
  importJWK,
} from 'jose';
import type { PatientRemoteTransportBinding } from './PatientCompanionStorage';

const DB_NAME = 'digital-crown-patient-companion';
const DB_VERSION = 1;
const STORE = 'vault';

const JWS_ALG = 'ES256';
const JWE_ALG = 'ECDH-ES+A256KW';
const JWE_ENC = 'A256GCM';
const JWS_TYP = 'application/dc-pc+jws';
const JWE_TYP = 'application/dc-pc+jwe';
const JWE_CTY = JWS_TYP;

const encoder = new TextEncoder();
const decoder = new TextDecoder();

export type PreparedRemoteEnrollment = {
  signingKid: string;
  encryptionKid: string;
  request: {
    signing_kid: string;
    signing_public_jwk: JsonWebKey;
    encryption_kid: string;
    encryption_public_jwk: JsonWebKey;
  };
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Coffre cryptographique distant indisponible.'));
  });
}

async function readKey(id: string): Promise<CryptoKey | null> {
  const db = await openDb();
  try {
    return await new Promise<CryptoKey | null>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const request = tx.objectStore(STORE).get(id);
      request.onsuccess = () => resolve((request.result as CryptoKey | undefined) ?? null);
      request.onerror = () => reject(request.error || new Error('Lecture de clé distante impossible.'));
    });
  } finally {
    db.close();
  }
}

async function writeKey(id: string, key: CryptoKey): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(key, id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Écriture de clé distante impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Écriture de clé distante interrompue.'));
    });
  } finally {
    db.close();
  }
}

async function deleteKey(id: string): Promise<void> {
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error('Suppression de clé distante impossible.'));
      tx.onabort = () => reject(tx.error || new Error('Suppression de clé distante interrompue.'));
    });
  } finally {
    db.close();
  }
}

const signingKeyId = (kid: string) => `remote-signing-private:${kid}`;
const encryptionKeyId = (kid: string) => `remote-encryption-private:${kid}`;

function publicJwk(jwk: JsonWebKey, kid: string, use: 'sig' | 'enc'): JsonWebKey {
  if (jwk.kty !== 'EC' || jwk.crv !== 'P-256' || !jwk.x || !jwk.y || jwk.d) {
    throw new Error('Clé publique distante invalide.');
  }
  return {
    kty: 'EC',
    crv: 'P-256',
    x: jwk.x,
    y: jwk.y,
    kid,
    use,
  };
}

function exactKeys(value: Record<string, unknown>, expected: string[]): boolean {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((item, index) => item === wanted[index]);
}

function assertJweHeader(header: Record<string, unknown>, expectedKid: string): void {
  if (!exactKeys(header, ['alg', 'enc', 'kid', 'typ', 'cty', 'epk'])) {
    throw new Error('En-tête JWE distant inattendu.');
  }
  if (
    header.alg !== JWE_ALG
    || header.enc !== JWE_ENC
    || header.kid !== expectedKid
    || header.typ !== JWE_TYP
    || header.cty !== JWE_CTY
  ) {
    throw new Error('Algorithme ou destinataire JWE inattendu.');
  }
  const epk = header.epk;
  if (
    typeof epk !== 'object'
    || epk === null
    || !exactKeys(epk as Record<string, unknown>, ['kty', 'crv', 'x', 'y'])
    || (epk as Record<string, unknown>).kty !== 'EC'
    || (epk as Record<string, unknown>).crv !== 'P-256'
  ) {
    throw new Error('Clé éphémère JWE invalide.');
  }
}

function assertJwsHeader(header: Record<string, unknown>, expectedKid: string): void {
  if (!exactKeys(header, ['alg', 'kid', 'typ'])) {
    throw new Error('En-tête JWS distant inattendu.');
  }
  if (header.alg !== JWS_ALG || header.kid !== expectedKid || header.typ !== JWS_TYP) {
    throw new Error('Signature distante inattendue.');
  }
}

export async function prepareRemoteEnrollment(): Promise<PreparedRemoteEnrollment | null> {
  if (
    typeof indexedDB === 'undefined'
    || typeof crypto === 'undefined'
    || !crypto.subtle
    || typeof crypto.randomUUID !== 'function'
  ) {
    return null;
  }

  const signingKid = crypto.randomUUID();
  const encryptionKid = crypto.randomUUID();
  const signing = await crypto.subtle.generateKey(
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['sign', 'verify'],
  ) as CryptoKeyPair;
  const encryption = await crypto.subtle.generateKey(
    { name: 'ECDH', namedCurve: 'P-256' },
    false,
    ['deriveBits', 'deriveKey'],
  ) as CryptoKeyPair;

  if (signing.privateKey.extractable || encryption.privateKey.extractable) {
    throw new Error('Les clés privées Patient Companion doivent être non exportables.');
  }

  const signingPublic = publicJwk(
    await crypto.subtle.exportKey('jwk', signing.publicKey),
    signingKid,
    'sig',
  );
  const encryptionPublic = publicJwk(
    await crypto.subtle.exportKey('jwk', encryption.publicKey),
    encryptionKid,
    'enc',
  );

  await writeKey(signingKeyId(signingKid), signing.privateKey);
  try {
    await writeKey(encryptionKeyId(encryptionKid), encryption.privateKey);
  } catch (error) {
    await deleteKey(signingKeyId(signingKid)).catch(() => undefined);
    throw error;
  }

  return {
    signingKid,
    encryptionKid,
    request: {
      signing_kid: signingKid,
      signing_public_jwk: signingPublic,
      encryption_kid: encryptionKid,
      encryption_public_jwk: encryptionPublic,
    },
  };
}

export async function discardRemoteEnrollment(prepared: PreparedRemoteEnrollment): Promise<void> {
  await Promise.all([
    deleteKey(signingKeyId(prepared.signingKid)).catch(() => undefined),
    deleteKey(encryptionKeyId(prepared.encryptionKid)).catch(() => undefined),
  ]);
}

export async function signAndEncryptRemote(
  payload: Record<string, unknown>,
  binding: PatientRemoteTransportBinding,
): Promise<string> {
  const signingPrivate = await readKey(signingKeyId(binding.signingKid));
  if (!signingPrivate) throw new Error('Clé de signature Patient Companion introuvable.');

  const cabinetEncryption = await importJWK(
    binding.cabinetEncryptionPublicJwk,
    JWE_ALG,
  );

  const compactJws = await new CompactSign(encoder.encode(JSON.stringify(payload)))
    .setProtectedHeader({
      alg: JWS_ALG,
      kid: binding.signingKid,
      typ: JWS_TYP,
    })
    .sign(signingPrivate);

  return new CompactEncrypt(encoder.encode(compactJws))
    .setProtectedHeader({
      alg: JWE_ALG,
      enc: JWE_ENC,
      kid: binding.cabinetEncryptionKid,
      typ: JWE_TYP,
      cty: JWE_CTY,
    })
    .encrypt(cabinetEncryption);
}

export async function decryptAndVerifyRemote(
  compactJwe: string,
  binding: PatientRemoteTransportBinding,
): Promise<Record<string, unknown>> {
  const encryptionPrivate = await readKey(encryptionKeyId(binding.encryptionKid));
  if (!encryptionPrivate) throw new Error('Clé de déchiffrement Patient Companion introuvable.');

  const decrypted = await compactDecrypt(compactJwe, encryptionPrivate, {
    keyManagementAlgorithms: [JWE_ALG],
    contentEncryptionAlgorithms: [JWE_ENC],
  });
  assertJweHeader(
    decrypted.protectedHeader as Record<string, unknown>,
    binding.encryptionKid,
  );

  const compactJws = decoder.decode(decrypted.plaintext);
  const cabinetSigning = await importJWK(binding.cabinetSigningPublicJwk, JWS_ALG);
  const verified = await compactVerify(compactJws, cabinetSigning, {
    algorithms: [JWS_ALG],
  });
  assertJwsHeader(
    verified.protectedHeader as Record<string, unknown>,
    binding.cabinetSigningKid,
  );

  const payload = JSON.parse(decoder.decode(verified.payload));
  if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
    throw new Error('Payload distant Patient Companion invalide.');
  }
  return payload as Record<string, unknown>;
}

export const PatientCompanionRemoteCrypto = {
  prepareEnrollment: prepareRemoteEnrollment,
  discardEnrollment: discardRemoteEnrollment,
  signAndEncrypt: signAndEncryptRemote,
  decryptAndVerify: decryptAndVerifyRemote,
};
