import { describe, expect, it } from 'vitest';
import { repairLocalActSuggestionPrices } from './AccountingActSuggestionPolicy';

describe('repairLocalActSuggestionPrices', () => {
  const specialties = [
    { acts: [{ id: 12, base_price: 450 }, { id: 99, base_price: 0 }] },
  ];

  it('restaure le vrai prix catalogue d’une suggestion locale', () => {
    const source = [{ id: 'template_12', name: 'Détartrage', base_price: 0, isLocal: true }];
    const result = repairLocalActSuggestionPrices(source, specialties);

    expect(result.changed).toBe(true);
    expect(result.suggestions[0].base_price).toBe(450);
    expect(source[0].base_price).toBe(0);
  });

  it('ne modifie pas une suggestion API/non locale', () => {
    const source = [{ id: 'template_12', base_price: 300, isLocal: false }];
    const result = repairLocalActSuggestionPrices(source, specialties);

    expect(result.changed).toBe(false);
    expect(result.suggestions).toEqual(source);
  });

  it('n’invente pas de prix lorsque le catalogue vaut zéro ou est absent', () => {
    const source = [
      { id: 'template_99', base_price: 0, isLocal: true },
      { id: 'template_404', base_price: 0, isLocal: true },
    ];
    const result = repairLocalActSuggestionPrices(source, specialties);

    expect(result.changed).toBe(false);
    expect(result.suggestions).toEqual(source);
  });
});
