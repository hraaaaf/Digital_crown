import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { resolveNamedDevisActPrice } from './AccountingNamedActPricePolicy';

const source = readFileSync(
  resolve(process.cwd(), 'src/features/admin/AccountingStudioLegacy.tsx'),
  'utf8',
);
const selectorSource = readFileSync(
  resolve(process.cwd(), 'src/components/odontogram/TreatmentSelector.tsx'),
  'utf8',
);

describe('AccountingStudio P2-D wiring', () => {
  it('branche le remplacement idempotent par dent dans le sélecteur actif', () => {
    expect(source).toContain('replaceOdontogramToothSelections');
    expect(source).toContain('currentTreatments={activeToothTreatments}');
    expect(source).toContain('replaceToothTreatmentsFromSelector(activeTooth, treatments, surfaces)');
  });

  it('déclare activeTooth avant le memo qui le lit', () => {
    const stateIndex = source.indexOf('const [activeTooth, setActiveTooth]');
    const memoIndex = source.indexOf('const activeToothTreatments = React.useMemo');

    expect(stateIndex).toBeGreaterThanOrEqual(0);
    expect(memoIndex).toBeGreaterThan(stateIndex);
  });

  it('fail-close les prix nommés absents du catalogue et exige un prix groupé positif', () => {
    expect(source).not.toContain('const price = PriceBrain.suggestPrice(act) || 0;');
    expect(source).toContain('resolveNamedDevisActPrice');
    expect(source).toContain("resolved.source === 'UNRESOLVED'");
    expect(source).toContain('Tarif catalogue absent : renseignez le prix avant archivage.');
    expect(source).toContain('Renseignez un prix positif avant d’ajouter cet acte groupé.');

    expect(resolveNamedDevisActPrice('Acte connu', [
      { name: 'Acte connu', base_price: 450, category: 'CONSERVATRICE' },
    ])).toEqual({ price: 450, category: 'CONSERVATRICE', source: 'CATALOG' });
    expect(resolveNamedDevisActPrice('Acte absent', [])).toEqual({
      price: 0,
      category: undefined,
      source: 'UNRESOLVED',
    });
  });

  it('ne remplace pas un libellé de surface existant par défaut quand aucune surface n’est renvoyée', () => {
    expect(source).toContain("const dentLabel = surfaces.length > 0 ? toothNumber.toString() + ` (${surfaces.join('')})` : undefined;");
  });

  it('autorise une sélection vide uniquement pour vider une dent déjà renseignée', () => {
    expect(source).toContain('allowEmptyConfirm={activeToothTreatments.length > 0}');
    expect(selectorSource).toContain('allowEmptyConfirm?: boolean;');
    expect(selectorSource).toContain('allowEmptyConfirm = false');
    expect(selectorSource).toContain('disabled={selectedTreatments.length === 0 && !allowEmptyConfirm}');
  });
});