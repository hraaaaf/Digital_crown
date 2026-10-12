/** LAB-ONLY mode. Both an explicit Vite build flag AND a live HTTPS
 * trycloudflare hostname are required. Product/production defaults to false.
 * Do not weaken Windows DPAPI, relay encryption or the remote-key endpoint.
 */
export function isSyntheticFieldLabLocalPairing(
  enabled: boolean,
  location?: Pick<Location, 'hostname' | 'protocol'>,
): boolean {
  return Boolean(
    enabled &&
    location?.protocol === 'https:' &&
    /^[a-z0-9-]+\.trycloudflare\.com$/i.test(location.hostname),
  );
}
