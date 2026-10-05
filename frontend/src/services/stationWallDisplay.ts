import { api } from './api';

export type WallIdentityMode = 'initials' | 'full_name' | 'number_only';

export type WallDisplayEntry = {
  ticketNumber: number;
  identityLabel: string | null;
};

export type WallDisplayCall = WallDisplayEntry & {
  expiresAt: string;
};

export type WallDisplaySnapshot = {
  waitingCount: number;
  entries: WallDisplayEntry[];
  currentCall: WallDisplayCall | null;
  callTtlSeconds: number;
  identityMode: WallIdentityMode;
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
