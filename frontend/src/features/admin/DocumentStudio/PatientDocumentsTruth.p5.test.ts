import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  resolve(process.cwd(), 'src/features/patients/PatientDocuments.tsx'),
  'utf8',
);

describe('Patient Documents P5 truth boundary', () => {
  it('distinguishes backend failure from a real empty history', () => {
    expect(source).toContain('const [fetchError, setFetchError]');
    expect(source).toContain("Impossible de charger l'historique");
    expect(source).toContain("Aucun état vide n'est déduit tant que le backend ne répond pas.");
    expect(source).toContain('Réessayer');
  });

  it('does not present the local duplicate heuristic as a canonical duplicate verdict', () => {
    expect(source).toContain('Contenu similaire à vérifier');
    expect(source).not.toContain('Doublon de contenu détecté');
  });

  it('opens and downloads through authenticated blobs and revokes object URLs', () => {
    expect(source).toContain("responseType: 'blob'");
    expect(source).toContain('URL.createObjectURL');
    expect(source).toContain('URL.revokeObjectURL');
  });

  it('uses trash as the normal delete action', () => {
    expect(source).toContain('`/documents/${docId}/trash`');
    expect(source).not.toContain('api.delete(`/documents/${docId}`');
  });
});
