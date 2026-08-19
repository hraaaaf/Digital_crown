import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

interface DocumentStudioUser {
  role?: string | { value?: string } | null;
  employer_id?: number | null;
  permissions?: Record<string, boolean> | null;
}

const permissionForTab: Record<CertifiableDocumentStudioTab, string> = {
  ordonnance: 'prescriptions',
  certificat: 'patients',
  devis: 'accounting',
  honoraires: 'accounting',
  echeancier: 'accounting',
  libre: 'clinical',
};

const secretaryLegacyDefaults: Record<string, boolean> = {
  patients: true,
  prescriptions: false,
  accounting: false,
  clinical: false,
};

const dentistEmployeeLegacyDefaults: Record<string, boolean> = {
  patients: true,
  prescriptions: true,
  accounting: false,
  clinical: false,
};

const roleValue = (role: DocumentStudioUser['role']): string => {
  if (!role) return '';
  if (typeof role === 'string') return role;
  return role.value || '';
};

export const hasDocumentStudioPermission = (
  user: DocumentStudioUser | null | undefined,
  permission: string,
): boolean => {
  if (!user) return false;
  const role = roleValue(user.role);

  if (role === 'ADMIN') return true;
  if (role === 'DENTISTE' && !user.employer_id) return true;

  const permissions = user.permissions || {};
  if (Object.keys(permissions).length > 0) {
    return permissions[permission] === true;
  }

  if (role === 'SECRETAIRE') return secretaryLegacyDefaults[permission] === true;
  if (role === 'DENTISTE' && user.employer_id) {
    return dentistEmployeeLegacyDefaults[permission] === true;
  }
  return false;
};

export const allowedDocumentStudioTabs = (
  user: DocumentStudioUser | null | undefined,
): CertifiableDocumentStudioTab[] => {
  return (Object.keys(permissionForTab) as CertifiableDocumentStudioTab[])
    .filter(tab => hasDocumentStudioPermission(user, permissionForTab[tab]));
};
