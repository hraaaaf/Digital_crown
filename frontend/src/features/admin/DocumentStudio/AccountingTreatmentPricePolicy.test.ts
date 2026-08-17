import { describe, expect, it } from 'vitest';

import { resolveDevisTreatmentPrice } from './AccountingTreatmentPricePolicy';

describe('P3-C Devis treatment price policy', () => {
  it('uses the explicit catalog tariff before remembered prices', () => {
    expect(resolveDevisTreatmentPrice({
      isCatalogAct: true,
      catalogPrice: 1250,
      rememberedPrice: 900,
    })).toEqual({ price: 1250, source: 'catalog' });
  });

  it('keeps a catalog act unresolved instead of silently using memory', () => {
    expect(resolveDevisTreatmentPrice({
      isCatalogAct: true,
      catalogPrice: undefined,
      rememberedPrice: 900,
    })).toEqual({ price: 0, source: 'catalog_missing' });
  });

  it('uses an explicit practitioner price for a non-catalog act', () => {
    expect(resolveDevisTreatmentPrice({
      isCatalogAct: false,
      practitionerPrice: 800,
      rememberedPrice: 600,
    })).toEqual({ price: 800, source: 'practitioner' });
  });

  it('uses remembered price only as a fallback for a non-catalog act', () => {
    expect(resolveDevisTreatmentPrice({
      isCatalogAct: false,
      rememberedPrice: 600,
    })).toEqual({ price: 600, source: 'memory' });
  });

  it('fails closed for invalid prices', () => {
    expect(resolveDevisTreatmentPrice({
      isCatalogAct: false,
      practitionerPrice: -10,
      rememberedPrice: Number.NaN,
    })).toEqual({ price: 0, source: 'unknown' });
  });
});
