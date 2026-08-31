import { describe, expect, it } from 'vitest';
import { getPlatformTopology } from '../services/platformTopology';

describe('platform control-plane topology', () => {
  it('accepts only a platform API on the current frontend origin', () => {
    const sameOrigin = getPlatformTopology(window.location.origin);
    expect(sameOrigin.ready).toBe(true);
    expect(sameOrigin.platformApiOrigin).toBe(window.location.origin);

    const crossOrigin = getPlatformTopology('https://other-control.example.test');
    expect(crossOrigin.ready).toBe(false);
    expect(crossOrigin.platformApiOrigin).toBe('https://other-control.example.test');
  });
});
