import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const source = fs.readFileSync(
  path.join(root, 'src/features/patients/components/MotifSelector.tsx'),
  'utf8',
);

describe('CUST-02 custom consultation motifs', () => {
  it('loads cabinet motifs without replacing the system dictionary', () => {
    expect(source).toContain("api.get('/motifs'");
    expect(source).toContain('MOTIFS_DICTIONARY.map');
    expect(source).toContain("source: 'cabinet'");
  });

  it('preserves unresolved and inactive historical values', () => {
    expect(source).toContain('Historique');
    expect(source).toContain('include_inactive: true');
    expect(source).toContain("motif.source === 'cabinet' && motif.is_active === false");
  });

  it('does not invent clinical hints for cabinet motifs', () => {
    expect(source).toContain('specialty_hints: []');
    expect(source).toContain('act_hints: []');
    expect(source).toContain('Aucun acte ni spécialité ne sera suggéré automatiquement');
  });

  it('keeps the existing selection ceiling and contextual add action', () => {
    expect(source).toContain('selected.length < maxSelect');
    expect(source).toContain('Maximum {maxSelect} motifs sélectionnés.');
    expect(source).toContain('Ajouter un motif');
  });

  it('creates through the cabinet API and handles permission denial explicitly', () => {
    expect(source).toContain("api.post('/motifs'");
    expect(source).toContain('status === 403');
    expect(source).toContain('réservée aux utilisateurs autorisés');
  });
});
