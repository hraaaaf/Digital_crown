export interface CatalogAct {
  id: string | number;
  base_price?: number | null;
}

export interface CatalogSpecialty {
  acts: CatalogAct[];
}

export interface ActSuggestion {
  id?: string | number;
  base_price?: number | null;
  isLocal?: boolean;
  [key: string]: unknown;
}

export function repairLocalActSuggestionPrices(
  suggestions: ActSuggestion[],
  specialties: CatalogSpecialty[],
): { suggestions: ActSuggestion[]; changed: boolean } {
  const prices = new Map<string, number>();
  specialties.forEach(specialty => {
    specialty.acts.forEach(act => {
      const price = Number(act.base_price);
      if (Number.isFinite(price) && price > 0) {
        prices.set(`template_${act.id}`, price);
      }
    });
  });

  let changed = false;
  const repaired = suggestions.map(suggestion => {
    if (!suggestion.isLocal) return suggestion;
    const id = String(suggestion.id ?? '');
    const catalogPrice = prices.get(id);
    if (!catalogPrice || Number(suggestion.base_price) === catalogPrice) return suggestion;

    changed = true;
    return { ...suggestion, base_price: catalogPrice };
  });

  return { suggestions: repaired, changed };
}
