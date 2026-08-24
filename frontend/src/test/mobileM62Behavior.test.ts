import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const memory = vi.hoisted(() => ({ store: new Map<string, unknown>() }));
const FUTURE_EXP = 4102444800; // 2100-01-01 UTC, deterministic and safely in the future.

vi.mock('localforage', () => ({
  default: {
    config: vi.fn(),
    getItem: vi.fn(async (key: string) => memory.store.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: unknown) => {
      memory.store.set(key, value);
      return value;
    }),
    removeItem: vi.fn(async (key: string) => {
      memory.store.delete(key);
    }),
  },
}));

import { MobileStorage } from '../services/zka/MobileStorage';
import { mobileFetch } from '../services/zka/mobileFetch';

function token(label: string): string {
  const payload = Buffer.from(JSON.stringify({ exp: FUTURE_EXP, label })).toString('base64url');
  return `header.${payload}.signature`;
}

function credentials(overrides: Record<string, string> = {}) {
  return {
    publicId: 'abcdef1234567890',
    masterKey: 'a'.repeat(64),
    access_token: token('old'),
    refresh_token: 'refresh-old',
    device_id: 'device-a',
    api_base_url: 'http://127.0.0.1:8005',
    ...overrides,
  };
}

beforeEach(async () => {
  memory.store.clear();
  vi.clearAllMocks();
  localStorage.clear();
  await MobileStorage.clearAll();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('Mobile M6.2 behavior', () => {
  it('scopes queued actions to the paired cabinet and device and drops the legacy queue', async () => {
    await MobileStorage.saveCredentials(credentials());
    await MobileStorage.enqueueAction(
      'http://127.0.0.1:8005/api/mobile/appointments/7/status',
      'PATCH',
      { status: 'arrived' },
      'action-a',
    );
    expect(await MobileStorage.getActionQueue()).toHaveLength(1);

    memory.store.set('zka_action_queue_v2', [{
      id: 'foreign',
      url: 'http://127.0.0.1:8005/api/mobile/appointments/8/status',
      method: 'PATCH',
      timestamp: Date.now(),
      cabinetPublicId: 'ffffffffffffffff',
      deviceId: 'device-other',
    }]);
    memory.store.set('zka_action_queue', [{ id: 'legacy-unscoped' }]);
    expect(await MobileStorage.getActionQueue()).toEqual([]);
    expect(memory.store.has('zka_action_queue')).toBe(false);
  });

  it('purges the queue when the paired device changes', async () => {
    await MobileStorage.saveCredentials(credentials());
    await MobileStorage.enqueueAction(
      'http://127.0.0.1:8005/api/mobile/appointments/7',
      'DELETE',
      undefined,
      'action-delete',
    );
    expect(await MobileStorage.getActionQueue()).toHaveLength(1);

    await MobileStorage.saveCredentials(credentials({ device_id: 'device-b' }));
    expect(await MobileStorage.getActionQueue()).toEqual([]);
  });

  it('rotates the mobile refresh token and retries one 401 with the new access token', async () => {
    await MobileStorage.saveCredentials(credentials());
    const newAccess = token('new');
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({
          access_token: newAccess,
          refresh_token: 'refresh-new',
          device_id: 'device-a',
        }),
      })
      .mockResolvedValueOnce({ status: 200, ok: true });
    vi.stubGlobal('fetch', fetchMock);

    const response = await mobileFetch('http://127.0.0.1:8005/api/mobile/dentists');
    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toBe('http://127.0.0.1:8005/api/mobile/refresh-token');

    const firstHeaders = new Headers(fetchMock.mock.calls[0][1]?.headers);
    const retryHeaders = new Headers(fetchMock.mock.calls[2][1]?.headers);
    expect(firstHeaders.get('Authorization')).toBe(`Bearer ${token('old')}`);
    expect(retryHeaders.get('Authorization')).toBe(`Bearer ${newAccess}`);

    const updated = await MobileStorage.getCredentials();
    expect(updated?.access_token).toBe(newAccess);
    expect(updated?.refresh_token).toBe('refresh-new');
  });

  it('clears the paired session when refresh is rejected as revoked', async () => {
    await MobileStorage.saveCredentials(credentials());
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValueOnce({ status: 401, ok: false });
    vi.stubGlobal('fetch', fetchMock);

    const response = await mobileFetch('http://127.0.0.1:8005/api/mobile/dentists');
    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(await MobileStorage.getCredentials()).toBeNull();
    expect(memory.store.has('zka_action_queue_v2')).toBe(false);
  });

  it('does not refresh or clear the session for a server 500 response', async () => {
    await MobileStorage.saveCredentials(credentials());
    const fetchMock = vi.fn().mockResolvedValueOnce({ status: 500, ok: false });
    vi.stubGlobal('fetch', fetchMock);

    const response = await mobileFetch('http://127.0.0.1:8005/api/mobile/dentists');
    expect(response.status).toBe(500);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect((await MobileStorage.getCredentials())?.device_id).toBe('device-a');
  });
});
