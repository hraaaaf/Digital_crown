import { describe, expect, it } from 'vitest';

import {
  buildTeethDataFromAccountingItems,
  canonicalDentLabel,
  hydrateAccountingItemsFromTeethData,
  hydrateArchivedDevisRows,
  normalizeStructuredAccountingItems,
} from './AccountingOdontogramSourcePolicy';

describe('P3-B odontogram source of truth', () => {
  it('uses structured tooth numbers instead of an edited free-text dent label', () => {
    const item = {
      id: 1,
      description: 'Couronne',
      dent: '21',
      price: 3500,
      toothNumbers: [16],
      _odontogramKey: '16::crown',
    };

    expect(canonicalDentLabel(item)).toBe('16');
    expect(normalizeStructuredAccountingItems([item])[0].dent).toBe('16');
  });

  it('uses the same comma-separated multi-tooth label as backend/PDF', () => {
    const item = {
      id: 12,
      description: 'Bridge',
      dent: '14-15-16',
      price: 9000,
      toothNumbers: [14, 15, 16],
    };

    expect(canonicalDentLabel(item)).toBe('14, 15, 16');
    expect(normalizeStructuredAccountingItems([item])[0].dent).toBe('14, 15, 16');
  });

  it('leaves a manual financial row untouched', () => {
    const manual = { id: 2, description: 'Remise exceptionnelle', dent: 'Arcade', price: -100 };
    expect(normalizeStructuredAccountingItems([manual])).toEqual([manual]);
  });

  it('builds one teeth_data entry per tooth with treatments, surfaces and notes', () => {
    const teethData = buildTeethDataFromAccountingItems([
      {
        id: 3,
        description: 'Composite 2 faces',
        dent: '21',
        price: 700,
        toothNumbers: [16],
        _odontogramKey: '16::comp-2',
        odontogramTreatmentCode: 'COMP2',
        odontogramSurfaces: ['M', 'O'],
        odontogramNotes: 'Carie profonde',
      },
      {
        id: 4,
        description: 'Traitement canalaire',
        dent: '16',
        price: 1800,
        toothNumbers: [16],
        _odontogramKey: '16::endo',
        odontogramTreatmentCode: 'ENDO',
        odontogramSurfaces: ['O'],
        odontogramNotes: 'Carie profonde',
      },
      {
        id: 5,
        description: 'Bridge',
        dent: '14, 15, 16',
        price: 9000,
        toothNumbers: [14, 15, 16],
      },
    ]);

    expect(teethData).toEqual([
      {
        tooth_number: 16,
        treatments: [
          { code: 'COMP2', name: 'Composite 2 faces', price: 700 },
          { code: 'ENDO', name: 'Traitement canalaire', price: 1800 },
        ],
        surfaces: ['M', 'O'],
        notes: 'Carie profonde',
      },
    ]);
  });

  it('rehydrates archived odontogram metadata without inventing financial rows', () => {
    const items = [
      { id: 10, description: 'Couronne Zircone', dent: '16', price: 4200, toothNumbers: [16] },
      { id: 11, description: 'Ligne manuelle', dent: '-', price: 200 },
    ];

    const hydrated = hydrateAccountingItemsFromTeethData(items, [
      {
        tooth_number: 16,
        treatments: [{ code: 'ZIRC', name: 'Couronne Zircone', price: 4200 }],
        surfaces: ['ALL'],
        notes: 'Pilier préparé',
      },
    ]);

    expect(hydrated).toHaveLength(2);
    expect(hydrated[0]).toMatchObject({
      dent: '16',
      toothNumbers: [16],
      odontogramTreatmentCode: 'ZIRC',
      odontogramSurfaces: ['ALL'],
      odontogramNotes: 'Pilier préparé',
    });
    expect(hydrated[0]._odontogramKey).toMatch(/^16::archived-/);
    expect(hydrated[1]).toEqual(items[1]);
  });

  it('rebuilds archived DocumentHub Devis rows and restores teeth_data metadata', () => {
    const rows = hydrateArchivedDevisRows(
      [
        { acte: 'Composite 2 faces', dent: '16', dents: [16], prix_unitaire: 700 },
        { acte: 'Bridge', dent: '14-15-16', dents: ['16', 14, 15, 14], prix_unitaire: 9000 },
        { acte: 'Ligne manuelle', dent: 'Arcade', montant: 200 },
      ],
      [
        {
          tooth_number: 16,
          treatments: [{ code: 'COMP2', name: 'Composite 2 faces', price: 700 }],
          surfaces: ['M', 'O', 'M'],
          notes: 'Carie profonde',
        },
      ],
      index => 100 + index,
    );

    expect(rows).toHaveLength(3);
    expect(rows[0]).toMatchObject({
      id: 100,
      description: 'Composite 2 faces',
      dent: '16',
      price: 700,
      toothNumbers: [16],
      odontogramTreatmentCode: 'COMP2',
      odontogramSurfaces: ['M', 'O'],
      odontogramNotes: 'Carie profonde',
    });
    expect(rows[0]._odontogramKey).toMatch(/^16::archived-/);
    expect(rows[1]).toMatchObject({
      id: 101,
      description: 'Bridge',
      dent: '14, 15, 16',
      price: 9000,
      toothNumbers: [14, 15, 16],
    });
    expect(rows[2]).toEqual({
      id: 102,
      description: 'Ligne manuelle',
      dent: 'Arcade',
      price: 200,
      toothNumbers: [],
    });
  });
});
