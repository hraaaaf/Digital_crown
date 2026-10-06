import { api } from './api';

export type StationStaffAssistanceAlert = {
  alertId: number;
  requestedAt: string;
};

export const stationStaffAssistanceService = {
  async list(): Promise<StationStaffAssistanceAlert[]> {
    const { data } = await api.get<{ alerts: StationStaffAssistanceAlert[] }>('/workstation/staff-assistance');
    return data.alerts;
  },

  async acknowledge(alertId: number): Promise<void> {
    await api.post(`/workstation/staff-assistance/${alertId}/acknowledge`);
  },
};
