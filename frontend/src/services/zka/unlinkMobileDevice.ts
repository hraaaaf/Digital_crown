import { MobileStorage, resolveMobileApiBaseUrl } from './MobileStorage';
import { markUnconfirmedMobileRevocation } from './mobileRevocationFollowUp';

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
      const response = await fetch(`${resolveMobileApiBaseUrl(creds.api_base_url)}/api/mobile/revoke-device`, {
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
    // Only a confirmed revoke of THIS device succeeds. A previous pending
    // revocation remains pending even if a later/new device is revoked.
    if (!remoteRevoked) markUnconfirmedMobileRevocation();
  }
  return remoteRevoked;
}
