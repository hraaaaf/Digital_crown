import { describe, expect, it } from 'vitest';

import { requiresDevisToHonorairesConfirmation } from './AccountingDocumentTransitionPolicy';

describe('P3-E accounting document transition', () => {
  it('requires explicit confirmation only for Devis to Honoraires conversion', () => {
    expect(requiresDevisToHonorairesConfirmation('devis', 'honoraires')).toBe(true);
    expect(requiresDevisToHonorairesConfirmation('honoraires', 'devis')).toBe(false);
    expect(requiresDevisToHonorairesConfirmation('devis', 'ordonnance')).toBe(false);
    expect(requiresDevisToHonorairesConfirmation('honoraires', 'echeancier')).toBe(false);
  });
});
