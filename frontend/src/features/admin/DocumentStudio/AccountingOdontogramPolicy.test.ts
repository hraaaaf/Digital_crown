import { describe, expect, it } from 'vitest';
import {
  mergeOdontogramSelections,
  odontogramTreatmentKey,
  replaceOdontogramToothSelections,
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

  it('remplace uniquement la dent éditée et préserve les autres dents ainsi que les lignes manuelles', () => {
    const current = [
      { id: 1, description: 'Manuel', dent: '-', price: 300 },
      { id: 2, description: 'Composite', dent: '16', price: 500, _odontogramKey: '16::comp' },
      { id: 3, description: 'Endodontie', dent: '21', price: 1200, _odontogramKey: '21::endo' },
    ];

    const next = replaceOdontogramToothSelections(
      current,
      16,
      [{ toothNumber: 16, treatmentId: 'crown', name: 'Couronne', price: 2500, dent: '16 (MOD)' }],
      () => 4,
    );

    expect(next).toEqual([
      { id: 1, description: 'Manuel', dent: '-', price: 300 },
      { id: 3, description: 'Endodontie', dent: '21', price: 1200, _odontogramKey: '21::endo' },
      {
        id: 4,
        description: 'Couronne',
        dent: '16 (MOD)',
        price: 2500,
        category: undefined,
        toothNumbers: [16],
        _odontogramKey: '16::crown',
        odontogramSurfaces: [],
        odontogramNotes: '',
        odontogramTreatmentCode: 'ACT',
      },
    ]);
  });

  it('réutilise la ligne existante quand la même sélection est reconfirmée', () => {
    const current = [
      { id: 9, description: 'Composite', dent: '16', price: 500, _odontogramKey: '16::comp' },
    ];

    const next = replaceOdontogramToothSelections(
      current,
      16,
      [{ toothNumber: 16, treatmentId: 'comp', name: 'Composite', price: 600 }],
      () => 10,
    );

    expect(next).toHaveLength(1);
    expect(next[0].id).toBe(9);
    expect(next[0].price).toBe(600);
  });

  it('préserve le libellé de surface existant si aucune nouvelle surface n’est fournie', () => {
    const current = [
      {
        id: 9,
        description: 'Composite',
        dent: '16 (MOD)',
        price: 500,
        _odontogramKey: '16::comp',
        odontogramSurfaces: ['M', 'O', 'D'],
        odontogramNotes: 'ancien contexte',
      },
    ];

    const next = replaceOdontogramToothSelections(
      current,
      16,
      [{ toothNumber: 16, treatmentId: 'comp', name: 'Composite', price: 600 }],
      () => 10,
    );

    expect(next[0].dent).toBe('16 (MOD)');
    expect(next[0].odontogramSurfaces).toEqual(['M', 'O', 'D']);
    expect(next[0].odontogramNotes).toBe('ancien contexte');
  });
});
