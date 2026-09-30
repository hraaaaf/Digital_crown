import { api } from './api';

export type WorkstationExperience = 'cabinet' | 'station' | 'control_center';

export type WorkstationBootstrapState = {
  workstationId: string | null;
  defaultExperience: WorkstationExperience | null;
  stationLocked: boolean;
  stationEscapeAuthorized: boolean;
  stationEscapeExpiresAt?: number | null;
  enrollmentRequired?: boolean;
  authenticated?: boolean;
  pinConfigured?: boolean;
  canManage?: boolean;
  canConfigurePin?: boolean;
};

export type WorkstationState = WorkstationBootstrapState & {
  workstationId: string;
  pinConfigured: boolean;
  canManage: boolean;
  canConfigurePin: boolean;
  enrollmentRequired?: false;
};

const CONVENIENCE_KEY = 'dc_workstation_default_experience';
const CHANNEL_NAME = 'dc-workstation-mode';
const LOCAL_EVENT = 'dc-workstation-mode-changed';

const emitWorkstationChange = () => {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new Event(LOCAL_EVENT));
  try {
    if ('BroadcastChannel' in window) {
      const channel = new BroadcastChannel(CHANNEL_NAME);
      channel.postMessage({ type: 'changed' });
      channel.close();
    }
  } catch {
    // Cross-tab notification is best effort; server state remains authoritative.
  }
};

const subscribeToWorkstationChanges = (listener: () => void) => {
  if (typeof window === 'undefined') return () => undefined;

  const localListener = () => listener();
  window.addEventListener(LOCAL_EVENT, localListener);

  let channel: BroadcastChannel | null = null;
  try {
    if ('BroadcastChannel' in window) {
      channel = new BroadcastChannel(CHANNEL_NAME);
      channel.addEventListener('message', listener);
    }
  } catch {
    channel = null;
  }

  return () => {
    window.removeEventListener(LOCAL_EVENT, localListener);
    if (channel) {
      channel.removeEventListener('message', listener);
      channel.close();
    }
  };
};

export const workstationModeService = {
  async getBootstrapState(): Promise<WorkstationBootstrapState> {
    const { data } = await api.get<WorkstationBootstrapState>('/workstation/bootstrap');
    return data;
  },

  async getState(): Promise<WorkstationState> {
    const { data } = await api.get<WorkstationState>('/workstation/state');
    try {
      if (data.defaultExperience) localStorage.setItem(CONVENIENCE_KEY, data.defaultExperience);
      else localStorage.removeItem(CONVENIENCE_KEY);
    } catch {
      // Convenience cache only. Server state remains authoritative.
    }
    return data;
  },

  async enrollWorkstation(accountPassword: string): Promise<WorkstationState> {
    const { data } = await api.post<WorkstationState>('/workstation/enroll', { accountPassword });
    emitWorkstationChange();
    return data;
  },

  async configureOwnerPin(accountPassword: string, newPin: string): Promise<void> {
    await api.post('/workstation/owner-pin', { accountPassword, newPin });
    emitWorkstationChange();
  },

  async changeMode(mode: WorkstationExperience, ownerPin: string): Promise<WorkstationState> {
    const { data } = await api.post<WorkstationState>('/workstation/mode', { mode, ownerPin });
    emitWorkstationChange();
    return data;
  },

  async authorizeStationEscape(ownerPin: string): Promise<{ expiresAt: number }> {
    const { data } = await api.post<{ expiresAt: number }>('/workstation/station/escape', { ownerPin });
    emitWorkstationChange();
    return data;
  },

  subscribe(listener: () => void): () => void {
    return subscribeToWorkstationChanges(listener);
  },
};
