import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const profileSource = fs.readFileSync(
  path.join(root, 'src/features/admin/Settings/tabs/ProfileTab.tsx'),
  'utf8',
);
const storeSource = fs.readFileSync(
  path.join(root, 'src/features/admin/Settings/hooks/useSettingsStore.ts'),
  'utf8',
);

describe('Settings R2 Profile product truth', () => {
  it('keeps the personal Benmoussa preset behind superadmin state', () => {
    expect(profileSource).toContain('user?.is_superadmin');
    expect(profileSource).toContain('Modèle Benmoussa');
    expect(profileSource).toContain('Réinitialiser depuis le cabinet');
  });

  it('does not claim AI background removal or vectorization in the active profile UI', () => {
    expect(profileSource).not.toContain('Logo Premium (IA)');
    expect(profileSource).not.toContain('détourer le fond automatiquement');
    expect(profileSource).not.toContain('format vectoriel (SVG)');
    expect(storeSource).not.toContain('Détourage IA');
    expect(storeSource).not.toContain('Logo Premium généré');
  });

  it('keeps manual bilingual header editing as an explicit advanced surface', () => {
    expect(profileSource).toContain('Personnalisation avancée');
    expect(profileSource).toContain('aria-expanded={showHeaderAdvanced}');
    expect(profileSource).toContain("profile.header_customized ? 'Personnalisé' : 'Automatique'");
  });
});
