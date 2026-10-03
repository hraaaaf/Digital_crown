export type SteinerProtocolLayer = 'STEINER_1953_BASE' | 'STEINER_1959_EXTENSION';

export interface SteinerProtocolRow {
  canonical_measurement_id: string;
  label: string;
  layer: SteinerProtocolLayer;
  value: number | null;
  unit: string | null;
  availability_status: string;
  measurement_refs: string[];
  value_authority_method_id?: string | null;
  historical_reference: number | null;
  reference_delta: number | null;
  reference_authority: string;
  classification_authority: boolean;
  interpretation_status: string;
}

export interface SteinerProtocolProjection {
  protocol_profile_id: string;
  source_lock_gate: { gate?: string; status?: string; scope?: string };
  final_gate: { gate?: string; status?: string };
  norm_set: {
    norm_set_id?: string;
    authority?: string;
    population?: string;
    applicability?: string;
    out_of_domain_behavior?: string;
  };
  rows: SteinerProtocolRow[];
  required_manual_identities?: Record<string, string>;
}

export const STEINER_EXPLICIT_IDENTITIES = [
  { id: 'Gn_anatomic', label: 'Gn anatomique', help: 'Gnathion anatomique explicite' },
  { id: 'U1_facial_surface', label: 'U1 surface faciale', help: 'Point coronaire facial maxillaire' },
  { id: 'L1_facial_surface', label: 'L1 surface faciale', help: 'Point coronaire facial mandibulaire' },
  { id: 'D_Steiner_1959', label: 'Point D Steiner', help: 'Point D explicite ? aucun alias D_point' },
  { id: 'Occ_Steiner_Ant', label: 'Occlusal ant?rieur', help: 'Ancrage ant?rieur du plan occlusal Steiner' },
  { id: 'Occ_Steiner_Post', label: 'Occlusal post?rieur', help: 'Ancrage post?rieur du plan occlusal Steiner' },
] as const;

export const STEINER_EXPLICIT_ID_SET = new Set<string>(STEINER_EXPLICIT_IDENTITIES.map(item => item.id));

export const readSteinerProtocolProjection = (anglesData: any): SteinerProtocolProjection | null => {
  const scientific = anglesData?.scientific_read_path;
  if (scientific?.authority !== 'EVIDENCE_GRAPH_V1' || scientific?.active_chain !== 'VERIFIED') return null;
  const profile = scientific?.protocol_profiles?.steiner;
  if (!profile || profile.protocol_profile_id !== 'STEINER_STATIC_PROTOCOL_PROFILE_V1' || !Array.isArray(profile.rows)) return null;
  return profile as SteinerProtocolProjection;
};

export const steinerProtocolRow = (anglesData: any, canonicalId: string): SteinerProtocolRow | null => {
  const profile = readSteinerProtocolProjection(anglesData);
  return profile?.rows.find(row => row.canonical_measurement_id === canonicalId) ?? null;
};

export const steinerAvailabilityLabel = (status?: string | null) => {
  switch ((status || '').toUpperCase()) {
    case 'AVAILABLE': return 'Calcul?e';
    case 'INVALID': return 'Invalide';
    case 'NOT_APPLICABLE': return 'Non applicable';
    case 'MISSING': return 'Donn?e manquante';
    default: return 'Non calculable';
  }
};
