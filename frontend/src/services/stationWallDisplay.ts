import { api } from './api';

export type WallDisplayEntry = {
  ticketNumber: number;
  initials: string;
};

export type WallDisplayCall = WallDisplayEntry & {
  expiresAt: string;
};

export type WallDisplaySnapshot = {
  waitingCount: number;
  entries: WallDisplayEntry[];
  currentCall: WallDisplayCall | null;
  callTtlSeconds: number;
};

export const stationWallDisplayService = {
  async snapshot(): Promise<WallDisplaySnapshot> {
    const { data } = await api.get<WallDisplaySnapshot>('/workstation/wall-display');
    return data;
  },

  async callPatient(appointmentId: number, ticketNumber?: number): Promise<WallDisplayCall & { status: 'CALLED' }> {
    const { data } = await api.post(
      `/workstation/wall-display/appointments/${appointmentId}/call`,
      { ticketNumber: ticketNumber ?? null },
    );
    return data;
  },
};
