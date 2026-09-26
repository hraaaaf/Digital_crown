import { describe, expect, it } from 'vitest';
import type { CatalogAct, Specialty } from '../Settings/hooks/useCatalogStore';
import {
  dentitionForTooth,
  evaluateCatalogAct,
  searchableCatalogActs,
  suggestedCatalogActs,
  toothTypeForTooth,
} from './AccountingActApplicabilityPolicy';

const act = (overrides: Partial<CatalogAct> = {}): CatalogAct => ({
  id: 1,
  specialty_id: 1,
  name: 'Acte test',
  base_price: 100,
  is_active: true,
  is_favorite: false,
  usage_count: 0,
  applicability: {},
  ...overrides,
});

describe('AccountingActApplicabilityPolicy', () => {
  it('derives FDI dentition and tooth type from the selected tooth', () => {
    expect(dentitionForTooth(51)).toBe('PRIMARY');
    expect(dentitionForTooth(11)).toBe('PERMANENT');
    expect(toothTypeForTooth(51)).toBe('INCISOR');
    expect(toothTypeForTooth(55)).toBe('MOLAR');
    expect(toothTypeForTooth(16)).toBe('MOLAR');
  });

  it('rejects a permanent-only grouped bridge for a primary tooth', () => {
    const bridge = act({
      name: 'Bridge',
      applicability: {
        dentitions: ['PERMANENT'],
        selection_modes: ['GROUP'],
        min_selected_teeth: 3,
        suggestion_priority: 90,
      },
    });
    const evaluated = evaluateCatalogAct(bridge, 'PROTHESE', {
      selectedTeeth: [51, 52, 53],
      selectionMode: 'GROUP',
    });
    expect(evaluated.level).toBe('INCOMPATIBLE');
    expect(evaluated.reasons).toContain('dentition');
  });

  it('suggests a pediatric act for a primary tooth and keeps neutral legacy acts searchable', () => {
    const specialties: Specialty[] = [{
      id: 1,
      name: 'PEDODONTIE',
      pathologies: [],
      acts: [
        act({
          id: 1,
          name: 'Pulpotomie dent temporaire',
          applicability: {
            dentitions: ['PRIMARY'],
            selection_modes: ['INDIVIDUAL'],
            min_selected_teeth: 1,
            max_selected_teeth: 1,
            suggestion_priority: 90,
          },
        }),
        act({ id: 2, name: 'Acte personnalisé sans règles', applicability: {} }),
      ],
    }];
    const context = { selectedTeeth: [51], selectionMode: 'INDIVIDUAL' as const };
    expect(suggestedCatalogActs(specialties, context).map(x => x.act.name)).toEqual(['Pulpotomie dent temporaire']);
    expect(searchableCatalogActs(specialties, context).map(x => x.act.name)).toContain('Acte personnalisé sans règles');
  });

  it('does not suggest a search-only periodontal act while preserving access by search', () => {
    const specialties: Specialty[] = [{
      id: 1,
      name: 'PARODONTOLOGIE',
      pathologies: [],
      acts: [act({
        name: 'Surfaçage radiculaire',
        applicability: {
          dentitions: ['PRIMARY', 'PERMANENT'],
          suggestion_priority: 0,
          searchable_when_not_suggested: true,
        },
      })],
    }];
    const context = { selectedTeeth: [51], selectionMode: 'INDIVIDUAL' as const };
    expect(suggestedCatalogActs(specialties, context)).toHaveLength(0);
    expect(searchableCatalogActs(specialties, context)).toHaveLength(1);
  });
});
