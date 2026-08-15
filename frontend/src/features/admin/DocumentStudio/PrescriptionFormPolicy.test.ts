import { describe, expect, it } from 'vitest';
import {
  hasMissingMedicationForm,
  preserveExplicitMedicationForms,
} from './PrescriptionFormPolicy';

describe('PrescriptionFormPolicy', () => {
  it('detects a missing medication form but ignores examination rows', () => {
    expect(hasMissingMedicationForm([
      { type: 'MEDICAMENT', forme: '' },
      { type: 'EXAMEN', forme: '' },
    ])).toBe(true);

    expect(hasMissingMedicationForm([
      { type: 'MEDICAMENT', forme: 'COMPRIMÉS' },
      { type: 'EXAMEN', forme: '' },
    ])).toBe(false);
  });

  it('removes a hidden generated fallback and preserves the explicit source form', () => {
    const payload = {
      data: {
        medications: [
          { nom: 'TEST', forme: 'Sachets', type: 'MEDICAMENT' },
          { nom: 'PANORAMIQUE', forme: 'Sachets', type: 'EXAMEN' },
        ],
      },
    };

    preserveExplicitMedicationForms(payload, [
      { type: 'MEDICAMENT', forme: '' },
      { type: 'EXAMEN', forme: '' },
    ]);

    expect(payload.data.medications[0].forme).toBe('');
    expect(payload.data.medications[1].forme).toBe('');
  });

  it('keeps the practitioner-visible explicit form', () => {
    const payload = { data: { medications: [{ forme: 'Sachets' }] } };
    preserveExplicitMedicationForms(payload, [{ type: 'MEDICAMENT', forme: 'GÉLULES' }]);
    expect(payload.data.medications[0].forme).toBe('GÉLULES');
  });
});
