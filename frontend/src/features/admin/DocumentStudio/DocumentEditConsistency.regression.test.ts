import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patientDocuments = readFileSync(
  resolve(process.cwd(), 'src/features/patients/PatientDocuments.tsx'),
  'utf8',
);
const patientStore = readFileSync(
  resolve(process.cwd(), 'src/stores/usePatientStore.ts'),
  'utf8',
);
const apiService = readFileSync(
  resolve(process.cwd(), 'src/services/api.ts'),
  'utf8',
);

describe('document edit consistency regression', () => {
  it('keeps the canonical archive id when editing an existing document', () => {
    expect(patientDocuments).toContain('setEditingDoc(doc)');
    expect(patientStore).toContain('DOCUMENT_EDIT_ARCHIVE_KEY');
    expect(patientStore).toContain('sessionStorage.setItem');
    expect(apiService).toContain('attachDocumentEditArchiveId');
    expect(apiService).toContain('_replace_archive_id');
  });

  it('keeps document actions as two explicit non-overlapping rows', () => {
    expect(patientDocuments).toContain('data-document-action="edit"');
    expect(patientDocuments).toContain('data-document-action="trash"');
    expect(patientDocuments).toMatch(/space-y-1|gap-1/);
  });
});
