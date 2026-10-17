/** R23-G2 read-only protocol rows. UI never calculates geometry or selects norms. */
export type R23G2Analysis = 'mcnamara' | 'com' | 'ricketts';
export type R23G2RickettsVersion = 'atlas' | 'gregoret';

export interface R23G2ProtocolRow {
  order: number;
  canonical_measurement_id: string;
  label: string;
  unit: string | null;
  contract_state: string;
  contract_gate?: string | null;
  availability_status: 'AVAILABLE' | 'MISSING' | 'INVALID' | 'NOT_APPLICABLE' | 'NOT_COMPUTABLE';
  value: number | null;
  measurement_refs?: string[];
  value_authority_method_id?: string | null;
  source_contract: string;
  classification_authority: false;
}

export interface R23G2Protocol {
  protocol_profile_id: string;
  profile_status: string;
  source_lock_gate: string;
  classification_authority: false;
  rows: R23G2ProtocolRow[];
}

const PROFILES = {
  mcnamara: ['mcnamara', 'MCNAMARA_1984_SINGLE_FILM_V1', 13, 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL'],
  com: ['com', 'COM_DC_LEGACY_V1', 10, 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL'],
  atlas: ['ricketts_atlas2009', 'RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1', 33, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL'],
  gregoret: ['ricketts_gregoret13', 'RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1', 13, 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED'],
} as const;

const AVAILABILITY = new Set(['AVAILABLE', 'MISSING', 'INVALID', 'NOT_APPLICABLE', 'NOT_COMPUTABLE']);

export function readCephaloR23G2Protocol(
  anglesData: any,
  analysis: R23G2Analysis,
  version: R23G2RickettsVersion = 'atlas',
): R23G2Protocol | null {
  const path = anglesData?.scientific_read_path;
  if (path?.authority !== 'EVIDENCE_GRAPH_V1' || path?.active_chain !== 'VERIFIED') return null;
  const key = analysis === 'ricketts' ? version : analysis;
  const [slot, protocolId, count, state] = PROFILES[key];
  const profile = path?.protocol_profiles?.[slot];
  if (!profile || profile.protocol_profile_id !== protocolId || profile.profile_status !== state
      || profile.classification_authority !== false || !Array.isArray(profile.rows)
      || profile.rows.length !== count) return null;
  if (analysis === 'ricketts' && profile.source_lock_gate !== 'COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED') return null;
  if (analysis !== 'ricketts' && profile.source_lock_gate !== 'HISTORICAL_WORKING_REFERENCE_ONLY') return null;
  const seen = new Set<string>();
  for (let index = 0; index < count; index++) {
    const row = profile.rows[index];
    if (!row || row.order !== index + 1 || typeof row.canonical_measurement_id !== 'string'
        || !row.canonical_measurement_id.startsWith('M_')
        || seen.has(row.canonical_measurement_id)
        || typeof row.contract_state !== 'string'
        || row.classification_authority !== false
        || row.source_contract !== protocolId
        || !AVAILABILITY.has(row.availability_status)) return null;
    seen.add(row.canonical_measurement_id);
    if (row.availability_status === 'AVAILABLE'
        && (!Number.isFinite(row.value) || !row.value_authority_method_id
            || !Array.isArray(row.measurement_refs) || row.measurement_refs.length === 0)) return null;
    if (row.availability_status !== 'AVAILABLE' && row.value !== null) return null;
  }
  return profile as R23G2Protocol;
}
