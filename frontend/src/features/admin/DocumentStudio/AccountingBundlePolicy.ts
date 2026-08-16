export interface AccountingBundleSuggestion {
  name: string;
  category?: string;
  price?: number;
}

export interface AccountingCatalogPrice {
  name: string;
  base_price?: number | string | null;
  category?: string;
}

export interface ResolvedAccountingBundle {
  name: string;
  category: string;
  price: number;
  priceSource: 'CATALOG' | 'UNRESOLVED';
}

const normalize = (value: string) => value.trim().toLocaleLowerCase('fr');

/**
 * Bundle rules decide which complementary act to suggest.
 * The managed catalog remains the only authoritative automatic price source.
 * Backend hard-coded/legacy bundle prices are deliberately ignored.
 */
export function resolveAccountingBundles(
  suggestions: AccountingBundleSuggestion[],
  catalog: AccountingCatalogPrice[],
): ResolvedAccountingBundle[] {
  const byName = new Map(catalog.map(item => [normalize(item.name), item]));
  const seen = new Set<string>();
  const result: ResolvedAccountingBundle[] = [];

  for (const suggestion of suggestions) {
    const key = normalize(suggestion.name || '');
    if (!key || seen.has(key)) continue;
    seen.add(key);

    const catalogAct = byName.get(key);
    const catalogPrice = Number(catalogAct?.base_price);
    const hasAuthoritativePrice = Number.isFinite(catalogPrice) && catalogPrice > 0;

    result.push({
      name: suggestion.name.trim(),
      category: catalogAct?.category || suggestion.category || 'GÉNÉRAL',
      price: hasAuthoritativePrice ? catalogPrice : 0,
      priceSource: hasAuthoritativePrice ? 'CATALOG' : 'UNRESOLVED',
    });
  }

  return result;
}
