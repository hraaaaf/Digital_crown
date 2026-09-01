export interface ApiLocationLike {
  protocol: string;
  hostname: string;
}

/**
 * Résout l'origine API du cabinet sans autoriser une configuration HTTP de dev
 * à casser une page servie en HTTPS.
 *
 * En runtime HTTPS, une VITE_API_URL en http:// est volontairement ignorée :
 * le navigateur doit parler au même hôte sur :8005. C'est indispensable pour
 * le desktop local ET pour l'iPhone, où 127.0.0.1 désignerait l'iPhone lui-même.
 */
export function resolveApiBase(
  configuredUrl: string | undefined,
  currentLocation?: ApiLocationLike,
): string {
  const fallback = currentLocation
    ? `${currentLocation.protocol}//${currentLocation.hostname}:8005`
    : 'http://127.0.0.1:8005';

  const configured = configuredUrl?.trim().replace(/\/$/, '');
  if (!configured) return fallback;

  const isHttpsPage = currentLocation?.protocol === 'https:';
  const isInsecureOverride = configured.toLowerCase().startsWith('http://');
  if (isHttpsPage && isInsecureOverride) return fallback;

  return configured;
}
