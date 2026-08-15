import { describe, expect, it } from 'vitest';
import {
  classifyAccountingPhase,
  groupAccountingItemsByPhase,
} from './AccountingPhasePolicy';

describe('AccountingPhasePolicy P2-C', () => {
  it('classe les actes de façon déterministe sans prétendre utiliser une IA', () => {
    expect(classifyAccountingPhase('Détartrage complet')).toBe('ASSAINISSEMENT');
    expect(classifyAccountingPhase('Extraction 48')).toBe('CHIRURGIE');
    expect(classifyAccountingPhase('Couronne zircone')).toBe('PROTHETIQUE');
    expect(classifyAccountingPhase('Consultation')).toBe('AUTRES');
  });

  it('regroupe les phases sans injecter de durée de cicatrisation', () => {
    const groups = groupAccountingItemsByPhase([
      { description: 'Extraction simple' },
      { description: 'Couronne céramique' },
    ]);

    expect(groups.map(group => group.label)).toEqual([
      'Phase 2 : Chirurgie',
      'Phase 3 : Prothétique',
    ]);
    expect(JSON.stringify(groups)).not.toMatch(/3 mois|cicatrisation/i);
  });

  it('ignore les anciens séparateurs de phase lors d’un nouveau regroupement', () => {
    const groups = groupAccountingItemsByPhase([
      { description: '--- PHASE 1 : ASSAINISSEMENT ---' },
      { description: 'Composite 11' },
    ]);

    expect(groups).toHaveLength(1);
    expect(groups[0].items).toEqual([{ description: 'Composite 11' }]);
  });
});
