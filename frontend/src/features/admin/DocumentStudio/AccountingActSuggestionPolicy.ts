export interface CatalogActTemplate {
  id: string | number;
  name: string;
  category: string;
  base_price: number;
}

export interface LocalActSuggestion {
  id: string;
  name: string;
  base_price: number;
  category: string;
  isLocal: true;
  is_habit: false;
}

export function buildLocalActSuggestions(
  templates: CatalogActTemplate[],
  query: string,
): LocalActSuggestion[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (normalizedQuery.length < 2) return [];

  return templates
    .filter(template =>
      template.name.toLowerCase().includes(normalizedQuery)
      || template.category.toLowerCase().includes(normalizedQuery),
    )
    .map(template => ({
      id: `template_${template.id}`,
      name: template.name,
      base_price: Number(template.base_price) || 0,
      category: template.category,
      isLocal: true as const,
      is_habit: false as const,
    }));
}
