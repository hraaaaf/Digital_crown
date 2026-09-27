import { beforeEach, describe, expect, it, vi } from 'vitest';

const store = vi.hoisted(() => new Map<string, unknown>());

vi.mock('localforage', () => ({
  default: {
    config: vi.fn(),
    getItem: vi.fn(async (key: string) => store.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: unknown) => {
      store.set(key, value);
      return value;
    }),
    removeItem: vi.fn(async (key: string) => {
      store.delete(key);
    }),
  },
}));

import { MobileStorage, type ZKACredentials } from './MobileStorage';

const credentials = (overrides: Partial<ZKACredentials> = {}): ZKACredentials => ({
  publicId: '0123456789abcdef',
  masterKey: 'a'.repeat(64),
  access_token: 'mobile-access-token',
  refresh_token: 'mobile-refresh-token',
  device_id: 'device-a',
  api_base_url: 'http://localhost:8005',
  ...overrides,
});

beforeEach(() => {
  store.clear();
  localStorage.clear();
});

describe('MobileStorage snapshot scope', () => {
  it('returns a cached snapshot only for the exact selected date', async () => {
    await MobileStorage.saveCredentials(credentials());
    await MobileStorage.saveLastSnapshot({ marker: 'sept-27' }, '2026-09-27');

    expect((await MobileStorage.getLastSnapshot('2026-09-27'))?.data).toEqual({ marker: 'sept-27' });
    expect(await MobileStorage.getLastSnapshot('2026-09-28')).toBeNull();
    expect(await MobileStorage.getLastSnapshot('2026-09-26')).toBeNull();
  });

  it('invalidates cached snapshots when the paired device scope changes', async () => {
    await MobileStorage.saveCredentials(credentials());
    await MobileStorage.saveLastSnapshot({ marker: 'device-a' }, '2026-09-27');

    await MobileStorage.saveCredentials(credentials({ device_id: 'device-b' }));

    expect(await MobileStorage.getLastSnapshot('2026-09-27')).toBeNull();
  });

  it('invalidates cached snapshots when the cabinet scope changes', async () => {
    await MobileStorage.saveCredentials(credentials());
    await MobileStorage.saveLastSnapshot({ marker: 'cabinet-a' }, '2026-09-27');

    await MobileStorage.saveCredentials(credentials({ publicId: 'fedcba9876543210' }));

    expect(await MobileStorage.getLastSnapshot('2026-09-27')).toBeNull();
  });
});
