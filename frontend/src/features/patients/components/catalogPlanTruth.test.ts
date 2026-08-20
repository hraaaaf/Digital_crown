import { describe, expect, it } from 'vitest';
import { buildCatalogPlanStep, flattenActiveCatalogActs, normalizePersistedPlanStep } from './catalogPlanTruth';

describe('catalog connected truth', () => {
  it('keeps only active cabinet acts and maps the current price', () => {
    const acts = flattenActiveCatalogActs([
      {
        name: 'Prévention',
        acts: [
          { id: 1, name: 'Détartrage', code: 'DET-001', base_price: 500, is_active: true },
          { id: 2, name: 'Ancien acte', base_price: 100, is_active: false },
        ],
      },
    ]);
    expect(acts).toEqual([{ id: 1, name: 'Détartrage', code: 'DET-001', basePrice: 500, specialtyName: 'Prévention' }]);
  });

  it('captures manual overrides by value in the plan payload', () => {
    const step = buildCatalogPlanStep(
      { id: 7, name: 'Détartrage', code: 'DET-001', basePrice: 500, specialtyName: 'Prévention' },
      'Détartrage complet',
      450,
      'Ajouté le 20/08/2026',
      2,
    );
    expect(step.title).toBe('Détartrage complet');
    expect(step.catalog_snapshot).toEqual({ act_id: 7, code: 'DET-001', name: 'Détartrage complet', price: 450 });
    expect(step.assistant).toContain('450 DH');
    expect(step.assistant).toContain('Tarif capturé');
  });

  it('preserves a persisted snapshot when rebuilding a plan payload', () => {
    const normalized = normalizePersistedPlanStep({
      title: 'Détartrage complet',
      assistant: 'Catalogue cabinet · DET-001 · 450 DH · Tarif capturé',
      status: 'done',
      date_str: 'Fait le 20/08/2026',
      catalog_snapshot: { act_id: 7, code: 'DET-001', name: 'Détartrage complet', price: 450 },
    }, 0);
    expect(normalized.catalog_snapshot?.price).toBe(450);
    expect(normalized.status).toBe('done');
  });
});
