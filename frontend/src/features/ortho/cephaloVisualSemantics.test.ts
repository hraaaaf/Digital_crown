import { describe, expect, it } from 'vitest';
import {
  CEPHALO_SCIENTIFIC_COLORS,
  cephaloGeometryColor,
  cephaloGeometryFamily,
  cephaloMetricColor,
  cephaloMetricFamily,
} from './cephaloVisualSemantics';

describe('Céphalo scientific color semantics', () => {
  it('keeps the five scientific families distinct', () => {
    expect(new Set(Object.values(CEPHALO_SCIENTIFIC_COLORS)).size).toBe(5);
  });

  it('maps skeletal metrics to the skeletal family', () => {
    for (const key of ['SNA', 'SNB', 'ANB', 'Angle_de_Tweed', 'Situation_A', 'Situation_B', 'Profondeur_Faciale', 'Co_A', 'Co_Gn', 'ANS_Me']) {
      expect(cephaloMetricFamily(key)).toBe('skeletal');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.skeletal);
    }
  });

  it('maps dental metrics to the dental family', () => {
    for (const key of ['IMPA', 'I_Francfort', 'Inter_Incisif', 'Surplomb', 'Recouvrement']) {
      expect(cephaloMetricFamily(key)).toBe('dental');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.dental);
    }
  });

  it('maps soft-tissue metrics to the soft-tissue family', () => {
    for (const key of ['Ligne_E_Ls', 'Ligne_E_Li']) {
      expect(cephaloMetricFamily(key)).toBe('soft_tissue');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.soft_tissue);
    }
  });

  it('keeps reference planes distinct from measured structures', () => {
    for (const key of ['fh', 'mp', 'sn', 'occ', 'mcnamara_perp']) {
      expect(cephaloGeometryFamily(key)).toBe('reference');
      expect(cephaloGeometryColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.reference);
    }
  });

  it('maps geometry to the same vocabulary used by the table', () => {
    expect(cephaloGeometryFamily('na')).toBe('skeletal');
    expect(cephaloGeometryFamily('nb')).toBe('skeletal');
    expect(cephaloGeometryFamily('u1')).toBe('dental');
    expect(cephaloGeometryFamily('l1')).toBe('dental');
    expect(cephaloGeometryFamily('eline')).toBe('soft_tissue');
  });

  it('fails safely to auxiliary for unknown presentation-only keys', () => {
    expect(cephaloMetricFamily('UNKNOWN_METRIC')).toBe('auxiliary');
    expect(cephaloGeometryFamily('unknown_geometry')).toBe('auxiliary');
  });
});
