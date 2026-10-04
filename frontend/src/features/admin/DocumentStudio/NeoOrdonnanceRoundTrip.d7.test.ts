import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (file: string) => readFileSync(resolve(process.cwd(), file), 'utf8');
const generator = read('src/features/admin/DocumentStudio/useDocumentGenerator.ts');
const hub = read('src/features/admin/DocumentHub.tsx');

describe('D7 Neo ordonnance archive round-trip contract', () => {
  it('serializes practitioner safety and exact catalog identity into the archive payload', () => {
    for (const token of [
      'non_substituable: d.non_substituable ?? false',
      'catalog_presentation_id: d.catalogPresentationId ?? null',
      'catalog_dci: d.catalogDci ?? null',
      'catalog_source_id: d.catalogSourceId ?? null',
      'catalog_source_label: d.catalogSourceLabel ?? null',
      'catalog_snapshot_date: d.catalogSnapshotDate ?? null',
      'catalog_marketing_status_verified: d.catalogMarketingStatusVerified ?? null',
    ]) expect(generator).toContain(token);
  });

  it('rehydrates practitioner safety and exact catalog identity when an archive is reopened', () => {
    for (const token of [
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
