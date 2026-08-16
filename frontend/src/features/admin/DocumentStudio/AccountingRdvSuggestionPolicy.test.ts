import { describe, expect, it } from 'vitest';
import { shouldSurfaceRdvSuggestion } from './AccountingRdvSuggestionPolicy';

describe('AccountingRdvSuggestionPolicy', () => {
  it('never surfaces a follow-up appointment from a Devis', () => {
    expect(shouldSurfaceRdvSuggestion('devis', false, true)).toBe(false);
  });

  it('does not surface suggestions during preview', () => {
    expect(shouldSurfaceRdvSuggestion('honoraires', true, true)).toBe(false);
  });

  it('allows a non-Devis completed flow to surface a backend suggestion', () => {
    expect(shouldSurfaceRdvSuggestion('honoraires', false, true)).toBe(true);
  });
});
