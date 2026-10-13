/**
 * A 423 is an HTTP lock, not automatically a biometric lock.
 * Only the server's canonical biometric step-up code may relock a paired
 * device. Other refusals stay refused by their original caller, fail-closed.
 */
export function isExplicitMobileBiometricLock(status: number, payload: unknown): boolean {
  if (status !== 423 || !payload || typeof payload !== 'object') return false;
  const detail = (payload as { detail?: unknown }).detail;
  return !!detail && typeof detail === 'object'
    && (detail as { code?: unknown }).code === 'MOBILE_BIOMETRIC_LOCKED';
}
