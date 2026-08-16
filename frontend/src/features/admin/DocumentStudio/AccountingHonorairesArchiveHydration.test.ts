import { describe, expect, it } from 'vitest';
import { hydrateArchivedDevisRows } from './AccountingOdontogramSourcePolicy';

describe('P4 Honoraires archive hydration', () => {
  it('rehydrates montant-based Honoraires rows with odontogram metadata', () => {
    const rows = hydrateArchivedDevisRows(
      [
        { acte: 'Composite 2 faces', dent: '16', dents: [16], montant: 700 },
        { acte: 'Ligne manuelle', dent: 'Arcade', montant: 200 },
      ],
      [
        {
          tooth_number: 16,
          treatments: [{ code: 'COMP2', name: 'Composite 2 faces', price: 700 }],
          surfaces: ['M', 'O'],
          notes: 'Carie profonde',
        },
      ],
      index => 200 + index,
    );

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      id: 200,
      description: 'Composite 2 faces',
      dent: '16',
      price: 700,
      toothNumbers: [16],
      odontogramTreatmentCode: 'COMP2',
      odontogramSurfaces: ['M', 'O'],
      odontogramNotes: 'Carie profonde',
    });
    expect(rows[0]._odontogramKey).toMatch(/^16::archived-/);
    expect(rows[1]).toEqual({
      id: 201,
      description: 'Ligne manuelle',
      dent: 'Arcade',
      price: 200,
      toothNumbers: [],
    });
  });
});
