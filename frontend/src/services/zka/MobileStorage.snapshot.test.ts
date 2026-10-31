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
  it('purges A offline snapshot and queued actions when API origin changes despite same tenant/device IDs', async () => {
    const a = credentials({ api_base_url: 'http://127.0.0.1:8005' });
    const b = credentials({ api_base_url: 'http://127.0.0.1:8105' });
    const day = '2026-09-27';

    await MobileStorage.saveCredentials(a);
    await MobileStorage.saveLastSnapshot({ marker: 'synthetic-A' }, day);
    await MobileStorage.enqueueAction(
      'http://127.0.0.1:8005/api/mobile/appointments/7/status',
      'PATCH',
      { status: 'EN_ATTENTE' },
      'synthetic-A-action',
    );
    expect((await MobileStorage.getLastSnapshot(day))?.data).toEqual({ marker: 'synthetic-A' });
    expect(await MobileStorage.getActionQueue()).toHaveLength(1);

    // A→B: same opaque cabinet/device IDs on another API origin must not leak A state.
    await MobileStorage.saveCredentials(b);
    expect(await MobileStorage.getLastSnapshot(day)).toBeNull();
    expect(await MobileStorage.getActionQueue()).toEqual([]);
    expect(store.has('zka_action_queue_v2')).toBe(false);

    await MobileStorage.saveLastSnapshot({ marker: 'synthetic-B' }, day);
    expect((await MobileStorage.getLastSnapshot(day))?.data).toEqual({ marker: 'synthetic-B' });

    // B→A: returning to A must also remove B's offline snapshot.
    await MobileStorage.saveCredentials(a);
    expect(await MobileStorage.getLastSnapshot(day)).toBeNull();
    expect(await MobileStorage.getActionQueue()).toEqual([]);
  });

});
