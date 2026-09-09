import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const patientDocuments = readFileSync(
  resolve(process.cwd(), 'src/features/patients/PatientDocuments.tsx'),
  'utf8',
);
const patientDetails = readFileSync(
  resolve(process.cwd(), 'src/features/patients/PatientDetailsInner.tsx'),
  'utf8',
);
const patientStore = readFileSync(
  resolve(process.cwd(), 'src/stores/usePatientStore.ts'),
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
const apiService = readFileSync(
  resolve(process.cwd(), 'src/services/api.ts'),
  'utf8',
);

describe('document edit consistency regression', () => {
  it('passes the canonical archive id explicitly from edit state to the generated payload', () => {
    expect(patientDocuments).toContain('setEditingDoc(doc)');
    expect(documentHub).toContain('editArchiveId: editData?.id');
    expect(generator).toContain('_replace_archive_id: params.editArchiveId');
    expect(generator).toContain("digitalcrown:document-edit-complete");
    expect(apiService).not.toContain('attachDocumentEditArchiveId');
    expect(apiService).not.toContain('DOCUMENT_EDIT_ARCHIVE_KEY');
    expect(patientStore).not.toContain('sessionStorage.setItem');
  });

  it('hydrates the complete honoraires financial state before regeneration', () => {
    expect(patientDocuments).toContain('payment_status?: string');
    expect(patientDocuments).toContain('is_accounted?: boolean');
    expect(documentHub).toContain("const paymentState = editData.payment_status === 'PAYE' ? 'PAYE' : 'EN_ATTENTE'");
    expect(documentHub).toContain('setIsAccounted(editData.is_accounted ?? true)');
    expect(documentHub).toContain('setIsGlobalNote(Boolean(d.is_global_note))');
    expect(documentHub).toContain('setInstallments((d.installments || []).map');
    expect(documentHub).toContain('sendReminder: Boolean(inst.sendReminder)');
    expect(documentHub).toContain('setPaymentMode(paymentState === \'PAYE\'');
  });

  it('clears edit state before every explicit new-document entry point', () => {
    expect(patientDetails).toContain('const handleDocumentCreate = () => {');
    expect(patientDetails).toMatch(/handleDocumentCreate[\s\S]*setEditingDoc\(null\)[\s\S]*setSearchParams\(\{ tab: 'admin' \}\)/);
    expect(patientDetails).toContain('label="Document" onClick={handleDocumentCreate}');
    expect(patientDetails).toContain('label="Documents"');
    expect(patientDetails).toContain('<button onClick={handleDocumentCreate}');
  });

  it('keeps document actions as two explicit non-overlapping rows', () => {
    expect(patientDocuments).toContain('data-document-action="edit"');
    expect(patientDocuments).toContain('data-document-action="trash"');
    expect(patientDocuments).toMatch(/space-y-1|gap-1/);
  });
});
