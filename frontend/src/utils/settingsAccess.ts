import type { AppUser } from '../types';

type PermissionName = 'agenda' | 'settings' | 'admin';

const SECRETARY_LEGACY_DEFAULTS: Record<PermissionName, boolean> = {
  agenda: true,
  settings: false,
  admin: false,
};

const DENTIST_EMPLOYEE_LEGACY_DEFAULTS: Record<PermissionName, boolean> = {
  agenda: true,
  settings: false,
  admin: false,
};

export const hasFrontendPermission = (user: AppUser | null, permission: PermissionName): boolean => {
  if (!user) return false;
  if (user.is_superadmin) return true;

  const role = String(user.role || '').toUpperCase();
  if (role === 'ADMIN') return true;
  if (role === 'DENTISTE' && user.employer_id == null) return true;

  const permissions = user.permissions;
  if (permissions && Object.keys(permissions).length > 0) {
    return permissions[permission] === true;
  }

  if (role === 'SECRETAIRE') return SECRETARY_LEGACY_DEFAULTS[permission];
  if (role === 'DENTISTE' && user.employer_id != null) {
    return DENTIST_EMPLOYEE_LEGACY_DEFAULTS[permission];
  }

  return false;
};

export const getSettingsAccess = (user: AppUser | null) => {
  const canAgenda = hasFrontendPermission(user, 'agenda');
  const canSettings = hasFrontendPermission(user, 'settings');
  const canAdmin = hasFrontendPermission(user, 'admin');

  return {
    canAgenda,
    canSettings,
    canAdmin,
    canOpenSettingsCenter: canAgenda || canSettings || canAdmin,
  };
};
