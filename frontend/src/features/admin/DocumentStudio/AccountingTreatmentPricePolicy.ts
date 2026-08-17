export type DevisTreatmentPriceSource =
  | 'catalog'
  | 'catalog_missing'
  | 'practitioner'
  | 'memory'
  | 'unknown';

export interface ResolveDevisTreatmentPriceInput {
  isCatalogAct: boolean;
  catalogPrice?: number | null;
  practitionerPrice?: number | null;
  rememberedPrice?: number | null;
}

export interface ResolvedDevisTreatmentPrice {
  price: number;
  source: DevisTreatmentPriceSource;
}

function finiteNonNegative(value: number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const normalized = Number(value);
  return Number.isFinite(normalized) && normalized >= 0 ? normalized : null;
}

/**
 * P3-C authoritative pricing rule for Devis treatment selection.
 *
 * A catalog entry is authoritative whenever the selected act comes from the
 * catalog. An empty/invalid catalog tariff must stay visibly unresolved (0)
 * instead of being replaced by a remembered local price. Practitioner and
 * memory prices are fallbacks only for non-catalog acts.
 */
export function resolveDevisTreatmentPrice(
  input: ResolveDevisTreatmentPriceInput,
): ResolvedDevisTreatmentPrice {
  const catalogPrice = finiteNonNegative(input.catalogPrice);
  const practitionerPrice = finiteNonNegative(input.practitionerPrice);
  const rememberedPrice = finiteNonNegative(input.rememberedPrice);

  if (input.isCatalogAct) {
    if (catalogPrice !== null && catalogPrice > 0) {
      return { price: catalogPrice, source: 'catalog' };
    }
    return { price: 0, source: 'catalog_missing' };
  }

  if (practitionerPrice !== null && practitionerPrice > 0) {
    return { price: practitionerPrice, source: 'practitioner' };
  }

  if (rememberedPrice !== null && rememberedPrice > 0) {
    return { price: rememberedPrice, source: 'memory' };
  }

  return { price: 0, source: 'unknown' };
}
