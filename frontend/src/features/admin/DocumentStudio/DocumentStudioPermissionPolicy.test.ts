import { describe, expect, it } from 'vitest';
import { allowedDocumentStudioTabs } from './DocumentStudioPermissionPolicy';

describe('allowedDocumentStudioTabs', () => {
  it('gives the cabinet owner all six document-producing surfaces', () => {
    expect(allowedDocumentStudioTabs(undefined, undefined)).toEqual([
      'ordonnance', 'certificat', 'devis', 'honoraires', 'echeancier', 'libre',
    ]);
  });

  it('maps prescriptions permission only to ordonnance', () => {
    expect(allowedDocumentStudioTabs(1, { prescriptions: true })).toEqual(['ordonnance']);
  });

  it('maps patients permission only to certificat', () => {
    expect(allowedDocumentStudioTabs(1, { patients: true })).toEqual(['certificat']);
  });

  it('maps accounting permission to the three financial document surfaces', () => {
    expect(allowedDocumentStudioTabs(1, { accounting: true })).toEqual(['devis', 'honoraires', 'echeancier']);
  });

  it('maps clinical permission only to document libre', () => {
    expect(allowedDocumentStudioTabs(1, { clinical: true })).toEqual(['libre']);
  });

  it('does not expose a document surface to a sub-account without a matching permission', () => {
    expect(allowedDocumentStudioTabs(1, {})).toEqual([]);
  });
});
