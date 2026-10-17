import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { CEPHALO_METRIC_FOCUS_EVENT, type CephaloMetricFocus } from '../cephaloAnalysisBridge';

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
  it('publishes exact active Co_anatomic focus on selection and clears it for blocked factors', () => {
    const old = useOrthoStore.getState().anglesData;
    const item: any = profile('mcnamara');
    item.rows[0] = {
      ...item.rows[0],
      canonical_measurement_id: 'M_CO_A_MM_V1',
      label: 'Co–A exact',
      availability_status: 'AVAILABLE',
      value: 12.3,
      measurement_refs: ['m:source-1'],
      value_authority_method_id: 'MCNAMARA_CO_A_CANONICAL_MM_V2',
      focus_evidence: {
        authority: 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1',
        canonical_measurement_id: 'M_CO_A_MM_V1',
        measurement_ref: 'm:source-1',
        value_authority_method_id: 'MCNAMARA_CO_A_CANONICAL_MM_V2',
        landmark_ids: ['Co_anatomic', 'A'],
        construction_ids: [],
        calibration_required: true,
      },
    };
    const events: Array<CephaloMetricFocus | null> = [];
    const receive = (event: Event) => events.push((event as CustomEvent<CephaloMetricFocus | null>).detail);
    window.addEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
    useOrthoStore.setState({ anglesData: {
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED',
        protocol_profiles: { mcnamara: item },
      },
    } });
    try {
      render(<CephaloAnalysisWorkbenchPanel P={P} analysis="mcnamara" />);
      fireEvent.click(document.querySelector('[data-r23g3-focus-select="M_CO_A_MM_V1"]')!);
      expect(events.at(-1)?.points).toEqual(['Co_anatomic','A']);
      expect(events.at(-1)?.points).not.toContain('Co');
      expect(events.at(-1)?.lines).toEqual([]);
      fireEvent.click(document.querySelector('[data-r23g3-focus-select="M_TEST_2_MM_V1"]')!);
      expect(events.at(-1)).toBeNull();
      expect(document.querySelector('[data-r23g3-focus-source="not-authorized"]')).toBeTruthy();
    } finally {
      window.removeEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
      useOrthoStore.setState({ anglesData: old });
    }
  });

  it('renders source-only Atlas U1 dependencies without activating geometry, and clears them on Gregoret', () => {
    const old = useOrthoStore.getState().anglesData;
    const atlas: any = profile('atlas');
    atlas.rows[10] = {
      ...atlas.rows[10],
      canonical_measurement_id: 'M_RICKETTS_U1_APOG_PROTRUSION_MM_V1',
      label: 'Incisive supérieure vers A-Pog',
      contract_state: 'EXECUTABLE',
      contract_gate: 'U1_INCISAL_EDGE_PERPENDICULAR_APOG__ANTERIOR_POSITIVE__VERIFIED_CALIBRATION_REQUIRED',
    };
    const events: Array<CephaloMetricFocus | null> = [];
    const receive = (event: Event) => events.push((event as CustomEvent<CephaloMetricFocus | null>).detail);
    window.addEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
    useOrthoStore.setState({ anglesData: {
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED',
        protocol_profiles: { ricketts_atlas2009: atlas, ricketts_gregoret13: profile('gregoret') },
      },
    } });
    try {
      render(<CephaloAnalysisWorkbenchPanel P={P} analysis="ricketts" />);
      fireEvent.click(document.querySelector('[data-r23g3-focus-select="M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"]')!);
      expect(document.querySelector('[data-r23g7-atlas-gate="M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"]')).toBeTruthy();
      expect(screen.getByText(/sans autorisation de mesure/)).toBeTruthy();
      expect(document.querySelector('[data-r23g3-focus-source="not-authorized"]')).toBeTruthy();
      expect(events.at(-1)).toBeNull();
      fireEvent.click(screen.getByRole('button', { name: 'Gregoret · 13 facteurs' }));
      expect(document.querySelector('[data-r23g7-atlas-gate]')).toBeNull();
      expect(events.at(-1)).toBeNull();
    } finally {
      window.removeEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
      useOrthoStore.setState({ anglesData: old });
    }
  });

  it('shows W1 same-image orientation obligations without claiming evidence or focus', () => {
    const old = useOrthoStore.getState().anglesData;
    const atlas: any = profile('atlas');
    atlas.rows[23] = {
      ...atlas.rows[23],
      canonical_measurement_id: 'M_RICKETTS_PALATAL_PLANE_FH_DEG_V1',
      label: 'Plan palatin–Frankfort',
      contract_state: 'CONDITIONAL_EXECUTABLE',
      contract_gate: 'VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED',
    };
    const events: Array<CephaloMetricFocus | null> = [];
    const receive = (event: Event) => events.push((event as CustomEvent<CephaloMetricFocus | null>).detail);
    window.addEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
    useOrthoStore.setState({ anglesData: {
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED',
        protocol_profiles: { ricketts_atlas2009: atlas, ricketts_gregoret13: profile('gregoret') },
      },
    } });
    try {
      render(<CephaloAnalysisWorkbenchPanel P={P} analysis="ricketts" />);
      fireEvent.click(document.querySelector('[data-r23g3-focus-select="M_RICKETTS_PALATAL_PLANE_FH_DEG_V1"]')!);
      expect(document.querySelector('[data-r23g8-w1-orientation-gate="M_RICKETTS_PALATAL_PLANE_FH_DEG_V1"]')).toBeTruthy();
      expect(screen.getByText(/orientation anatomique obligatoire et NON vérifiée/)).toBeTruthy();
      expect(screen.getByText(/Aucune valeur ni Focus autorisé par cet aperçu/)).toBeTruthy();
      expect(document.querySelector('[data-r23g3-focus-source="not-authorized"]')).toBeTruthy();
      expect(events.at(-1)).toBeNull();
      fireEvent.click(screen.getByRole('button', { name: 'Gregoret · 13 facteurs' }));
      expect(document.querySelector('[data-r23g8-w1-orientation-gate]')).toBeNull();
      expect(events.at(-1)).toBeNull();
    } finally {
      window.removeEventListener(CEPHALO_METRIC_FOCUS_EVENT, receive);
      useOrthoStore.setState({ anglesData: old });
    }
  });

});
