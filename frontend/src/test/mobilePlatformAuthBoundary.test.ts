import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearMobilePlatformAccessToken,
  getRuntimeAuthToken,
  setMobilePlatformAccessToken,
} from '../services/api';
import { getPlatformPrimaryAccessToken } from '../services/platformPasskey';

describe('mobile platform auth boundary', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    window.history.replaceState({}, '', '/mobile/superadmin');
  });

  it('uses the dedicated platform token for Superadmin calls', () => {
    localStorage.setItem('token', 'cabinet-access');
    setMobilePlatformAccessToken('platform-access');
    expect(getRuntimeAuthToken('/superadmin/clients')).toBe('platform-access');
  });

  it('fails closed instead of falling back to the cabinet token', () => {
    localStorage.setItem('token', 'cabinet-access');
    clearMobilePlatformAccessToken();
    expect(getRuntimeAuthToken('/superadmin/clients')).toBeNull();
  });

  it('binds the WebAuthn ceremony to the same dedicated platform session', () => {
    localStorage.setItem('token', 'cabinet-access');
    setMobilePlatformAccessToken('platform-access');
    expect(getPlatformPrimaryAccessToken()).toBe('platform-access');

    clearMobilePlatformAccessToken();
    expect(getPlatformPrimaryAccessToken()).toBeNull();
  });

  it('does not reuse the platform token outside Superadmin requests', () => {
    setMobilePlatformAccessToken('platform-access');
    localStorage.setItem('token', 'cabinet-access');
    window.history.replaceState({}, '', '/mobile/dashboard');
    expect(getRuntimeAuthToken('/mobile/snapshot')).toBe('cabinet-access');
  });
});
