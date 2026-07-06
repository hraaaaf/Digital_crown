import { gcm } from '@noble/ciphers/aes.js';
import { p256 } from '@noble/curves/nist.js';
import { bytesToHex, hexToBytes } from '@noble/curves/utils.js';
import { hkdf } from '@noble/hashes/hkdf.js';
import { sha256 } from '@noble/hashes/sha2.js';

const PAIRING_INFO = new TextEncoder().encode('zka_mobile_bridge');
const HKDF_SALT = new Uint8Array(32);
const NONCE_LENGTH = 12;
const MASTER_KEY_PATTERN = /^[0-9a-fA-F]{64}$/;

export const PAIRING_CRYPTO_UNAVAILABLE_MESSAGE =
  'Appairage impossible : module cryptographique indisponible.';

export interface ClientKeyPair {
  privateKey: Uint8Array;
  publicKeyHex: string;
}

function cryptoUnavailable(): Error {
  return new Error(PAIRING_CRYPTO_UNAVAILABLE_MESSAGE);
}

function normalizeHex(hex: string): string {
  const clean = hex.trim();
  if (!clean || clean.length % 2 !== 0 || !/^[0-9a-fA-F]+$/.test(clean)) {
    throw cryptoUnavailable();
  }
  return clean.toLowerCase();
}

function decodeUtf8(bytes: Uint8Array): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    throw cryptoUnavailable();
  }
}

function safeBytesFromHex(hex: string): Uint8Array {
  try {
    return hexToBytes(normalizeHex(hex));
  } catch {
    throw cryptoUnavailable();
  }
}

function wrapCrypto<T>(fn: () => T): T {
  try {
    return fn();
  } catch (error) {
    if (error instanceof Error && error.message === PAIRING_CRYPTO_UNAVAILABLE_MESSAGE) {
      throw error;
    }
    throw cryptoUnavailable();
  }
}

export function hasPlaintextMasterKey(payload: unknown): boolean {
  if (!payload || typeof payload !== 'object') return false;
  const record = payload as Record<string, unknown>;
  return typeof record.masterKey === 'string' || typeof record.master_key === 'string';
}

export async function generateClientKeyPair(): Promise<ClientKeyPair> {
  return wrapCrypto(() => {
    const privateKey = p256.utils.randomSecretKey();
    const publicKeyHex = bytesToHex(p256.getPublicKey(privateKey, false));
    return { privateKey, publicKeyHex };
  });
}

export async function deriveMasterKey(
  privateKey: Uint8Array,
  serverPublicKeyHex: string,
  encryptedMasterKeyHex: string,
): Promise<string> {
  return wrapCrypto(() => {
    if (!(privateKey instanceof Uint8Array) || privateKey.length !== 32) {
      throw cryptoUnavailable();
    }

    const serverPublicKey = safeBytesFromHex(serverPublicKeyHex);
    const encryptedBlob = safeBytesFromHex(encryptedMasterKeyHex);
    if (serverPublicKey.length !== 65 || serverPublicKey[0] !== 0x04) {
      throw cryptoUnavailable();
    }
    if (encryptedBlob.length <= NONCE_LENGTH + 16) {
      throw cryptoUnavailable();
    }

    const sharedSecret = p256.getSharedSecret(privateKey, serverPublicKey, true).slice(1);
    const aesKey = hkdf(sha256, sharedSecret, HKDF_SALT, PAIRING_INFO, 32);

    const nonce = encryptedBlob.slice(0, NONCE_LENGTH);
    const ciphertextAndTag = encryptedBlob.slice(NONCE_LENGTH);
    const plaintext = gcm(aesKey, nonce).decrypt(ciphertextAndTag);
    const masterKey = decodeUtf8(plaintext);
    if (!MASTER_KEY_PATTERN.test(masterKey)) {
      throw cryptoUnavailable();
    }
    return masterKey;
  });
}
