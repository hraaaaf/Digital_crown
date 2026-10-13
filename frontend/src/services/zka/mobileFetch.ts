import { MobileStorage } from './MobileStorage';
import { isExplicitMobileBiometricLock } from './mobileBiometricLock';

function withMobileAuth(init: RequestInit, token: string): RequestInit {
  const headers = new Headers(init.headers ?? {});
  headers.set('Authorization', `Bearer ${token}`);
  return { ...init, headers };
}

async function propagateBiometricLock(response: Response): Promise<Response> {
  if (response.status === 423) {
    // Keep the response body available to the caller; a generic 423 must never
    // impersonate a WebAuthn lock after a fresh, successful pairing.
    const payload: unknown = await response.clone().json().catch(() => null);
    if (isExplicitMobileBiometricLock(response.status, payload)) {
      MobileStorage.lockBiometricVault();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('digitalcrown:mobile-biometric-locked'));
      }
    }
  }
  return response;
}

/** Native fetch for paired mobile routes with biometric UV memory-token support and one refresh retry. */
export async function mobileFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const creds = await MobileStorage.getCredentials();
  if (!creds) throw new Error('Non appairé');

  const biometricToken = MobileStorage.getBiometricAccessToken();
  const first = await fetch(input, withMobileAuth(init, biometricToken || creds.access_token));
  if (first.status !== 401) return propagateBiometricLock(first);

  // A 5-minute UV JWT may simply have expired. Drop it before rotating the durable
  // device refresh token; the retried request will then correctly return 423 if
  // biometric step-up is still required.
  if (biometricToken) MobileStorage.clearBiometricAccessToken();
  const refreshed = await MobileStorage.refreshCredentials();
  if (!refreshed) return first;
  const retry = await fetch(input, withMobileAuth(init, refreshed.access_token));
  return propagateBiometricLock(retry);
}
