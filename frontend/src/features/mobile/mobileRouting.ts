export const MOBILE_CANONICAL_ROUTE_MAP: Readonly<Record<string, string>> = Object.freeze({
  '/dashboard': '/mobile/dashboard?tab=agenda',
  '/agenda': '/mobile/dashboard?tab=agenda',
  '/patients': '/mobile/dashboard?tab=patients',
  '/accounting': '/mobile/dashboard?tab=finance',
  '/stock': '/mobile/dashboard?tab=stock',
  '/approvisionnement': '/mobile/dashboard?tab=marketplace',
  '/bibliotheque': '/mobile/dashboard?tab=library',
  '/salle-attente': '/mobile/dashboard?tab=waiting-room',
  '/super-admin': '/mobile/superadmin',
});

export function isMobileRuntimeDevice(width: number, userAgent: string): boolean {
  return width <= 768 || /Mobi|Android|iPhone/i.test(userAgent);
}

export function resolveCanonicalMobileRoute(pathname: string): string | null {
  return MOBILE_CANONICAL_ROUTE_MAP[pathname] ?? null;
}

export function resolveMobileWildcardFallback(pathname: string): string | null {
  if (!pathname.startsWith('/mobile/')) return null;
  if (pathname === '/mobile/onboarding') return null;
  return '/mobile/dashboard';
}
