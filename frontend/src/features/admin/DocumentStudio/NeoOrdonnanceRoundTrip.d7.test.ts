import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (file: string) => readFileSync(resolve(process.cwd(), file), 'utf8');
const generator = read('src/features/admin/DocumentStudio/useDocumentGenerator.ts');
const hub = read('src/features/admin/DocumentHub.tsx');

describe('Neo D7 archive mapping regression contract', () => {
  it('includes quantity, NS and provenance in the saved prescription', () => {
    for (const token of [
      'quantite_explicit: Boolean(d.quantiteExplicit)',
      'non_substituable: d.non_substituable ?? false',
      'catalog_presentation_id: d.catalogPresentationId ?? null',
      'catalog_dci: d.catalogDci ?? null',
      'catalog_source_id: d.catalogSourceId ?? null',
      'catalog_source_label: d.catalogSourceLabel ?? null',
      'catalog_snapshot_date: d.catalogSnapshotDate ?? null',
      'catalog_marketing_status_verified: d.catalogMarketingStatusVerified ?? null',
    ]) expect(generator).toContain(token);
  });
  it('restores practitioner NS and exact catalogue identity', () => {
    for (const token of [
      'quantiteExplicit: Boolean(m.quantite_explicit)',
      'non_substituable: Boolean(m.non_substituable)',
      'catalogPresentationId: m.catalog_presentation_id || undefined',
      'catalogDci: m.catalog_dci || undefined',
      'catalogSourceId: m.catalog_source_id || undefined',
      'catalogSourceLabel: m.catalog_source_label || undefined',
      'catalogSnapshotDate: m.catalog_snapshot_date || undefined',
      "catalogMarketingStatusVerified: typeof m.catalog_marketing_status_verified === 'boolean'",
    ]) expect(hub).toContain(token);
  });
});
