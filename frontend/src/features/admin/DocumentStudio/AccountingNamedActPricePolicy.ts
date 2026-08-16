export interface NamedCatalogAct {
  name: string;
  base_price?: number | string | null;
  category?: string;
}

export interface ResolvedNamedActPrice {
  price: number;
  category?: string;
  source: 'CATALOG' | 'UNRESOLVED';
}

function normalizeActName(value: string): string {
  return value.trim().toLocaleLowerCase('fr').replace(/\s+/g, ' ');
}

/**
 * Devis pricing rule for named shortcuts/groups.
 * The managed catalog is authoritative. Remembered or hard-coded fallback prices
 * must not silently become quote amounts.
 */
export function resolveNamedDevisActPrice(
  name: string,
  catalogActs: NamedCatalogAct[],
): ResolvedNamedActPrice {
  const wanted = normalizeActName(name);
  const match = catalogActs.find(act => normalizeActName(act.name) === wanted);
  const price = Number(match?.base_price);

  if (match && Number.isFinite(price) && price > 0) {
    return { price, category: match.category, source: 'CATALOG' };
  }
  return { price: 0, category: match?.category, source: 'UNRESOLVED' };
}
