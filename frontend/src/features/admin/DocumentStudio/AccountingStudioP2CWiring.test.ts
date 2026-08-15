import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const sourcePath = fileURLToPath(new URL('../AccountingStudioLegacy.tsx', import.meta.url));
const source = readFileSync(sourcePath, 'utf8');

describe('AccountingStudio P2-C wiring', () => {
  it('branche les actes rapides explicites et le regroupement déterministe', () => {
    expect(source).toContain("AccountingQuickActions");
    expect(source).toContain("groupAccountingItemsByPhase");
    expect(source).toContain("Organiser par phases");
  });

  it('retire les libellés pseudo-IA et la durée clinique non sourcée du flux devis', () => {
    expect(source).not.toContain('Smart Acts');
    expect(source).not.toContain('Combo IA Détecté');
    expect(source).not.toContain("Séquencer avec l'IA");
    expect(source).not.toContain('DÉLAI DE CICATRISATION (ESTIMÉ : 3 MOIS)');
    expect(source).not.toContain('Ghost Treasury');
  });
});
