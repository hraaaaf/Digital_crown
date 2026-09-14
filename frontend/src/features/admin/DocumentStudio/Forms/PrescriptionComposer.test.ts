import { describe, expect, it } from 'vitest';
import {
  composePrescriptionPosology,
  parsePrescriptionPosology,
} from './PrescriptionComposer';

describe('PrescriptionComposer', () => {
  it('compose le schéma régulier du mockup sans modifier le contrat posologie', () => {
    expect(composePrescriptionPosology({
      amount: '1 comprimé',
      frequency: '3 fois par jour',
      constraint: '7 jours',
      context: 'après les repas',
    })).toBe('1 comprimé, 3 fois par jour pendant 7 jours, après les repas.');
  });

  it('compose le schéma si douleur avec plafond quotidien et durée', () => {
    expect(composePrescriptionPosology({
      amount: '1 comprimé',
      frequency: 'si douleur',
      constraint: 'max 3/jour',
      context: '3 jours',
    })).toBe('1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.');
  });

  it('conserve si douleur lors du roundtrip avec plafond quotidien', () => {
    const state = {
      amount: '1 comprimé',
      frequency: 'si douleur',
      constraint: 'max 3/jour',
      context: '3 jours',
    };
    expect(parsePrescriptionPosology(composePrescriptionPosology(state))).toEqual(state);
  });

  it('reconnaît un preset historique x 3 par jour', () => {
    expect(parsePrescriptionPosology('1 cp x 3 / jour pendant 4 jours')).toEqual({
      amount: '1 comprimé',
      frequency: '3 fois par jour',
      constraint: '4 jours',
      context: '',
    });
  });

  it('reconnaît matin et soir, durée et prise pendant les repas', () => {
    expect(parsePrescriptionPosology('1 cp Matin et Soir pendant 3 jours (au milieu des repas)')).toEqual({
      amount: '1 comprimé',
      frequency: 'matin et soir',
      constraint: '3 jours',
      context: 'pendant les repas',
    });
  });

  it('préserve un texte non reconnu en dehors du composer jusqu’à action explicite', () => {
    expect(parsePrescriptionPosology('Selon protocole personnalisé du praticien')).toEqual({
      amount: '',
      frequency: '',
      constraint: '',
      context: '',
    });
  });
});
