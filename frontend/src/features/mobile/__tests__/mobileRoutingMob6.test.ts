import { describe, expect, it } from 'vitest';
import { MOBILE_BRIDGE_ROUTES } from '../bridge';
import {
  isMobileRuntimeDevice,
  resolveCanonicalMobileRoute,
  resolveMobileWildcardFallback,
} from '../mobileRouting';

describe('MOB-6 canonical mobile routing', () => {
  it('maps only top-level desktop routes with proven mobile equivalents', () => {
    expect(resolveCanonicalMobileRoute('/agenda')).toBe(MOBILE_BRIDGE_ROUTES.agenda);
    expect(resolveCanonicalMobileRoute('/patients')).toBe(MOBILE_BRIDGE_ROUTES.patients);
    expect(resolveCanonicalMobileRoute('/accounting')).toBe(MOBILE_BRIDGE_ROUTES.finance);
    expect(resolveCanonicalMobileRoute('/stock')).toBe(MOBILE_BRIDGE_ROUTES.stock);
    expect(resolveCanonicalMobileRoute('/approvisionnement')).toBe(MOBILE_BRIDGE_ROUTES.marketplace);
    expect(resolveCanonicalMobileRoute('/bibliotheque')).toBe(MOBILE_BRIDGE_ROUTES.library);
    expect(resolveCanonicalMobileRoute('/salle-attente')).toBe(MOBILE_BRIDGE_ROUTES['waiting-room']);
    expect(resolveCanonicalMobileRoute('/super-admin')).toBe(MOBILE_BRIDGE_ROUTES.superadmin);
  });

  it('does not destroy rich desktop deep-link context', () => {
    expect(resolveCanonicalMobileRoute('/patients/42')).toBeNull();
    expect(resolveCanonicalMobileRoute('/patients/42/edit')).toBeNull();
    expect(resolveCanonicalMobileRoute('/bibliotheque/PERIO-001')).toBeNull();
    expect(resolveCanonicalMobileRoute('/approvisionnement/partenaire/7')).toBeNull();
    expect(resolveCanonicalMobileRoute('/approvisionnement/produits/9')).toBeNull();
  });

  it('keeps known mobile routes and normalizes unknown mobile paths through the canonical bridge', () => {
    expect(resolveMobileWildcardFallback('/mobile/dashboard')).toBeNull();
    expect(resolveMobileWildcardFallback('/mobile/context')).toBeNull();
    expect(resolveMobileWildcardFallback('/mobile/dentists')).toBeNull();
    expect(resolveMobileWildcardFallback('/mobile/superadmin')).toBeNull();
    expect(resolveMobileWildcardFallback('/mobile/onboarding')).toBeNull();
    expect(resolveMobileWildcardFallback('/mobile/does-not-exist')).toBe(MOBILE_BRIDGE_ROUTES.agenda);
  });

  it('uses the same device rule for viewport and mobile user agents', () => {
    expect(isMobileRuntimeDevice(390, 'Desktop UA')).toBe(true);
    expect(isMobileRuntimeDevice(768, 'Desktop UA')).toBe(true);
    expect(isMobileRuntimeDevice(1280, 'Mozilla/5.0 iPhone')).toBe(true);
    expect(isMobileRuntimeDevice(1280, 'Desktop UA')).toBe(false);
  });
});
