import { describe, expect, it } from 'vitest';
import type { AppUser } from '../types';
import { hasAccess } from './accessControl';

const user = (overrides: Partial<AppUser>): AppUser => overrides as AppUser;

describe('hasAccess — matrice canonique D1', () => {
  it('refuse tant que l’utilisateur n’est pas résolu', () => {
    expect(hasAccess(null, 'patients')).toBe(false);
    expect(hasAccess(undefined, 'accounting')).toBe(false);
  });

  it('autorise ADMIN et superadmin', () => {
    expect(hasAccess(user({ role: 'ADMIN' }), 'accounting')).toBe(true);
    expect(hasAccess(user({ role: 'SECRETAIRE', is_superadmin: true }), 'admin')).toBe(true);
  });

  it('autorise le dentiste propriétaire sur toutes les permissions', () => {
    const owner = user({ role: 'DENTISTE', employer_id: null });
    expect(hasAccess(owner, 'patients')).toBe(true);
    expect(hasAccess(owner, 'accounting')).toBe(true);
    expect(hasAccess(owner, 'admin')).toBe(true);
  });

  it('refuse un profil dentiste incomplet dont employer_id n’est pas résolu', () => {
    const partialDentist = user({ role: 'DENTISTE' });
    expect(hasAccess(partialDentist, 'patients')).toBe(false);
    expect(hasAccess(partialDentist, 'accounting')).toBe(false);
  });

  it('donne au dentiste salarié legacy le clinique mais pas la finance/admin', () => {
    const employee = user({ role: 'DENTISTE', employer_id: 10, permissions: {} });
    expect(hasAccess(employee, 'patients')).toBe(true);
    expect(hasAccess(employee, 'agenda')).toBe(true);
    expect(hasAccess(employee, 'prescriptions')).toBe(true);
    expect(hasAccess(employee, 'panoramic')).toBe(true);
    expect(hasAccess(employee, 'cephalo')).toBe(true);
    expect(hasAccess(employee, 'accounting')).toBe(false);
    expect(hasAccess(employee, 'payments')).toBe(false);
    expect(hasAccess(employee, 'settings')).toBe(false);
    expect(hasAccess(employee, 'admin')).toBe(false);
  });

  it('donne à la secrétaire legacy patients + agenda uniquement', () => {
    const secretary = user({ role: 'SECRETAIRE', employer_id: 10, permissions: {} });
    expect(hasAccess(secretary, 'patients')).toBe(true);
    expect(hasAccess(secretary, 'agenda')).toBe(true);
    expect(hasAccess(secretary, 'prescriptions')).toBe(false);
    expect(hasAccess(secretary, 'accounting')).toBe(false);
    expect(hasAccess(secretary, 'payments')).toBe(false);
    expect(hasAccess(secretary, 'admin')).toBe(false);
  });

  it('fait primer toute matrice explicite non vide sur les fallbacks legacy', () => {
    const explicitDentist = user({
      role: 'DENTISTE',
      employer_id: 10,
      permissions: { patients: false, accounting: true },
    });
    expect(hasAccess(explicitDentist, 'patients')).toBe(false);
    expect(hasAccess(explicitDentist, 'accounting')).toBe(true);
    expect(hasAccess(explicitDentist, 'agenda')).toBe(false);
  });

  it('refuse les rôles inconnus', () => {
    const unknown = user({ role: 'UNKNOWN', employer_id: 10, permissions: {} });
    expect(hasAccess(unknown, 'patients')).toBe(false);
    expect(hasAccess(unknown, 'accounting')).toBe(false);
  });
});
