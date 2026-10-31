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

  it('must forget all clinical offline state on explicit unlink, including theme and queue', async () => {
    const current = credentials({ api_base_url: 'http://127.0.0.1:8005' });
    await MobileStorage.saveCredentials(current);
    await MobileStorage.saveLastSnapshot({ patient: 'DISPOSABLE_PHI_MARKER' }, '2026-09-27');
    await MobileStorage.enqueueAction(
      'http://127.0.0.1:8005/api/mobile/appointments/7/status',
      'PATCH', { status: 'EN_ATTENTE' }, 'action-before-unlink',
    );
    store.set('zka_bridge_context', { key: 'DISPOSABLE_CONTEXT' });
    store.set('zka_biometric_vault_v1', { fake: 'DISPOSABLE_VAULT' });
    localStorage.setItem('digitalcrown_mobile_theme:http%3A%2F%2F127.0.0.1%3A8005:a', '{"selected_theme":"rose"}');
    localStorage.setItem('digitalcrown_mobile_theme:old', 'OLD_THEME');
    localStorage.setItem('token', 'legacy');
    localStorage.setItem('unrelated-setting', 'keep');

    await MobileStorage.clearCredentials();
    for (const key of ['zka_credentials', 'zka_last_snapshot', 'zka_action_queue_v2',
      'zka_bridge_context', 'zka_biometric_vault_v1']) {
      expect(store.has(key), key).toBe(false);
    }
    expect(await MobileStorage.getLastSnapshot('2026-09-27')).toBeNull();
    expect(await MobileStorage.getActionQueue()).toEqual([]);
    expect(await MobileStorage.isPaired()).toBe(false);
    expect(localStorage.getItem('digitalcrown_mobile_theme:old')).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('unrelated-setting')).toBe('keep');
  });

});
