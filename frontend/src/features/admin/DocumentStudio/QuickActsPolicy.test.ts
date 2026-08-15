import { describe, expect, it } from 'vitest';
import { normalizeQuickActs } from './QuickActsPolicy';

describe('QuickActsPolicy', () => {
  const acts = [
    { name: 'Composite 1 face', price: 420, category: 'CONSERVATRICE' },
    { name: 'Traitement endodontique', price: 900, category: 'ENDO' },
    { name: 'Consultation', price: 250, category: 'CONSULTATION' },
  ];

  it('normalise les libellés patient sans modifier les prix ni les catégories', () => {
    expect(normalizeQuickActs(acts, 'SELF')).toEqual([
      { name: 'Composite', price: 420, category: 'CONSERVATRICE' },
      { name: 'Endodontie', price: 900, category: 'ENDO' },
      { name: 'Consultation', price: 250, category: 'CONSULTATION' },
    ]);
  });

  it('utilise une terminologie explicite pour un tiers payeur sans toucher aux montants', () => {
    expect(normalizeQuickActs(acts, 'THIRD_PARTY')).toEqual([
      { name: 'Restauration composite', price: 420, category: 'CONSERVATRICE' },
      { name: 'Traitement endodontique', price: 900, category: 'ENDO' },
      { name: 'Consultation', price: 250, category: 'CONSULTATION' },
    ]);
  });
});
