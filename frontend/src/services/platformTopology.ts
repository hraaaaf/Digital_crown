const viteEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;

const trimTrailingSlash = (value: string): string => value.replace(/\/$/, '');

export const PLATFORM_APP_URL = trimTrailingSlash(viteEnv?.VITE_PLATFORM_APP_URL ?? '');

export type PlatformTopology = {
  ready: boolean;
  currentOrigin: string;
  platformApiOrigin: string;
  platformAppOrigin: string;
  controlUrl: string;
};

function safeUrl(value: string, fallback: string): URL | null {
  try {
    return new URL(value || fallback, fallback);
  } catch {
    return null;
  }
}

function secureOrLocal(url: URL | null): boolean {
  if (!url) return false;
  return url.protocol === 'https:' || url.hostname === 'localhost' || url.hostname === '127.0.0.1';
}

export function getPlatformTopology(platformApiBase: string): PlatformTopology {
  if (typeof window === 'undefined') {
    return {
      ready: true,
      currentOrigin: '',
      platformApiOrigin: '',
      platformAppOrigin: '',
      controlUrl: '/mobile/superadmin',
    };
  }

  const currentUrl = safeUrl(window.location.origin, window.location.origin);
  const currentOrigin = currentUrl?.origin || '';
  const platformApiUrl = safeUrl(platformApiBase, currentOrigin);
  const platformAppUrl = PLATFORM_APP_URL
    ? safeUrl(PLATFORM_APP_URL, currentOrigin)
    : currentUrl;
  const platformApiOrigin = platformApiUrl?.origin || '';
  const platformAppOrigin = platformAppUrl?.origin || '';
  const controlUrl = platformAppUrl && PLATFORM_APP_URL
    ? `${platformAppUrl.origin}/mobile/superadmin`
    : '/mobile/superadmin';

  return {
    ready: Boolean(currentOrigin)
      && secureOrLocal(currentUrl)
      && secureOrLocal(platformApiUrl)
      && secureOrLocal(platformAppUrl)
      && platformApiOrigin === currentOrigin
      && platformAppOrigin === currentOrigin,
    currentOrigin,
    platformApiOrigin,
    platformAppOrigin,
    controlUrl,
  };
}

export function getPlatformControlUrl(): string {
  if (typeof window === 'undefined' || !PLATFORM_APP_URL) return '/mobile/superadmin';
  const parsed = safeUrl(PLATFORM_APP_URL, window.location.origin);
  return parsed ? `${parsed.origin}/mobile/superadmin` : '/mobile/superadmin';
}

export function isExternalPlatformControlUrl(controlUrl: string): boolean {
  if (typeof window === 'undefined') return false;
  const parsed = safeUrl(controlUrl, window.location.origin);
  return Boolean(parsed && parsed.origin !== window.location.origin);
}
