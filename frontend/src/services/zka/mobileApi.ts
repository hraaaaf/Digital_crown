import { MobileStorage } from './MobileStorage';
import { mobileFetch } from './mobileFetch';

function resolveMobileApiBase(stored: string): string {
  if (typeof window === 'undefined') return stored;
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}

export async function mobileApiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const creds = await MobileStorage.getCredentials();
  if (!creds) throw new Error('Non appairé');
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return mobileFetch(`${resolveMobileApiBase(creds.api_base_url)}/api/mobile${normalized}`, init);
}

export async function mobileApiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await mobileApiFetch(path, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload?.detail === 'string' ? payload.detail : `Erreur ${response.status}`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
