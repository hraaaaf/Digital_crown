import { describe, expect, it } from 'vitest';
import { V1_CEPHALO_PROTOCOLS, asV1CephaloProtocol,
  v1ModeForProtocol, v1ProtocolForMode } from './cephaloV1ProtocolScope';

describe('Céphalo V1 L1-a protocol scope', () => {
  it('lists COM Digital Crown and Steiner 1953 only', () => {
    expect(V1_CEPHALO_PROTOCOLS.map(p => p.id)).toEqual(['COM', 'STEINER']);
    expect(V1_CEPHALO_PROTOCOLS.map(p => p.label))
      .toEqual(['COM Digital Crown', 'Steiner 1953']);
  });
  it('maps selection both ways without McNamara or Ricketts aliases', () => {
    expect(v1ModeForProtocol('COM')).toBe('com');
    expect(v1ModeForProtocol('STEINER')).toBe('steiner');
    expect(v1ProtocolForMode('com')).toBe('COM');
    expect(v1ProtocolForMode('steiner')).toBe('STEINER');
    for (const legacy of ['all', 'tweed', 'mcnamara', 'ricketts']) {
      expect(v1ProtocolForMode(legacy)).toBeNull();
    }
  });
  it('refuses an out-of-scope historic study instead of relabelling it COM', () => {
    for (const legacy of ['ALL', 'MCNAMARA', 'WITS', 'TWEED', '', 'com']) {
      expect(asV1CephaloProtocol(legacy)).toBeNull();
      expect(v1ModeForProtocol(legacy)).toBeNull();
    }
    expect(asV1CephaloProtocol('COM')).toBe('COM');
  });
});
