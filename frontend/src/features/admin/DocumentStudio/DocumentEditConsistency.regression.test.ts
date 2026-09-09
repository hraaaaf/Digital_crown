import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patientDocuments = readFileSync(
  resolve(process.cwd(), 'src/features/patients/PatientDocuments.tsx'),
  'utf8',
);
const documentHub = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentHub.tsx'),
  'utf8',
);
const generator = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/useDocumentGenerator.ts'),
  'utf8',
);

describe('document edit consistency regression', () => {
  it('keeps the canonical archive id when editing an existing document', () => {
    expect(patientDocuments).toContain('setEditingDoc(doc)');
    expect(documentHub).toMatch(/editData\?\.id|editingArchiveId/);
    expect(generator).toContain('replace_archive_id');
  });

  it('keeps document actions as two explicit non-overlapping rows', () => {
    expect(patientDocuments).toContain('data-document-action="edit"');
    expect(patientDocuments).toContain('data-document-action="trash"');
    expect(patientDocuments).toMatch(/space-y-1|gap-1/);
  });
});
