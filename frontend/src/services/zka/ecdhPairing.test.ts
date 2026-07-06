import { afterEach, describe, expect, it } from 'vitest';
import { createCipheriv, createECDH, hkdfSync, randomBytes } from 'node:crypto';

import {
  deriveMasterKey,
  generateClientKeyPair,
  hasPlaintextMasterKey,
  PAIRING_CRYPTO_UNAVAILABLE_MESSAGE,
} from './ecdhPairing';

const INFO = Buffer.from('zka_mobile_bridge', 'utf8');
const SALT = Buffer.alloc(32, 0);

function buildEncryptedBlob(sharedSecret: Buffer, masterKey: string): string {
  const aesKey = Buffer.from(hkdfSync('sha256', sharedSecret, SALT, INFO, 32));
  const nonce = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', aesKey, nonce);
  const ciphertext = Buffer.concat([cipher.update(masterKey, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([nonce, ciphertext, tag]).toString('hex');
}

function setCryptoSubtle(value: SubtleCrypto | undefined) {
  Object.defineProperty(globalThis.crypto, 'subtle', {
    configurable: true,
    value,
  });
}

const originalSubtle = globalThis.crypto.subtle;

afterEach(() => {
  setCryptoSubtle(originalSubtle);
});

describe('ecdhPairing', () => {
  it('generateClientKeyPair does not require crypto.subtle', async () => {
    setCryptoSubtle(undefined);

    const keyPair = await generateClientKeyPair();

    expect(keyPair.privateKey).toBeInstanceOf(Uint8Array);
    expect(keyPair.privateKey).toHaveLength(32);
    expect(keyPair.publicKeyHex).toMatch(/^04[0-9a-f]{128}$/i);
  });

  it('deriveMasterKey does not require crypto.subtle', async () => {
    const keyPair = await generateClientKeyPair();
    const server = createECDH('prime256v1');
    const serverPublicKeyHex = server.generateKeys('hex', 'uncompressed');
    const sharedSecret = server.computeSecret(Buffer.from(keyPair.publicKeyHex, 'hex'));
    const masterKey = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
    const encryptedMasterKeyHex = buildEncryptedBlob(sharedSecret, masterKey);

    setCryptoSubtle(undefined);

    await expect(
      deriveMasterKey(keyPair.privateKey, serverPublicKeyHex, encryptedMasterKeyHex),
    ).resolves.toBe(masterKey);
  });

  it('supports the full pairing flow when crypto.subtle is undefined', async () => {
    setCryptoSubtle(undefined);

    const client = await generateClientKeyPair();
    const server = createECDH('prime256v1');
    const serverPublicKeyHex = server.generateKeys('hex', 'uncompressed');
    const sharedSecret = server.computeSecret(Buffer.from(client.publicKeyHex, 'hex'));
    const masterKey = 'abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789';
    const encryptedMasterKeyHex = buildEncryptedBlob(sharedSecret, masterKey);

    const derived = await deriveMasterKey(
      client.privateKey,
      serverPublicKeyHex,
      encryptedMasterKeyHex,
    );

    expect(derived).toBe(masterKey);
  });

  it('returns a clean error when the crypto payload is unusable', async () => {
    setCryptoSubtle(undefined);

    await expect(
      deriveMasterKey(new Uint8Array(32), 'deadbeef', 'beef'),
    ).rejects.toThrow(PAIRING_CRYPTO_UNAVAILABLE_MESSAGE);
  });

  it('does not accept plaintext masterKey response shapes and keeps legacy mode disabled', () => {
    expect(hasPlaintextMasterKey({ masterKey: 'plaintext' })).toBe(true);
    expect(hasPlaintextMasterKey({ master_key: 'plaintext' })).toBe(true);
    expect(
      hasPlaintextMasterKey({
        server_public_key_hex: '04',
        encrypted_master_key_hex: '00',
      }),
    ).toBe(false);
  });
});
