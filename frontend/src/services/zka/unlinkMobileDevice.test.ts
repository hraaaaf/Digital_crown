import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const storage = vi.hoisted(() => ({
  getCredentials: vi.fn(),
  clearAll: vi.fn(),
  resolveMobileApiBaseUrl: vi.fn((base: string) => base),
}));
vi.mock('./MobileStorage', () => ({ MobileStorage: storage, resolveMobileApiBaseUrl: storage.resolveMobileApiBaseUrl }));
import { unlinkCurrentMobileDevice } from './unlinkMobileDevice';
import { hasUnconfirmedMobileRevocation, acknowledgeMobileRevocationFollowUp } from './mobileRevocationFollowUp';

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  storage.getCredentials.mockResolvedValue({
    publicId: '0123456789abcdef',
    access_token: 'disposable-token',
    device_id: 'disposable-device',
    api_base_url: 'http://127.0.0.1:8005',
  });
  storage.clearAll.mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { onLine: true });
  vi.stubGlobal('window', { location: { hostname: '127.0.0.1', protocol: 'http:' } });
});
afterEach(() => { vi.unstubAllGlobals(); });

describe('explicit single-device unlink', () => {
  it('revokes only the current mobile token and then purges local state', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    vi.stubGlobal('fetch', fetchMock);
    expect(await unlinkCurrentMobileDevice()).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:8005/api/mobile/revoke-device');
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer disposable-token');
    expect(storage.clearAll).toHaveBeenCalledOnce();
  });

  it('always purges locally even if on-premise API rejects the revoke', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    expect(await unlinkCurrentMobileDevice()).toBe(false);
    expect(storage.clearAll).toHaveBeenCalledOnce();
  });

  it('never claims remote revoke while offline; still wipes locally', async () => {
    vi.stubGlobal('navigator', { onLine: false });
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    expect(await unlinkCurrentMobileDevice()).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(storage.clearAll).toHaveBeenCalledOnce();
  });

  it('wipes local patient state even if credentials cannot be read', async () => {
    storage.getCredentials.mockRejectedValue(new Error('IndexedDB unavailable'));
    vi.stubGlobal('fetch', vi.fn());
    expect(await unlinkCurrentMobileDevice()).toBe(false);
    expect(storage.clearAll).toHaveBeenCalledOnce();
  });
  it('persists an offline remote-revocation warning without storing clinical identifiers', async () => {
    vi.stubGlobal('navigator', { onLine: false });
    vi.stubGlobal('fetch', vi.fn());
    expect(await unlinkCurrentMobileDevice()).toBe(false);
    expect(hasUnconfirmedMobileRevocation()).toBe(true);
    expect(localStorage.length).toBe(1);
    expect(localStorage.key(0)).toBe('dc_mobile_remote_revocation_unconfirmed_v1');
    expect(localStorage.getItem('dc_mobile_remote_revocation_unconfirmed_v1')).toBe('1');
  });

  it('does not erase an older pending revoke after success revoking another pairing', async () => {
    vi.stubGlobal('navigator', { onLine: false });
    vi.stubGlobal('fetch', vi.fn());
    expect(await unlinkCurrentMobileDevice()).toBe(false);
    vi.stubGlobal('navigator', { onLine: true });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200 }));
    expect(await unlinkCurrentMobileDevice()).toBe(true);
    expect(hasUnconfirmedMobileRevocation()).toBe(true);
    acknowledgeMobileRevocationFollowUp();
    expect(hasUnconfirmedMobileRevocation()).toBe(false);
  });

  it('does not invent a pending reminder for a confirmed first-time revoke', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200 }));
    expect(await unlinkCurrentMobileDevice()).toBe(true);
    expect(hasUnconfirmedMobileRevocation()).toBe(false);
  });

});
