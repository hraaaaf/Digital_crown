import type { AppUser } from '../types';

const SECRETARY_LEGACY_DEFAULTS: Readonly<Record<string, boolean>> = {
  agenda: true,
  patients: true,
  prescriptions: false,
  accounting: false,
  payments: false,
  panoramic: false,
  cephalo: false,
  settings: false,
  admin: false,
};

const DENTIST_EMPLOYEE_LEGACY_DEFAULTS: Readonly<Record<string, boolean>> = {
  agenda: true,
  patients: true,
  prescriptions: true,
  accounting: false,
  payments: false,
  panoramic: true,
  cephalo: true,
  settings: false,
  admin: false,
};

/**
 * Politique frontend canonique des permissions Digital Crown.
 *
 * Sécurité : cette fonction ne remplace jamais les contrôles backend. Elle sert
 * uniquement à empêcher le rendu et le chargement de données que l'interface
 * ne doit pas exposer.
 */
export const hasAccess = (
  user: AppUser | null | undefined,
  permission: string,
): boolean => {
  if (!user) return false;
  if (user.is_superadmin === true) return true;

  const role = user.role;
  if (role === 'ADMIN') return true;

  // Un profil dentiste partiel sans employer_id résolu n'est jamais assimilé
  // à un propriétaire : on attend une identité métier complète.
  if (role === 'DENTISTE' && user.employer_id === undefined) return false;
  if (role === 'DENTISTE' && user.employer_id === null) return true;

  const permissions = user.permissions;
  if (
    permissions &&
    typeof permissions === 'object' &&
    Object.keys(permissions).length > 0
  ) {
    return permissions[permission] === true;
  }

  if (role === 'SECRETAIRE') {
    return SECRETARY_LEGACY_DEFAULTS[permission] ?? false;
  }

  if (role === 'DENTISTE' && typeof user.employer_id === 'number') {
    return DENTIST_EMPLOYEE_LEGACY_DEFAULTS[permission] ?? false;
  }

  return false;
};
