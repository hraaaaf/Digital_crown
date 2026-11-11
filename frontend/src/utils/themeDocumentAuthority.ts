/**
 * The selected CSS theme is owned by documentElement.
 * Desktop Settings mirrors it onto body for legacy consumers.
 * Pocket applies a cabinet-scoped theme independently and must never receive
 * the desktop theme from the legacy localStorage key on app mount.
 * With no selected theme, :root is the authoritative Elite default.
 */
export function syncDesktopBodyThemeFromRoot(pathname: string): void {
  if (pathname === '/mobile' || pathname.startsWith('/mobile/')) return;

  document.body.dataset.theme = document.documentElement.dataset.theme || '';
}
