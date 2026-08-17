import { describe, expect, it } from 'vitest';
import { getSettingsAccess, hasFrontendPermission } from './settingsAccess';

const user = (overrides: Record<string, unknown>) => ({
  id: 1,
  email: 'user@example.com',
  aud: 'authenticated',
  app_metadata: {},
  user_metadata: {},
  created_at: '2026-01-01T00:00:00Z',
  ...overrides,
} as any);

describe('settingsAccess', () => {
  it('grants all settings capabilities to an ADMIN', () => {
    const access = getSettingsAccess(user({ role: 'ADMIN', permissions: {} }));
    expect(access).toEqual({
      canAgenda: true,
      canSettings: true,
      canAdmin: true,
      canOpenSettingsCenter: true,
    });
  });

  it('keeps legacy secretary limited to agenda', () => {
    const legacySecretary = user({ role: 'SECRETAIRE', permissions: {} });
    expect(hasFrontendPermission(legacySecretary, 'agenda')).toBe(true);
    expect(hasFrontendPermission(legacySecretary, 'settings')).toBe(false);
    expect(hasFrontendPermission(legacySecretary, 'admin')).toBe(false);
  });

  it('treats an explicit permission matrix as authoritative', () => {
    const explicitSecretary = user({
      role: 'SECRETAIRE',
      permissions: { agenda: false, settings: true, admin: false },
    });
    expect(hasFrontendPermission(explicitSecretary, 'agenda')).toBe(false);
    expect(hasFrontendPermission(explicitSecretary, 'settings')).toBe(true);
    expect(hasFrontendPermission(explicitSecretary, 'admin')).toBe(false);
  });

  it('grants root dentist all capabilities but not an employee dentist', () => {
    const owner = user({ role: 'DENTISTE', employer_id: null, permissions: {} });
    const employee = user({ role: 'DENTISTE', employer_id: 42, permissions: {} });

    expect(getSettingsAccess(owner).canAdmin).toBe(true);
    expect(getSettingsAccess(owner).canSettings).toBe(true);
    expect(getSettingsAccess(employee).canAgenda).toBe(true);
    expect(getSettingsAccess(employee).canSettings).toBe(false);
    expect(getSettingsAccess(employee).canAdmin).toBe(false);
  });

  it('fails closed when no user is available', () => {
    expect(getSettingsAccess(null).canOpenSettingsCenter).toBe(false);
  });
});
