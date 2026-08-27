export type MobilePasskeyState = 'disabled' | 'pending' | 'enabled';
export interface MobilePasskeyStatus {
  state: MobilePasskeyState;
  credential_id: string | null;
  rp_id: string;
  expected_origin: string;
  origin_ready: boolean;
  user_verification: 'required';
  server_gate: boolean;
}
function currentStatus(): MobilePasskeyStatus {
  const locked = typeof window !== 'undefined' && window.location.pathname.includes('mobile-m6-i-lock');
  return {
    state: locked ? 'enabled' : 'disabled',
    credential_id: locked ? 'visual-credential' : null,
    rp_id: 'digitalcrown.local',
    expected_origin: 'https://digitalcrown.local:5173',
    origin_ready: true,
    user_verification: 'required',
    server_gate: locked,
  };
}
export async function getMobilePasskeyStatus(): Promise<MobilePasskeyStatus> { return currentStatus(); }
export async function activateMobilePasskey(): Promise<MobilePasskeyStatus> { return { ...currentStatus(), state: 'enabled', server_gate: true }; }
export async function disableMobilePasskey(): Promise<void> {}
export function isStablePasskeyOrigin(): boolean { return true; }
export async function unlockMobilePasskey(): Promise<MobilePasskeyStatus> { return { ...currentStatus(), state: 'enabled', server_gate: true }; }
