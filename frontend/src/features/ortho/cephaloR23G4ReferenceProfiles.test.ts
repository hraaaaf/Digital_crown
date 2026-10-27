import { describe, expect, it } from 'vitest';
import {
  isR23G4ReferenceBound, readCephaloR23G2Protocol,
  resolveR23G3RuntimeFocus, type R23G2Analysis,
} from './cephaloR23G4ReferenceProfiles';

const meta = {
  mcnamara: ['mcnamara', 'MCNAMARA_1984_SINGLE_FILM_V1', 13, 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL', 'HISTORICAL_WORKING_REFERENCE_ONLY'],
  com: ['com', 'COM_DC_LEGACY_V1', 10, 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL', 'HISTORICAL_WORKING_REFERENCE_ONLY'],
  atlas: ['ricketts_atlas2009', 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1', 33, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL', 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
  gregoret: ['ricketts_gregoret13', 'RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1', 13, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED', 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED'],
} as const;
const comIds = [
  'M_COM_DC_LEGACY_OVERJET_FH_MM_V1',
  'M_COM_DC_LEGACY_OVERBITE_SCREEN_POSITIVE_Y_FH_MM_V1',
  'M_IMPA_GOME_DEG_V1',
  'M_COM_DC_LEGACY_U1_FH_PO_OR_DEG_V1',
  'M_INTERINCISAL_DEG_V1',
  'M_COM_DC_LEGACY_FMA_PO_OR_DEG_V1',
  'M_COM_DC_LEGACY_AB_PRIME_PO_OR_MM_V1',
  'M_COM_DC_LEGACY_A_NPERP_PO_OR_MM_V1',
  'M_COM_DC_LEGACY_B_NPERP_PO_OR_MM_V1',
  'M_COM_DC_LEGACY_S_NPERP_DEPTH_PO_OR_MM_V1',
] as const;
type Key = keyof typeof meta;
const profile = (key: Key) => {
  const [, id, size, status, gate] = meta[key];
  return {
    protocol_profile_id: id, profile_status: status, source_lock_gate: gate,
    classification_authority: false,
    rows: Array.from({ length: size }, (_, i) => ({
      order: i + 1, canonical_measurement_id: key === 'com' ? comIds[i] : `M_TEST_${i + 1}_MM_V1`,
      label: `Source ${i + 1}`, unit: 'mm', source_contract: id,
      contract_state: 'PENDING_EQUIVALENCE', classification_authority: false,
      availability_status: 'NOT_COMPUTABLE', value: null,
    })),
  };
};
const payload = () => ({
  analysis_id: 9, revision: 2, authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED',
  reference_display_only: true, clinical_release: false,
  profiles: {
    com: profile('com'), mcnamara: profile('mcnamara'),
    ricketts_atlas2009: profile('atlas'), ricketts_gregoret13: profile('gregoret'),
  },
});

describe('R23-G4 experimental reference reader, fail-closed', () => {
  it.each([
    ['com', 'atlas', 10], ['mcnamara', 'atlas', 13],
    ['ricketts', 'atlas', 33], ['ricketts', 'gregoret', 13],
  ] as const)('%s %s has all %d source rows, with no fabricated numbers', (analysis, version, size) => {
    const data = payload();
    const result = readCephaloR23G2Protocol(data, analysis as R23G2Analysis, version);
    expect(result?.rows).toHaveLength(size);
    expect(result?.rows.every(row => row.availability_status === 'NOT_COMPUTABLE' && row.value === null)).toBe(true);
    expect(result?.classification_authority).toBe(false);
  });

  it('never accepts wrong study/revision, clinical release, or inferred provenance', () => {
    const data = payload();
    expect(isR23G4ReferenceBound(data, 7, 9, 2)).toBe(true);
    expect(isR23G4ReferenceBound(data, 7, 10, 2)).toBe(false);
    expect(isR23G4ReferenceBound(data, 7, 9, 1)).toBe(false);
    expect(isR23G4ReferenceBound(data, null, 9, 2)).toBe(false);
    expect(isR23G4ReferenceBound({ ...data, clinical_release: true }, 7, 9, 2)).toBe(false);
    expect(readCephaloR23G2Protocol({ ...data, active_chain: 'BROKEN' }, 'com')).toBeNull();
    expect(readCephaloR23G2Protocol({ ...data, clinical_release: true }, 'com')).toBeNull();
    data.profiles.com.rows[0].value = 9 as never;
    expect(readCephaloR23G2Protocol(data, 'com')).toBeNull();
  });

  it('denies an invalid Focus and admits only exact typed method and current evidence', () => {
    const data = payload();
    const row: any = data.profiles.com.rows[0];
    row.contract_state = 'SOURCE_LOCKED';
    row.availability_status = 'AVAILABLE';
    row.value = 4.7;
    row.measurement_refs = ['m:verified'];
    row.value_authority_method_id = 'M:EXACT';
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
    row.focus_evidence = {
      authority: 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1',
      canonical_measurement_id: row.canonical_measurement_id, measurement_ref: 'm:verified',
      value_authority_method_id: 'M:EXACT', landmark_ids: ['A', 'B'],
      construction_ids: [], calibration_required: false,
    };
    expect(readCephaloR23G2Protocol(data, 'com')).not.toBeNull();
    const focus = resolveR23G3RuntimeFocus(row);
    expect(focus?.points).toEqual(['A', 'B']);
    expect(focus?.lines).toEqual([]);
    expect(focus?.authority).toBe('ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1');
    row.focus_evidence.measurement_ref = 'm:wrong';
    expect(readCephaloR23G2Protocol(data, 'com')).toBeNull();
    expect(resolveR23G3RuntimeFocus(row)).toBeNull();
  });

  it('rejects duplicated source factor identifiers and absent complete source-lock', () => {
    const data = payload();
    data.profiles.ricketts_atlas2009.rows[1].canonical_measurement_id =
      data.profiles.ricketts_atlas2009.rows[0].canonical_measurement_id;
    expect(readCephaloR23G2Protocol(data, 'ricketts', 'atlas')).toBeNull();
    const second = payload();
    second.profiles.com.source_lock_gate = 'NOT_LOCKED' as never;
    expect(readCephaloR23G2Protocol(second, 'com')).toBeNull();
    const third = payload();
    third.profiles.com.rows[0].canonical_measurement_id = 'M_OVERJET_MM_V1';
    expect(readCephaloR23G2Protocol(third, 'com')).toBeNull();
  });
});
