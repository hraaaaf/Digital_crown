import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

// Regression contract for the actual DrugRow rendered to clinicians.
// The separate Chromium visual gate certifies the live data/text/behavior.
const drugRow = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx'),
  'utf8',
);

describe('LOT07 R2 per-presentation catalog provenance regression', () => {
  it('renders each source and its own snapshot date on the suggestion, not only an HTML data attribute', () => {
    expect(drugRow).toContain('data-catalog-provenance');
    expect(drugRow).toContain('{catalogSourceShortLabel(presentation.source)}');
    expect(drugRow).toContain("presentation.source.snapshot_date || 'date non renseignée'");
    expect(drugRow).toContain("source.id.startsWith('ammps-')");
    expect(drugRow).toContain("source.id === 'cnops-open-data-medications'");
  });

  it('never certifies marketing availability simply because a documentary catalog has a match', () => {
    expect(drugRow).toContain('presentation.source.current_marketing_status_verified');
    expect(drugRow).toContain("'non certifié'");
    expect(drugRow).toContain('data-presentation-id={presentation.presentation_id}');
    expect(drugRow).toContain('selectPresentation(presentation)');
    expect(drugRow).toContain('onMouseDown={event => {');
  });
});
