import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const tabSource = fs.readFileSync(
  path.join(root, 'src/features/admin/Settings/tabs/CatalogTab.tsx'),
  'utf8',
);
const storeSource = fs.readFileSync(
  path.join(root, 'src/features/admin/Settings/hooks/useCatalogStore.ts'),
  'utf8',
);

describe('Settings R6 Catalog safe CRUD', () => {
  it('removes browser prompt CRUD from the Catalog surface', () => {
    expect(tabSource).not.toContain('prompt(');
    expect(tabSource).not.toContain('window.prompt');
    expect(tabSource).toContain('role="dialog"');
  });

  it('supports complete act editing and explicit active state', () => {
    expect(tabSource).toContain("base_price: parsedPrice");
    expect(tabSource).toContain('is_active: isActive');
    expect(tabSource).toContain('<StatusBadge active={act.is_active} />');
    expect(storeSource).toContain('color?: string; is_active?: boolean');
  });

  it('supports pathology editing through the existing backend route', () => {
    expect(storeSource).toContain('updatePathology:');
    expect(storeSource).toContain('`/catalog/pathologies/${pathologyId}`');
    expect(tabSource).toContain('await updatePathology(modal.pathology.id, payload)');
  });

  it('does not invent destructive Catalog deletion', () => {
    expect(tabSource).not.toContain('Supprimer');
    expect(storeSource).not.toContain('api.delete');
  });

  it('keeps failed mutations observable instead of closing optimistically', () => {
    expect(storeSource).toContain('Promise<boolean>');
    expect(tabSource).toContain('if (ok) onClose();');
    expect(tabSource).toContain("setFormError('Le tarif doit être un nombre positif ou nul.')");
  });
});
