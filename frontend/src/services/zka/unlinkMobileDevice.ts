import { MobileStorage } from './MobileStorage';

function resolveCabinetBase(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  return stored.includes('localhost') || stored.includes('127.0.0.1')
    ? `${window.location.protocol}//${hostname}:8005`
    : stored;
}

/**
 * Explicit unlink of ONE phone, never a cabinet-wide revocation.
 * Local clinical data is purged regardless of LAN/server availability.
 * false means remote revocation was NOT confirmed; the cabinet must finish it.
 */
export async function unlinkCurrentMobileDevice(): Promise<boolean> {
  let remoteRevoked = false;
  try {
    const creds = await MobileStorage.getCredentials();
    if (creds && typeof navigator !== 'undefined' && navigator.onLine !== false) {
      const response = await fetch(`${resolveCabinetBase(creds.api_base_url)}/api/mobile/revoke-device`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(2500),
      });
      remoteRevoked = response.ok;
    }
  } catch {
    // Local unlink remains mandatory if the on-premise server is unreachable.
  } finally {
    await MobileStorage.clearAll();
  }
  return remoteRevoked;
}
