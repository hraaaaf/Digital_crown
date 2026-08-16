import { describe, expect, it } from 'vitest';
import { replaceOdontogramToothSelections } from './AccountingOdontogramPolicy';

describe('P3-B odontogram row metadata', () => {
  it('persists surfaces, notes and treatment code on each structured row', () => {
    const rows = replaceOdontogramToothSelections([], 16, [
      {
        toothNumber: 16,
        treatmentId: 'comp-2',
        treatmentCode: 'COMP2',
        name: 'Composite 2 faces',
        price: 700,
        category: 'CONSERVATRICE',
        surfaces: ['M', 'O'],
        notes: 'Carie profonde',
      },
    ], () => 100);

    expect(rows).toEqual([
      {
        id: 100,
        description: 'Composite 2 faces',
        dent: '16',
        price: 700,
        category: 'CONSERVATRICE',
        toothNumbers: [16],
        _odontogramKey: '16::comp-2',
        odontogramSurfaces: ['M', 'O'],
        odontogramNotes: 'Carie profonde',
        odontogramTreatmentCode: 'COMP2',
      },
    ]);
  });

  it('updates metadata without duplicating an existing tooth-treatment row', () => {
    const existing = [{
      id: 42,
      description: 'Composite 2 faces',
      dent: '16',
      price: 650,
      category: 'CONSERVATRICE',
      toothNumbers: [16],
      _odontogramKey: '16::comp-2',
      odontogramSurfaces: ['M'],
      odontogramNotes: 'Ancienne note',
      odontogramTreatmentCode: 'COMP2',
    }];

    const rows = replaceOdontogramToothSelections(existing, 16, [
      {
        toothNumber: 16,
        treatmentId: 'comp-2',
        treatmentCode: 'COMP2',
        name: 'Composite 2 faces',
        price: 700,
        category: 'CONSERVATRICE',
        surfaces: ['M', 'O'],
        notes: 'Note mise à jour',
      },
    ], () => 999);

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      id: 42,
      price: 700,
      odontogramSurfaces: ['M', 'O'],
      odontogramNotes: 'Note mise à jour',
    });
  });
});
