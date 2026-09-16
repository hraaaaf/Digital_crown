export type CephaloScientificFamily =
  | 'skeletal'
  | 'dental'
  | 'soft_tissue'
  | 'reference'
  | 'auxiliary';

/**
 * Global Céphalo scientific color contract.
 *
 * Scientific identity is carried by a stable base hue. The rendered color is
 * mixed with Digital Crown's existing --text-main token so contrast adapts to
 * light, dark, prestige and high-contrast themes without creating a parallel
 * Céphalo theme system. App surfaces, borders, shadows and interaction focus
 * remain fully owned by Digital Crown theme tokens.
 */
export const CEPHALO_SCIENTIFIC_BASE_HUES: Readonly<Record<CephaloScientificFamily, string>> = Object.freeze({
  skeletal: '#2563eb',
  dental: '#7c3aed',
  soft_tissue: '#059669',
  reference: '#d97706',
  auxiliary: '#64748b',
});

const adaptiveScientificColor = (baseHue: string): string =>
  `color-mix(in srgb, ${baseHue} 60%, var(--text-main) 40%)`;

export const CEPHALO_SCIENTIFIC_COLORS: Readonly<Record<CephaloScientificFamily, string>> = Object.freeze({
  skeletal: adaptiveScientificColor(CEPHALO_SCIENTIFIC_BASE_HUES.skeletal),
  dental: adaptiveScientificColor(CEPHALO_SCIENTIFIC_BASE_HUES.dental),
  soft_tissue: adaptiveScientificColor(CEPHALO_SCIENTIFIC_BASE_HUES.soft_tissue),
  reference: adaptiveScientificColor(CEPHALO_SCIENTIFIC_BASE_HUES.reference),
  auxiliary: adaptiveScientificColor(CEPHALO_SCIENTIFIC_BASE_HUES.auxiliary),
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
