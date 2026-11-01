/**
 * Non-clinical tombstone: a prior phone was locally unlinked but its
 * server-side revocation could not be confirmed. Never store a token, patient,
 * cabinet identifier, IP, or device ID here.
 *
 * This intentionally survives MobileStorage.clearAll(), so restarting the
 * installed PWA cannot erase the administrator follow-up obligation.
 */
const NOTICE_KEY = 'dc_mobile_remote_revocation_unconfirmed_v1';

export function hasUnconfirmedMobileRevocation(): boolean {
  try { return localStorage.getItem(NOTICE_KEY) === '1'; }
  catch { return false; }
}

export function markUnconfirmedMobileRevocation(): void {
  try { localStorage.setItem(NOTICE_KEY, '1'); }
  catch { /* restricted private browsing: URL fallback still displays warning */ }
}

/** Human acknowledgement, NOT a server revocation. */
export function acknowledgeMobileRevocationFollowUp(): void {
  try { localStorage.removeItem(NOTICE_KEY); }
  catch { /* the warning can only be hidden for this render */ }
}
