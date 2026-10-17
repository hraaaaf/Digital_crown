import { describe, expect, it } from 'vitest';
import { readCephaloR23G2Protocol, type R23G2Analysis } from './cephaloR23G2ClinicalProfiles';

const ids = (n: number) => Array.from({ length: n }, (_, i) => ({
  order: i + 1,
  canonical_measurement_id: `M_TEST_${i + 1}_MM_V1`,
  label: `Facteur ${i + 1}`,
  value: null,
  unit: 'mm',
  availability_status: 'NOT_COMPUTABLE',
  contract_state: 'CONDITIONAL_EXECUTABLE',
  source_contract: 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1',
  classification_authority: false,
}));
const atlas = { protocol_profile_id: 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1', profile_status: 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL', rows: ids(33) };
const data = (profile = atlas) => ({ scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1', active_chain: 'VERIFIED', protocol_profiles: { ricketts_atlas2009: profile } } });

describe('R23-G2 fail-closed clinical presentation', () => {
  it('shows all 33 rows instead of the previous two-line panel', () => {
    expect(readCephaloR23G2Protocol(data(), 'ricketts', 'atlas')?.rows).toHaveLength(33);
  });
  it('fails closed when the active chain is not verified', () => {
    expect(readCephaloR23G2Protocol({ scientific_read_path: { ...data().scientific_read_path, active_chain: 'STALE' } }, 'ricketts', 'atlas')).toBeNull();
  });
  it('refuses truncated, duplicated and clinically classified profile rows', () => {
    expect(readCephaloR23G2Protocol(data({ ...atlas, rows: ids(2) }), 'ricketts', 'atlas')).toBeNull();
    expect(readCephaloR23G2Protocol(data({ ...atlas, rows: [...ids(32), ids(1)[0]] }), 'ricketts', 'atlas')).toBeNull();
    expect(readCephaloR23G2Protocol(data({ ...atlas, rows: [...ids(32), { ...ids(33)[32], classification_authority: true }] }), 'ricketts', 'atlas')).toBeNull();
  });
  it('never promotes an AVAILABLE row without verified provenance', () => {
    const rows = ids(33);
    rows[0] = { ...rows[0], availability_status: 'AVAILABLE', value: 3.1 } as typeof rows[number];
    expect(readCephaloR23G2Protocol(data({ ...atlas, rows }), 'ricketts', 'atlas')).toBeNull();
  });
  it('requires exact profile identities for every mode', () => {
    for (const mode of ['mcnamara', 'com'] as R23G2Analysis[]) {
      expect(readCephaloR23G2Protocol(data(), mode, 'atlas')).toBeNull();
    }
  });
});
