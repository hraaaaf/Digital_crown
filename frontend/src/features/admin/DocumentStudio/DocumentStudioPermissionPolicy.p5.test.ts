import { describe, expect, it } from 'vitest';
import { allowedDocumentStudioTabs, hasDocumentStudioPermission } from './DocumentStudioPermissionPolicy';

describe('P5 Document Studio permission policy', () => {
  it('allows every document tab for the cabinet owner and admin', () => {
    expect(allowedDocumentStudioTabs({ role: 'DENTISTE', employer_id: null, permissions: {} })).toEqual([
      'ordonnance', 'certificat', 'devis', 'honoraires', 'echeancier', 'libre',
    ]);
    expect(allowedDocumentStudioTabs({ role: 'ADMIN', employer_id: 10, permissions: {} })).toHaveLength(6);
  });

  it('mirrors backend legacy dentist employee defaults', () => {
    const user = { role: 'DENTISTE', employer_id: 10, permissions: {} };
    expect(allowedDocumentStudioTabs(user)).toEqual(['ordonnance', 'certificat']);
    expect(hasDocumentStudioPermission(user, 'accounting')).toBe(false);
    expect(hasDocumentStudioPermission(user, 'clinical')).toBe(false);
  });

  it('mirrors backend legacy secretary defaults', () => {
    const user = { role: 'SECRETAIRE', employer_id: 10, permissions: {} };
    expect(allowedDocumentStudioTabs(user)).toEqual(['certificat']);
  });

  it('treats a non-empty explicit matrix as authoritative', () => {
    const user = {
      role: 'DENTISTE',
      employer_id: 10,
      permissions: {
        patients: false,
        prescriptions: false,
        accounting: true,
        clinical: true,
      },
    };
    expect(allowedDocumentStudioTabs(user)).toEqual(['devis', 'honoraires', 'echeancier', 'libre']);
  });

  it('fails closed for unknown roles or no authenticated user', () => {
    expect(allowedDocumentStudioTabs(null)).toEqual([]);
    expect(allowedDocumentStudioTabs({ role: 'UNKNOWN', employer_id: 10, permissions: {} })).toEqual([]);
  });
});
