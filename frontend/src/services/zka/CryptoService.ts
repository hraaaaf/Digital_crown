/**
 * Service cryptographique ZKA — AES-256-GCM via @noble/ciphers.
 * Fonctionne en HTTP et HTTPS (pas de dépendance à window.crypto.subtle).
 */
import { gcm } from '@noble/ciphers/aes.js';
import { hexToBytes } from '@noble/ciphers/utils.js';

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function bytesToB64(bytes: Uint8Array): string {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

export const CryptoService = {
  /**
   * Déchiffre un payload chiffré par le backend.
   * Format attendu : base64(IV(12) + Ciphertext + Tag(16))
   */
  async decryptPayload(base64Payload: string, hexKey: string): Promise<any> {
    const key = hexToBytes(hexKey);
    const combined = b64ToBytes(base64Payload);
    const iv = combined.slice(0, 12);
    const ciphertextWithTag = combined.slice(12);
    const plaintext = gcm(key, iv).decrypt(ciphertextWithTag);
    return JSON.parse(new TextDecoder().decode(plaintext));
  },

  /**
   * Chiffre un payload JSON pour l'envoyer au backend.
   * Retourne base64(IV(12) + Ciphertext + Tag(16))
   */
  async encryptPayload(data: any, hexKey: string): Promise<string> {
    const key = hexToBytes(hexKey);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const plaintext = new TextEncoder().encode(JSON.stringify(data));
    const ciphertextWithTag = gcm(key, iv).encrypt(plaintext);
    const combined = new Uint8Array(12 + ciphertextWithTag.length);
    combined.set(iv, 0);
    combined.set(ciphertextWithTag, 12);
    return bytesToB64(combined);
  },
};
