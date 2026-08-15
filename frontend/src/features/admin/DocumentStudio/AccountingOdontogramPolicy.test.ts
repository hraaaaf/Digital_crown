import { describe, expect, it } from 'vitest';
import {
  mergeOdontogramSelections,
  odontogramTreatmentKey,
} from './AccountingOdontogramPolicy';

describe('AccountingOdontogramPolicy P2-D', () => {
  it('produit une clé stable dent::traitement', () => {
    expect(odontogramTreatmentKey(16, 'endo')).toBe('16::endo');
  });

  it('n’ajoute pas deux fois le même traitement sur la même dent', () => {
    const selection = {
      toothNumber: 16,
      treatmentId: 'endo',
      name: 'Endodontie',
      price: 1200,
    };

    const first = mergeOdontogramSelections([], [selection], () => 1);
    const second = mergeOdontogramSelections(first, [selection], () => 2);

    expect(second).toHaveLength(1);
    expect(second[0]._odontogramKey).toBe('16::endo');
    expect(second[0].price).toBe(1200);
  });

  it('retire les anciennes lignes odontogramme absentes de la sélection sans supprimer les lignes manuelles', () => {
    const current = [
      { id: 1, description: 'Manuel', dent: '-', price: 300 },
      { id: 2, description: 'Composite', dent: '11', price: 500, _odontogramKey: '11::comp' },
    ];

    const next = mergeOdontogramSelections(current, [], () => 3);

    expect(next).toEqual([{ id: 1, description: 'Manuel', dent: '-', price: 300 }]);
  });

  it('autorise le même traitement sur deux dents différentes', () => {
    const next = mergeOdontogramSelections(
      [],
      [
        { toothNumber: 11, treatmentId: 'comp', name: 'Composite', price: 500 },
        { toothNumber: 21, treatmentId: 'comp', name: 'Composite', price: 500 },
      ],
      (() => {
        let id = 0;
        return () => ++id;
      })(),
    );

    expect(next.map(item => item._odontogramKey)).toEqual(['11::comp', '21::comp']);
  });
});
