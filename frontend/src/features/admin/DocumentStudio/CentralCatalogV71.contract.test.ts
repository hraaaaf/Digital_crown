import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const selector = readFileSync(
  resolve(process.cwd(), 'src/components/odontogram/TreatmentSelector.tsx'),
  'utf8',
);
const generator = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/useDocumentGenerator.ts'),
  'utf8',
);

describe('V7.1 central catalog UX contract', () => {
  it('exposes personal favorites, recents and contextual suggestions', () => {
    expect(selector).toContain("setActiveCategory('FAVORITES')");
    expect(selector).toContain("setActiveCategory('RECENT')");
    expect(selector).toContain("setActiveCategory('SUGGESTED')");
    expect(selector).toContain('setActFavorite');
    expect(selector).toContain('act.last_used_at');
  });

  it('requires a specialty before creating an inline act', () => {
    expect(selector).toContain('Spécialité du nouvel acte');
    expect(selector).toContain('!newActSpecialtyId');
    expect(selector).not.toContain('category: \'CONSERVATRICE\', scope: \'UNITAIRE\'');
  });

  it('sends specialty/category to financial archive learning without mixing catalog id namespaces', () => {
    expect(generator).toContain('category: i.category');
    expect(generator).not.toContain('catalog_act_id: i.catalogActId');
  });
});
