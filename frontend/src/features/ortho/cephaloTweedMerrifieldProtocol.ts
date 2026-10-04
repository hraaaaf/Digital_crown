export interface TweedMerrifieldProtocolRow {
  canonical_measurement_id: string;
  label: string;
  profile_section: string;
  value: number | null;
  unit: string | null;
  availability_status: string;
  measurement_refs: string[];
  value_authority_method_id?: string | null;
  reference_authority: string;
  classification_authority: boolean;
  interpretation_status: string;
}

export interface TweedMerrifieldProtocolProjection {
  protocol_profile_id: string;
  source_lock_gate: { gate?: string; status?: string; scope?: string };
  final_gate: { gate?: string; status?: string };
  rows: TweedMerrifieldProtocolRow[];
  reference_contexts?: Array<Record<string, unknown>>;
  historical_geometry_resolution?: Record<string, unknown>;
  scope_resolutions?: Record<string, string>;
}

export const readTweedMerrifieldProtocolProjection = (
  anglesData: any,
): TweedMerrifieldProtocolProjection | null => {
  const scientific = anglesData?.scientific_read_path;
  if (scientific?.authority !== 'EVIDENCE_GRAPH_V1' || scientific?.active_chain !== 'VERIFIED') return null;
  const profile = scientific?.protocol_profiles?.tweed_merrifield;
  if (
    !profile ||
    profile.protocol_profile_id !== 'TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1' ||
    !Array.isArray(profile.rows)
  ) return null;
  return profile as TweedMerrifieldProtocolProjection;
};

export const tweedMerrifieldProtocolRow = (
  anglesData: any,
  canonicalId: string,
): TweedMerrifieldProtocolRow | null => {
  const profile = readTweedMerrifieldProtocolProjection(anglesData);
  return profile?.rows.find(row => row.canonical_measurement_id === canonicalId) ?? null;
};
