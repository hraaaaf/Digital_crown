import { describe, expect, it } from 'vitest';
import {
  MOROCCAN_CLINICAL_RULES,
  estimateWeightFromAge,
  getAgeAwareDosing,
  getPediatricGuide,
} from './clinical_rules';

const firstKnownRule = Object.keys(MOROCCAN_CLINICAL_RULES)[0];

describe('missing-data guards', () => {
  it('does not synthesize weight from age', () => {
    expect(estimateWeightFromAge(8)).toBe(0);
  });

  it('does not compute age-aware output without explicit pediatric weight', () => {
    expect(getAgeAwareDosing(firstKnownRule, 8, undefined)).toBeNull();
  });

  it('does not compute age-aware output without explicit age', () => {
    expect(getAgeAwareDosing(firstKnownRule, undefined, 20)).toBeNull();
  });

  it('does not compute pediatric guide output for invalid weight', () => {
    expect(getPediatricGuide(firstKnownRule, 0)).toBeNull();
  });
});
