import { describe, expect, it } from 'vitest';
import { evaluateDiagnosisWithoutAutomaticSubstitution } from './SafeDiagnosticEngine';

describe('P5-P0 DiagnosticEngine pharmacovigilance boundary', () => {
  it('signale une allergie pénicilline sans substituer automatiquement le protocole', () => {
    const result = evaluateDiagnosisWithoutAutomaticSubstitution({
      motif: 'DOULEUR',
      vitality: 'NEGATIVE',
      percussion: 'POSITIVE_AXIALE',
      palpation: '',
      radiology: '',
      lesionDuration: '',
      medicalHistory: 'Allergie pénicilline connue',
    });

    expect(result.protocol.some((line: string) => line.includes('AMOXICILLINE'))).toBe(true);
    expect(result.protocol.some((line: string) => line.includes('CLINDAMYCINE/MACROLIDE'))).toBe(false);
    expect(result.warnings.some((line: string) => /allergie.*pénicilline/i.test(line))).toBe(true);
    expect(result.warnings.some((line: string) => /validation.*praticien|aucune substitution/i.test(line))).toBe(true);
  });

  it('signale une allergie AINS sans remplacer automatiquement par des corticostéroïdes', () => {
    const result = evaluateDiagnosisWithoutAutomaticSubstitution({
      motif: 'DOULEUR',
      vitality: 'POSITIVE_PERSISTANTE',
      percussion: '',
      palpation: '',
      radiology: '',
      lesionDuration: '',
      medicalHistory: 'Allergie aux AINS',
    });

    expect(result.protocol.some((line: string) => line.includes('AINS'))).toBe(true);
    expect(result.protocol.some((line: string) => line.includes('CORTICOSTÉROÏDES'))).toBe(false);
    expect(result.warnings.some((line: string) => /allergie.*ains/i.test(line))).toBe(true);
    expect(result.warnings.some((line: string) => /validation.*praticien|aucune substitution/i.test(line))).toBe(true);
  });
});
