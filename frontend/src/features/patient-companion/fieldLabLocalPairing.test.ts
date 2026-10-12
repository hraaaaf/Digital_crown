import { describe, expect, it } from 'vitest';
import { isSyntheticFieldLabLocalPairing } from './fieldLabLocalPairing';

describe('04.5 synthetic iPhone field mode', () => {
  it('permits explicit local-only pairing on real secure ephemeral lab host', () => {
    expect(isSyntheticFieldLabLocalPairing(true, {
      protocol: 'https:', hostname: 'test-station.trycloudflare.com',
    })).toBe(true);
  });
  it('fails closed for production, HTTP, or spoofed host', () => {
    expect(isSyntheticFieldLabLocalPairing(false, {
      protocol: 'https:', hostname: 'test-station.trycloudflare.com',
    })).toBe(false);
    expect(isSyntheticFieldLabLocalPairing(true, {
      protocol: 'http:', hostname: 'test-station.trycloudflare.com',
    })).toBe(false);
    expect(isSyntheticFieldLabLocalPairing(true, {
      protocol: 'https:', hostname: 'test-station.trycloudflare.com.attacker.net',
    })).toBe(false);
    expect(isSyntheticFieldLabLocalPairing(true, {
      protocol: 'https:', hostname: 'cabinet.digitalcrown.local',
    })).toBe(false);
    expect(isSyntheticFieldLabLocalPairing(true, undefined)).toBe(false);
  });
});
