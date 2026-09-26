import { describe, expect, it } from 'vitest';
import {
  DEFAULT_CATALOG_ACT_APPLICABILITY,
  normalizeCatalogActApplicability,
} from './useCatalogStore';

describe('catalog applicability normalization', () => {
  it('keeps legacy acts unrestricted and searchable by default', () => {
    expect(normalizeCatalogActApplicability(undefined)).toEqual(DEFAULT_CATALOG_ACT_APPLICABILITY);
  });

  it('clones array fields so editor mutations cannot leak between acts', () => {
    const source = { dentitions: ['PRIMARY'] as Array<'PRIMARY' | 'PERMANENT'> };
    const first = normalizeCatalogActApplicability(source);
    const second = normalizeCatalogActApplicability(source);
    first.dentitions.push('PERMANENT');
    expect(second.dentitions).toEqual(['PRIMARY']);
  });
});
