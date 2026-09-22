import { describe, expect, it } from 'vitest';
import { getHonoraireTrashTarget } from './utils';

describe('getHonoraireTrashTarget', () => {
  it('targets the parent archive for a derived Acte row', () => {
    expect(getHonoraireTrashTarget({
      id: 'acte_42',
      document_archive_id: 7,
    })).toBe(7);
  });

  it('falls back to the row id for a standalone Acte', () => {
    expect(getHonoraireTrashTarget({
      id: 'acte_42',
      document_archive_id: null,
    })).toBe('acte_42');
  });

  it('keeps a legacy document row target when no explicit archive id exists', () => {
    expect(getHonoraireTrashTarget({
      id: 'doc_9',
    })).toBe('doc_9');
  });
});
