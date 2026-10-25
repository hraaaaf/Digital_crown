import { describe, expect, it } from 'vitest';
import { allowedDocumentStudioTabs, hasDocumentStudioPermission } from './DocumentStudioPermissionPolicy';

describe('LOT07 R2 real document tab fail-closed RBAC contracts', () => {
  it('allows the explicit authorized employee to use only their two permitted editor families', () => {
    const clinician={role:'DENTISTE',employer_id:31,permissions:{
      patients:true,prescriptions:true,accounting:false,clinical:false,
    }};
    expect(allowedDocumentStudioTabs(clinician)).toEqual(['ordonnance','certificat']);
    expect(hasDocumentStudioPermission(clinician,'accounting')).toBe(false);
  });

  it('does not allow an accounting-disabled secretary to mount Honoraires or Prescription', () => {
    const secretary={role:'SECRETAIRE',employer_id:31,permissions:{
      patients:true,prescriptions:false,accounting:false,clinical:false,
    }};
    expect(allowedDocumentStudioTabs(secretary)).toEqual(['certificat']);
    expect(hasDocumentStudioPermission(secretary,'accounting')).toBe(false);
    expect(hasDocumentStudioPermission(secretary,'prescriptions')).toBe(false);
  });

  it('denies missing, unknown and explicitly revoked permissions for non-owners', () => {
    expect(allowedDocumentStudioTabs(null)).toEqual([]);
    expect(allowedDocumentStudioTabs({role:'UNKNOWN',employer_id:31})).toEqual([]);
    const staff={role:'DENTISTE',employer_id:31,permissions:{
      patients:false,prescriptions:false,accounting:false,clinical:false,
    }};
    expect(allowedDocumentStudioTabs(staff)).toEqual([]);
  });

  it('keeps the existing owner and admin exceptions separate from a new W/X grant', () => {
    for(const actor of [{role:'ADMIN'}, {role:'DENTISTE',employer_id:null}]) {
      expect(allowedDocumentStudioTabs(actor)).toEqual([
        'ordonnance','certificat','devis','honoraires','echeancier','libre',
      ]);
    }
    // These visibility permissions DO NOT themselves certify W or X in MultiView.
    expect(hasDocumentStudioPermission({role:'SECRETAIRE',employer_id:11},'accounting')).toBe(false);
  });
});
