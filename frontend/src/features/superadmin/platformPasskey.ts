import { api, API_BASE, PLATFORM_API_BASE } from '../../services/api';
import { ensurePlatformStepUp } from '../../services/platformPasskey';

export type PlatformPasskeyStatus = {
  enrolled: boolean;
  origin_ready: boolean;
  step_up_valid: boolean;
  rp_id: string;
  expected_origin: string;
};

function platformApiBase(): string {
  return typeof window !== 'undefined' && window.location.pathname.startsWith('/mobile/superadmin')
    ? PLATFORM_API_BASE
    : API_BASE;
}

export const fetchPlatformPasskeyStatus = async (): Promise<PlatformPasskeyStatus> => {
  const response = await api.get('/superadmin/passkey/status');
  return response.data as PlatformPasskeyStatus;
};

export const establishPlatformStepUp = async (_enrolled: boolean): Promise<void> => {
  // Canonical ceremony implementation lives in services/platformPasskey.ts so
  // the control-center button and the mutation interceptor share one 5-minute
  // proof window instead of prompting WebAuthn twice.
  await ensurePlatformStepUp(platformApiBase());
};
