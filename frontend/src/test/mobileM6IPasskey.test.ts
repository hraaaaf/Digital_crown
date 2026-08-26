import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { base64UrlToArrayBuffer } from '../services/zka/mobilePasskey';

function source(path: string): string {
  return readFileSync(resolve(process.cwd(), path), 'utf8');
}

describe('M6-I passkey / biometric hardening', () => {
  it('decodes base64url WebAuthn ids losslessly', () => {
    const result = new Uint8Array(base64UrlToArrayBuffer('AQIDBA'));
    expect([...result]).toEqual([1, 2, 3, 4]);
  });

  it('keeps the biometric UV token memory-only and seals sensitive local data', () => {
    const storage = source('src/services/zka/MobileStorage.ts');
    expect(storage).toContain("let biometricAccessToken: string | null = null");
    expect(storage).not.toContain("localStorage.setItem('biometric");
    expect(storage).not.toContain('sessionStorage.setItem');
    expect(storage).toContain("{ name: 'AES-GCM' }");
    expect(storage).toContain("masterKey: ''");
    expect(storage).toContain('removeItem(STORE_SNAPSHOT_ID)');
    expect(storage).toContain('removeItem(STORE_BRIDGE_CONTEXT_ID)');
    expect(storage).toContain('removeItem(STORE_ACTION_QUEUE_ID)');
  });

  it('forces the stable local hostname instead of a stale DHCP API address', () => {
    const storage = source('src/services/zka/MobileStorage.ts');
    expect(storage).toContain("hostname === 'digitalcrown.local'");
    expect(storage).toContain("return `${window.location.protocol}//${hostname}:8005`");
  });

  it('fails closed on server biometric lock responses', () => {
    const fetchSource = source('src/services/zka/mobileFetch.ts');
    expect(fetchSource).toContain('response.status === 423');
    expect(fetchSource).toContain('lockBiometricVault');
    expect(fetchSource).toContain('digitalcrown:mobile-biometric-locked');
  });

  it('recovers an orphaned local vault after server-side disable', () => {
    const client = source('src/services/zka/mobilePasskey.ts');
    const gate = source('src/features/mobile/Security/MobileBiometricGate.tsx');
    expect(client).toContain("if (status.state === 'disabled')");
    expect(client).toContain('authenticateLocalVault(vault.credential_id, vault.prf_salt)');
    expect(client).toContain('disableBiometricVault');
    expect(gate).toContain('Finalisez la désactivation biométrique');
  });

  it('requires PRF, user verification and never replaces an enabled passkey directly', () => {
    const client = source('src/services/zka/mobilePasskey.ts');
    const server = source('../backend/routers/mobile_passkey.py');
    expect(client).toContain("prf?: { enabled?: boolean }");
    expect(client).toContain("userVerification: 'required'");
    expect(client).toContain('sealBiometricVault');
    expect(server).toContain('PASSKEY_REPLACEMENT_REQUIRES_DISABLE');
    expect(server).toContain('require_user_verification=True');
  });
});