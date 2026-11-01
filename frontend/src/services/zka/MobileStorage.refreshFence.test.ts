import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const entries = vi.hoisted(() => new Map<string, unknown>());
vi.mock('localforage', () => ({
  default: {
    config: vi.fn(),
    getItem: vi.fn(async (key: string) => entries.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: unknown) => { entries.set(key, value); return value; }),
    removeItem: vi.fn(async (key: string) => { entries.delete(key); }),
  },
}));

import {
  MobileStorage, resolveMobileApiBaseUrl, resolveMobileOnboardingApiBaseUrl,
  type ZKACredentials,
} from './MobileStorage';

const credentials = (refresh_token: string, overrides: Partial<ZKACredentials> = {}): ZKACredentials => ({
  publicId: '0123456789abcdef',
  masterKey: 'a'.repeat(64),
  access_token: 'initial-access-' + refresh_token,
  refresh_token,
  device_id: 'the-same-disposable-device',
  api_base_url: 'http://127.0.0.1:8005',
  ...overrides,
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(r => { resolve = r; });
  return { promise, resolve };
}

beforeEach(() => {
  entries.clear();
  localStorage.clear();
  vi.restoreAllMocks();
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('mobile API origin — no per-component hard-coded cabinet address', () => {
  it('preserves a non-loopback explicitly configured clinic origin and port', () => {
    vi.stubGlobal('window', { location: { hostname: 'digitalcrown.local', protocol: 'https:' } });
    expect(resolveMobileApiBaseUrl('https://cabinet.example:9344/')).toBe('https://cabinet.example:9344');
    expect(resolveMobileOnboardingApiBaseUrl('https://cabinet.example:9344/')).toBe('https://cabinet.example:9344');
  });

  it('maps only true loopback to current cabinet hostname, not deceptive substrings', () => {
    vi.stubGlobal('window', { location: { hostname: 'cabinet.lan', protocol: 'https:' } });
    expect(resolveMobileApiBaseUrl('https://notlocalhost.example:9443')).toBe('https://notlocalhost.example:9443');
    expect(resolveMobileApiBaseUrl('http://localhost:8005/')).toBe('https://cabinet.lan:8005');
    expect(resolveMobileApiBaseUrl('http://127.0.0.1:8005')).toBe('https://cabinet.lan:8005');
  });

  it('retains standard on-premise onboarding origin when no override is provided', () => {
    vi.stubGlobal('window', { location: { hostname: 'localhost', protocol: 'http:' } });
    expect(resolveMobileOnboardingApiBaseUrl('')).toBe('http://127.0.0.1:8005');
  });
});

describe('refresh responses cannot resurrect an unlinked or replaced session', () => {
  it('a late 401 from A cannot wipe new pairing B on the very same device', async () => {
    const response = deferred<Response>();
    const fetchMock = vi.fn().mockImplementation(() => response.promise);
    vi.stubGlobal('fetch', fetchMock);
    await MobileStorage.saveCredentials(credentials('A-token'));
    const pendingA = MobileStorage.refreshCredentials();
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    await MobileStorage.clearAll();
    await MobileStorage.saveCredentials(credentials('B-token'));
    response.resolve({ ok: false, status: 401 } as Response);
    expect(await pendingA).toBeNull();
    const active = await MobileStorage.getCredentials();
    expect(active?.refresh_token).toBe('B-token');
    expect(active?.access_token).toBe('initial-access-B-token');
  });

  it('a late successful A refresh cannot overwrite tokens of newly paired B', async () => {
    const response = deferred<Response>();
    vi.stubGlobal('fetch', vi.fn(() => response.promise));
    await MobileStorage.saveCredentials(credentials('A-token'));
    const pendingA = MobileStorage.refreshCredentials();
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    await MobileStorage.clearAll();
    await MobileStorage.saveCredentials(credentials('B-token'));
    response.resolve({ ok: true, status: 200, json: async () => ({
      access_token: 'stale-A-access', refresh_token: 'stale-A-refresh',
      device_id: 'the-same-disposable-device',
    }) } as Response);
    expect(await pendingA).toBeNull();
    expect((await MobileStorage.getCredentials())?.refresh_token).toBe('B-token');
    expect((await MobileStorage.getCredentials())?.access_token).toBe('initial-access-B-token');
  });

  it('new refresh B starts independently while previous A request is unresolved', async () => {
    const oldReply = deferred<Response>();
    const newReply = deferred<Response>();
    const fetchMock = vi.fn()
      .mockImplementationOnce(() => oldReply.promise)
      .mockImplementationOnce(() => newReply.promise);
    vi.stubGlobal('fetch', fetchMock);
    await MobileStorage.saveCredentials(credentials('A-token'));
    const pendingA = MobileStorage.refreshCredentials();
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await MobileStorage.clearAll();
    await MobileStorage.saveCredentials(credentials('B-token'));
    const pendingB = MobileStorage.refreshCredentials();
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    oldReply.resolve({ ok: false, status: 401 } as Response);
    expect(await pendingA).toBeNull();
    newReply.resolve({ ok: true, status: 200, json: async () => ({
      access_token: 'B-rotated-access', refresh_token: 'B-rotated-refresh',
      device_id: 'the-same-disposable-device',
    }) } as Response);
    expect((await pendingB)?.refresh_token).toBe('B-rotated-refresh');
    expect((await MobileStorage.getCredentials())?.access_token).toBe('B-rotated-access');
  });

  it('unavailable server response after unlink never returns stale credentials to caller', async () => {
    const response = deferred<Response>();
    vi.stubGlobal('fetch', vi.fn(() => response.promise));
    await MobileStorage.saveCredentials(credentials('A-token'));
    const pending = MobileStorage.refreshCredentials();
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledOnce());
    await MobileStorage.clearAll();
    response.resolve({ ok: false, status: 503 } as Response);
    expect(await pending).toBeNull();
    expect(await MobileStorage.getCredentials()).toBeNull();
  });
});
