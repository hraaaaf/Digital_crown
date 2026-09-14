import { describe, expect, it } from 'vitest';
import {
  cephaloAnalysisMetricKeys,
  formatCephaloNormText,
  readCephaloMetricValue,
} from './CephaloAnalysisWorkbenchPanel';

describe('CephaloAnalysisWorkbenchPanel R19 contract', () => {
  it('keeps COM autonomous with the ten source-locked rows', () => {
    expect(cephaloAnalysisMetricKeys.com).toEqual([
      'Surplomb',
      'Recouvrement',
      'IMPA',
      'I_Francfort',
      'Inter_Incisif',
      'Angle_de_Tweed',
      'Decalage_A_B',
      'Situation_A',
      'Situation_B',
      'Profondeur_Faciale',
    ]);
    expect(cephaloAnalysisMetricKeys.mcnamara).toEqual(['Co_A', 'Co_Gn', 'ANS_Me']);
  });

  it('reads both current valeur and value payload shapes without synthesizing missing data', () => {
    expect(readCephaloMetricValue({ valeur: 2.4, status: 'N/A' })).toBe(2.4);
    expect(readCephaloMetricValue({ value: -1.2, status: 'N/A' })).toBe(-1.2);
    expect(readCephaloMetricValue({ status: 'Missing' })).toBeNull();
  });

  it('shows only norms carried by the result payload', () => {
    expect(formatCephaloNormText({ norm_min: 85, norm_max: 95, status: 'N/A' }, '°')).toBe('85,0 à 95,0 °');
    expect(formatCephaloNormText({ status: 'N/A' }, 'mm')).toBe('—');
  });
});
