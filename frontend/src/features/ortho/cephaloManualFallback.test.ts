import { describe, it, expect } from 'vitest';
import { REQUIRED_LANDMARKS } from './cephaloShared';

// The manual fallback must expose only the 38 actual SRPose landmarks.
// Occ_Ant and Occ_Post are constructed planes, not model predictions.
const manualPointIds: readonly string[] = REQUIRED_LANDMARKS.filter(
  id => id !== 'Occ_Ant' && id !== 'Occ_Post',
);

describe('LOT05 SRPose38 manual fallback contract', () => {
  it('offers exactly 38 unique manually placed anatomical points', () => {
    expect(manualPointIds).toHaveLength(38);
    expect(new Set(manualPointIds).size).toBe(38);
  });

  it('requires dental apices and cranial anchors but not synthesized planes', () => {
    expect(manualPointIds).toContain('U1_apex');
    expect(manualPointIds).toContain('L1_apex');
    expect(manualPointIds).toContain('S');
    expect(manualPointIds).toContain('N');
    expect(manualPointIds).not.toContain('Occ_Ant');
    expect(manualPointIds).not.toContain('Occ_Post');
  });
});
