import { beforeEach, describe, expect, it, vi } from 'vitest';
import { isExplicitMobileBiometricLock } from './mobileBiometricLock';
import { mobileFetch } from './mobileFetch';
import { MobileStorage } from './MobileStorage';

vi.mock('./MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(),
    getBiometricAccessToken: vi.fn(),
    lockBiometricVault: vi.fn(),
    clearBiometricAccessToken: vi.fn(),
    refreshCredentials: vi.fn(),
  },
}));

function refusal(detail: unknown, status = 423): Response {
  return {
    status,
    clone: () => ({ json: async () => ({ detail }) }),
  } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(MobileStorage.getCredentials).mockResolvedValue({
    publicId: 'a'.repeat(16),
    masterKey: 'b'.repeat(64),
    access_token: 'paired-access',
    refresh_token: 'refresh',
    device_id: 'device',
    api_base_url: 'https://synthetic.example',
  });
  vi.mocked(MobileStorage.getBiometricAccessToken).mockReturnValue(null);
});

describe('Pocket typed biometric refusal', () => {
  it('accepts only canonical server biometric step-up among 423 responses', () => {
    expect(isExplicitMobileBiometricLock(423, { detail: { code: 'MOBILE_BIOMETRIC_LOCKED' } })).toBe(true);
    expect(isExplicitMobileBiometricLock(423, { detail: 'WORKSTATION_ENROLLMENT_REQUIRED' })).toBe(false);
    expect(isExplicitMobileBiometricLock(423, { detail: { code: 'CABINET_LOCKED' } })).toBe(false);
    expect(isExplicitMobileBiometricLock(423, null)).toBe(false);
    expect(isExplicitMobileBiometricLock(401, { detail: { code: 'MOBILE_BIOMETRIC_LOCKED' } })).toBe(false);
  });

  it('keeps an unrelated 423 refused without displaying a misleading Face ID lock', async () => {
    const response = refusal({ code: 'WORKSTATION_ENROLLMENT_REQUIRED' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
    const listener = vi.fn();
    window.addEventListener('digitalcrown:mobile-biometric-locked', listener);
    try {
      expect(await mobileFetch('/api/mobile/snapshot')).toBe(response);
      expect(MobileStorage.lockBiometricVault).not.toHaveBeenCalled();
      expect(listener).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener('digitalcrown:mobile-biometric-locked', listener);
      vi.unstubAllGlobals();
    }
  });

  it('still locks immediately when server explicitly requires WebAuthn UV', async () => {
    const response = refusal({ code: 'MOBILE_BIOMETRIC_LOCKED' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
    const listener = vi.fn();
    window.addEventListener('digitalcrown:mobile-biometric-locked', listener);
    try {
      expect(await mobileFetch('/api/mobile/snapshot')).toBe(response);
      expect(MobileStorage.lockBiometricVault).toHaveBeenCalledOnce();
      expect(listener).toHaveBeenCalledOnce();
    } finally {
      window.removeEventListener('digitalcrown:mobile-biometric-locked', listener);
      vi.unstubAllGlobals();
    }
  });

  it('never consumes the original 423 response body when inspecting its clone', async () => {
    const json = vi.fn().mockResolvedValue({ detail: { code: 'CABINET_LOCKED' } });
    const response = { status: 423, clone: () => ({ json: async () => ({ detail: { code: 'CABINET_LOCKED' } }) }), json } as unknown as Response;
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
    try {
      expect(await mobileFetch('/api/mobile/snapshot')).toBe(response);
      expect(json).not.toHaveBeenCalled();
      expect(MobileStorage.lockBiometricVault).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
