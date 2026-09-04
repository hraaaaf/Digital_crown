import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

describe('MobilePatientsView patient isolation', () => {
  it('purges prior patient data before a new network load starts', () => {
    const source = readFileSync(
      join(process.cwd(), 'src/features/mobile/Dashboard/views/MobilePatientsView.tsx'),
      'utf8',
    );

    const marker = '// Fail closed between patient selections.';
    const markerIndex = source.indexOf(marker);
    const loadIndex = source.indexOf('let cancelled = false;', markerIndex);
    expect(markerIndex).toBeGreaterThan(-1);
    expect(loadIndex).toBeGreaterThan(markerIndex);

    const resetBlock = source.slice(markerIndex, loadIndex);
    expect(resetBlock).toContain('setCockpit(null);');
    expect(resetBlock).toContain('setResources({ documents: [], panoramics: [] });');
    expect(resetBlock).toContain('setOpeningContext(null);');
    expect(resetBlock).toContain("setError('');");
  });
});
