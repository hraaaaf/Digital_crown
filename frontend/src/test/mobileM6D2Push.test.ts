import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { evaluatePushCapability, urlBase64ToUint8Array } from '../services/zka/mobilePush';

describe('M6-D2 Web Push capability gates', () => {
  it('fails closed on insecure LAN origins', () => {
    const state = evaluatePushCapability({
      secure: false,
      ios: false,
      standalone: false,
      notificationApi: true,
      serviceWorker: true,
      pushManager: true,
      permission: 'default',
    });
    expect(state.kind).toBe('secure-required');
  });

  it('requires Home Screen installation on iOS before prompting', () => {
    const state = evaluatePushCapability({
      secure: true,
      ios: true,
      standalone: false,
      notificationApi: true,
      serviceWorker: true,
      pushManager: true,
      permission: 'default',
    });
    expect(state.kind).toBe('install-required');
  });

  it('only exposes an activation prompt when the platform prerequisites pass', () => {
    const state = evaluatePushCapability({
      secure: true,
      ios: false,
      standalone: false,
      notificationApi: true,
      serviceWorker: true,
      pushManager: true,
      permission: 'default',
    });
    expect(state.kind).toBe('prompt');
  });

  it('decodes the unpadded VAPID application server key', () => {
    expect(Array.from(urlBase64ToUint8Array('AQIDBA'))).toEqual([1, 2, 3, 4]);
  });
});

describe('M6-D2 service worker privacy boundary', () => {
  it('renders fixed generic OS copy instead of server-supplied title/body', () => {
    const source = readFileSync(resolve(process.cwd(), 'public/push-sw.js'), 'utf8');
    expect(source).toContain("const title = 'Digital Crown'");
    expect(source).toContain("const body = 'De nouvelles alertes sont disponibles");
    expect(source).not.toContain('payload.title');
    expect(source).not.toContain('payload.body');
    expect(source).toContain("const url = '/mobile/dashboard'");
  });
});
