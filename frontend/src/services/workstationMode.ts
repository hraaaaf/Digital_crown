import { api } from './api';

export type WorkstationExperience = 'cabinet' | 'station' | 'control_center';

export type WorkstationBootstrapState = {
  workstationId: string | null;
  defaultExperience: WorkstationExperience | null;
  stationLocked: boolean;
  stationEscapeAuthorized: boolean;
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
};

const CONVENIENCE_KEY = 'dc_workstation_default_experience';

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

  async configureOwnerPin(accountPassword: string, newPin: string): Promise<void> {
    await api.post('/workstation/owner-pin', { accountPassword, newPin });
  },

  async changeMode(mode: WorkstationExperience, ownerPin: string): Promise<WorkstationState> {
    const { data } = await api.post<WorkstationState>('/workstation/mode', { mode, ownerPin });
    return data;
  },

  async authorizeStationEscape(ownerPin: string): Promise<void> {
    await api.post('/workstation/station/escape', { ownerPin });
  },
};
