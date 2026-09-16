export type CephaloScientificFamily =
  | 'skeletal'
  | 'dental'
  | 'soft_tissue'
  | 'reference'
  | 'auxiliary';

/**
 * Global Céphalo scientific color contract.
 *
 * These colors encode scientific meaning only. App surfaces, text, borders,
 * shadows and interaction focus remain owned by Digital Crown theme tokens.
 * The hues stay stable across app themes so the same scientific family never
 * changes identity when the user changes the application theme.
 */
export const CEPHALO_SCIENTIFIC_COLORS: Readonly<Record<CephaloScientificFamily, string>> = Object.freeze({
  skeletal: '#2563eb',
  dental: '#7c3aed',
  soft_tissue: '#059669',
  reference: '#d97706',
  auxiliary: '#64748b',
});

const METRIC_FAMILY: Readonly<Record<string, CephaloScientificFamily>> = Object.freeze({
  SNA: 'skeletal',
  SNB: 'skeletal',
  ANB: 'skeletal',
  Angle_de_Tweed: 'skeletal',
  Decalage_A_B: 'skeletal',
  Situation_A: 'skeletal',
  Situation_B: 'skeletal',
  Profondeur_Faciale: 'skeletal',
  Co_A: 'skeletal',
  Co_Gn: 'skeletal',
  ANS_Me: 'skeletal',
  IMPA: 'dental',
  I_Francfort: 'dental',
  Inter_Incisif: 'dental',
  Surplomb: 'dental',
  Recouvrement: 'dental',
  Ligne_E_Ls: 'soft_tissue',
  Ligne_E_Li: 'soft_tissue',
});

const GEOMETRY_FAMILY: Readonly<Record<string, CephaloScientificFamily>> = Object.freeze({
  fh: 'reference',
  mp: 'reference',
  sn: 'reference',
  occ: 'reference',
  mcnamara_perp: 'reference',
  na: 'skeletal',
  nb: 'skeletal',
  ab: 'skeletal',
  coa: 'skeletal',
  cogn: 'skeletal',
  ansme: 'skeletal',
  situation_a: 'skeletal',
  situation_b: 'skeletal',
  facial_depth: 'skeletal',
  a_prime: 'skeletal',
  b_prime: 'skeletal',
  ab_prime: 'skeletal',
  npog: 'skeletal',
  convexity: 'skeletal',
  u1: 'dental',
  l1: 'dental',
  inter_incisif: 'dental',
  overjet: 'dental',
  overbite: 'dental',
  eline: 'soft_tissue',
  soft_profile: 'soft_tissue',
});

export const cephaloMetricFamily = (metricKey: string): CephaloScientificFamily =>
  METRIC_FAMILY[metricKey] ?? 'auxiliary';

export const cephaloMetricColor = (metricKey: string): string =>
  CEPHALO_SCIENTIFIC_COLORS[cephaloMetricFamily(metricKey)];

export const cephaloGeometryFamily = (geometryKey: string): CephaloScientificFamily =>
  GEOMETRY_FAMILY[geometryKey] ?? 'auxiliary';

export const cephaloGeometryColor = (geometryKey: string): string =>
  CEPHALO_SCIENTIFIC_COLORS[cephaloGeometryFamily(geometryKey)];
