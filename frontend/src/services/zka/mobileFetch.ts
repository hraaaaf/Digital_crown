import { MobileStorage } from './MobileStorage';

function withMobileAuth(init: RequestInit, token: string): RequestInit {
  const headers = new Headers(init.headers ?? {});
  headers.set('Authorization', `Bearer ${token}`);
  return { ...init, headers };
}

/** Native fetch for paired mobile routes with one device-bound refresh retry on 401. */
export async function mobileFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const creds = await MobileStorage.getCredentials();
  if (!creds) throw new Error('Non appairé');

  const first = await fetch(input, withMobileAuth(init, creds.access_token));
  if (first.status !== 401) return first;

  const refreshed = await MobileStorage.refreshCredentials();
  if (!refreshed || refreshed.access_token === creds.access_token) return first;
  return fetch(input, withMobileAuth(init, refreshed.access_token));
}
