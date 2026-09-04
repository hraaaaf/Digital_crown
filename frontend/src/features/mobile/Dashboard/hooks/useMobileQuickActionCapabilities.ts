import { useCallback, useEffect, useState } from 'react';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { CryptoService } from '../../../../services/zka/CryptoService';

export interface MobileQuickActionCapabilities {
  can_create_appointment: boolean;
  can_create_patient: boolean;
  can_open_clinical_context: boolean;
  can_pay: boolean;
}

const DENY_ALL: MobileQuickActionCapabilities = {
  can_create_appointment: false,
  can_create_patient: false,
  can_open_clinical_context: false,
  can_pay: false,
};

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored.replace(/\/$/, '');
}

export function useMobileQuickActionCapabilities() {
  const [capabilities, setCapabilities] = useState<MobileQuickActionCapabilities>(DENY_ALL);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) {
        setCapabilities(DENY_ALL);
        setLoaded(true);
        return;
      }
      const response = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/quick-actions/capabilities`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error(`Capabilities unavailable (${response.status})`);
      const raw = await response.json();
      const payload = raw.payload
        ? await CryptoService.decryptPayload(raw.payload, creds.masterKey)
        : raw;
      setCapabilities({
        can_create_appointment: payload?.can_create_appointment === true,
        can_create_patient: payload?.can_create_patient === true,
        can_open_clinical_context: payload?.can_open_clinical_context === true,
        can_pay: payload?.can_pay === true,
      });
    } catch {
      // Fail closed. A missing capability response never grants a quick action.
      setCapabilities(DENY_ALL);
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { capabilities, loaded, refresh };
}
