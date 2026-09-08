import { MOBILE_BRIDGE_ROUTES } from './bridge';

const DESKTOP_TO_MOBILE_DESTINATION: Readonly<Record<string, keyof typeof MOBILE_BRIDGE_ROUTES>> = Object.freeze({
  '/dashboard': 'agenda',
  '/agenda': 'agenda',
  '/patients': 'patients',
  '/accounting': 'finance',
  '/stock': 'stock',
  '/approvisionnement': 'marketplace',
  '/bibliotheque': 'library',
  '/salle-attente': 'waiting-room',
  '/super-admin': 'superadmin',
});

export const KNOWN_MOBILE_PATHS = new Set([
  '/mobile/onboarding',
  '/mobile/dashboard',
  '/mobile/context',
  '/mobile/dentists',
  '/mobile/superadmin',
]);

export function isMobileRuntimeDevice(width: number, userAgent: string): boolean {
  return width <= 768 || /Mobi|Android|iPhone/i.test(userAgent);
}

export function resolveCanonicalMobileRoute(pathname: string): string | null {
  const destination = DESKTOP_TO_MOBILE_DESTINATION[pathname];
  return destination ? MOBILE_BRIDGE_ROUTES[destination] : null;
}

export function resolveMobileWildcardFallback(pathname: string): string | null {
  if (!pathname.startsWith('/mobile/')) return null;
  if (KNOWN_MOBILE_PATHS.has(pathname)) return null;
  return MOBILE_BRIDGE_ROUTES.agenda;
}
