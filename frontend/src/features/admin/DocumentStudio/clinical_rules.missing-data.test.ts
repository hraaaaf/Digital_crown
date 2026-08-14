import { describe, expect, it } from 'vitest';
import {
  estimateWeightFromAge,
  getAgeAwareDosing,
  getPediatricGuide,
} from './clinical_rules';

describe('missing-data guards', () => {
  it('does not synthesize weight from age', () => {
    expect(estimateWeightFromAge(8)).toBe(0);
  });

  it('does not compute a weight-dependent pediatric regimen without explicit weight', () => {
    expect(getAgeAwareDosing('CLARITHROMYCINE', 8, undefined)).toBeNull();
  });

  it('does not compute age-aware output without explicit age', () => {
    expect(getAgeAwareDosing('PARACETAMOL', undefined, 20)).toBeNull();
  });

  it('keeps the deprecated weight-only pediatric helper fail-closed', () => {
    expect(getPediatricGuide('AMOXICILLINE', 20)).toBeNull();
  });
});
