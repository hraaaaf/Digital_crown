import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';

const P: any = {
  bg: '#fff', bgPanel: '#fff', bgCard: '#f8fafc', bgInput: '#fff',
  border: '#ddd', borderFocus: '#2255aa', text: '#111', textMuted: '#666',
  textDim: '#999', accent: '#2255aa', accentSuccess: '#0a0',
  accentWarning: '#b70', accentError: '#c00', shadow: 'none', shadowLg: 'none',
};

const profile = (kind: 'atlas' | 'gregoret' | 'mcnamara') => {
  const full = {
    atlas: ['RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1', 33, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL', 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
    gregoret: ['RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1', 13, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED', 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
    mcnamara: ['MCNAMARA_1984_SINGLE_FILM_V1', 13, 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL', 'HISTORICAL_WORKING_REFERENCE_ONLY'],
  } as const;
  const [id, count, state, gate] = full[kind];
  return {
    protocol_profile_id: id, profile_status: state, source_lock_gate: gate,
    classification_authority: false,
    rows: Array.from({ length: count }, (_, index) => ({
      order: index + 1,
      canonical_measurement_id: 'M_TEST_' + String(index + 1) + '_MM_V1',
      label: 'Facteur ' + String(index + 1),
      unit: 'mm', value: null, availability_status: 'NOT_COMPUTABLE',
      contract_state: 'CONDITIONAL_EXECUTABLE', classification_authority: false,
      source_contract: id, measurement_refs: [], value_authority_method_id: null,
    })),
  };
};

const readings = {
  scientific_read_path: {
    authority: 'EVIDENCE_GRAPH_V1',
    active_chain: 'VERIFIED',
    protocol_profiles: {
      ricketts_atlas2009: profile('atlas'),
      ricketts_gregoret13: profile('gregoret'),
      mcnamara: profile('mcnamara'),
    },
  },
};

afterEach(cleanup);

describe('R23-G2 full read-only profile tables', () => {
  it('renders 33 Atlas factors, then exactly 13 Gregoret factors without numeric substitution', () => {
    const old = useOrthoStore.getState().anglesData;
    useOrthoStore.setState({ anglesData: readings });
    try {
      render(<CephaloAnalysisWorkbenchPanel P={P} analysis="ricketts" />);
      expect(document.querySelectorAll('[data-r23g2-measurement-id]')).toHaveLength(33);
      expect(screen.getByText(/0\/33 valeurs disponibles/)).toBeTruthy();
      fireEvent.click(screen.getByRole('button', { name: 'Gregoret · 13 facteurs' }));
      expect(document.querySelectorAll('[data-r23g2-measurement-id]')).toHaveLength(13);
      expect(screen.getByText(/0\/13 valeurs disponibles/)).toBeTruthy();
      expect(document.querySelectorAll('[data-r23g2-measurement-id] td')).toHaveLength(26);
    } finally {
      useOrthoStore.setState({ anglesData: old });
    }
  });

  it('shows 13 historical McNamara rows but refuses any unverified read path', () => {
    const old = useOrthoStore.getState().anglesData;
    useOrthoStore.setState({ anglesData: readings });
    try {
      const { rerender } = render(<CephaloAnalysisWorkbenchPanel P={P} analysis="mcnamara" />);
      expect(document.querySelectorAll('[data-r23g2-measurement-id]')).toHaveLength(13);
      useOrthoStore.setState({
        anglesData: { scientific_read_path: { ...readings.scientific_read_path, active_chain: 'STALE' } },
      });
      rerender(<CephaloAnalysisWorkbenchPanel P={P} analysis="mcnamara" />);
      expect(document.querySelectorAll('[data-r23g2-measurement-id]')).toHaveLength(0);
      expect(screen.getByText(/Profil non vérifié/)).toBeTruthy();
    } finally {
      useOrthoStore.setState({ anglesData: old });
    }
  });
});
