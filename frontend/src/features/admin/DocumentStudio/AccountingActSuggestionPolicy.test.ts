import { describe, expect, it } from 'vitest';
import { buildLocalActSuggestions } from './AccountingActSuggestionPolicy';

describe('AccountingActSuggestionPolicy', () => {
  const templates = [
    { id: 1, name: 'Détartrage', category: 'Parodontologie', base_price: 450 },
    { id: 2, name: 'Composite molaire', category: 'Conservatrice', base_price: 700 },
  ];

  it('conserve le vrai prix catalogue dans une suggestion locale', () => {
    const result = buildLocalActSuggestions(templates, 'dét');

    expect(result).toEqual([
      expect.objectContaining({
        id: 'template_1',
        name: 'Détartrage',
        base_price: 450,
        category: 'Parodontologie',
        isLocal: true,
        is_habit: false,
      }),
    ]);
  });

  it('peut chercher par catégorie sans modifier le prix', () => {
    const result = buildLocalActSuggestions(templates, 'conserv');

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Composite molaire');
    expect(result[0].base_price).toBe(700);
  });

  it('ne propose rien pour une requête trop courte', () => {
    expect(buildLocalActSuggestions(templates, 'd')).toEqual([]);
  });
});
