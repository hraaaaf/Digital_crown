import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useOrthoStore } from '../stores/useOrthoStore';
import {
  CephaloAnalysisWorkbenchPanel,
  cephaloAnalysisMetricKeys,
  formatCephaloNormText,
  readCephaloMetricValue,
} from './CephaloAnalysisWorkbenchPanel';

const P: any = {
  bg: '#fff', bgPanel: '#fff', bgCard: '#f8fafc', bgInput: '#fff',
  border: '#ddd', borderFocus: '#2255aa', text: '#111', textMuted: '#666',
  textDim: '#999', accent: '#2255aa', accentSuccess: '#0a0',
  accentWarning: '#b70', accentError: '#c00', shadow: 'none', shadowLg: 'none',
};
afterEach(cleanup);

describe('CephaloAnalysisWorkbenchPanel R19 contract', () => {
  it('keeps semantic measure selection inside native desktop keyboard-accessible buttons', () => {
    const previous = useOrthoStore.getState().anglesData;
    useOrthoStore.setState({
      anglesData: {
        metrics: { analyse_dentaire: {
          Surplomb: { valeur: 2.2, status: 'N/A' },
          Recouvrement: { valeur: 1.4, status: 'N/A' },
        }},
      } as any,
    });
    try {
      render(<CephaloAnalysisWorkbenchPanel P={P} analysis="com" />);
      const first = screen.getByRole('button', { name: 'Sélectionner la mesure Surplomb' });
      const second = screen.getByRole('button', { name: 'Sélectionner la mesure Recouvrement' });
      expect(first.getAttribute('aria-pressed')).toBe('true');
      expect(second.getAttribute('aria-pressed')).toBe('false');
      expect(first.closest('tr')?.hasAttribute('tabindex')).toBe(false);
      fireEvent.mouseEnter(first.closest('tr')!);
      expect(first.getAttribute('aria-pressed')).toBe('true');
      expect(second.getAttribute('aria-pressed')).toBe('false');
      fireEvent.focus(second);
      expect(second.getAttribute('aria-pressed')).toBe('true');
      expect(first.getAttribute('aria-pressed')).toBe('false');
      expect(document.querySelector('[data-r19-measure-detail="Recouvrement"]')).toBeTruthy();
      fireEvent.click(first);
      expect(first.getAttribute('aria-pressed')).toBe('true');
      expect(document.querySelector('[data-r19-measure-detail="Surplomb"]')).toBeTruthy();
    } finally {
      useOrthoStore.setState({ anglesData: previous });
    }
  });

  it('exposes the complete source-locked Steiner static profile rows', () => {
    expect(cephaloAnalysisMetricKeys.steiner).toEqual([
      'M_SNA_DEG_V1','M_SNB_DEG_V1','M_ANB_DEG_V1','M_U1_NA_DEG_V1','M_U1_NA_MM_V1',
      'M_L1_NB_DEG_V1','M_L1_NB_MM_V1','M_INTERINCISAL_DEG_V1','M_OCCLUSAL_PLANE_SN_DEG_V1',
      'M_SN_GOGN_DEG_V1','M_L1_GOGN_DEG_V1','M_SND_DEG_V1','M_POG_NB_MM_V1',
      'M_L1_DLINE_MM_V1','M_L1_DLINE_DEG_V1',
    ]);
  });

  it('exposes Tweed-Merrifield only through canonical LOT06 identities', () => {
    expect(cephaloAnalysisMetricKeys.tweed).toEqual([
      'M_FH_GOME_DEG_V1',
      'M_IMPA_GOME_DEG_V1',
      'M_FMIA_L1_FH_DEG_V1',
      'M_MERRIFIELD_Z_FH_DEG_V1',
    ]);
  });

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
