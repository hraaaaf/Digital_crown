import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AppUser } from '../../../types';
import { useTodayAppointments } from './useTodayAppointments';

const apiGet = vi.hoisted(() => vi.fn());
const apiPut = vi.hoisted(() => vi.fn());
vi.mock('../../../services/api', () => ({
  api: { get: apiGet, put: apiPut },
}));

const canonical = {
  id: 50, datetime_start: '2026-10-20T09:15:00', status: 'EN_S_ATTENTE',
  patient_id: 500, patient_name: 'SECRET-CABINET-PATIENT', motif: 'SENSITIVE-MOTIF',
};

const owner = {
  id: 'staff-01', role: 'SECRETAIRE', employer_id: 15,
  permissions: { agenda: true, patients: true },
} as unknown as AppUser;

const restricted = {
  ...owner, permissions: { agenda: true, patients: false },
} as AppUser;

const options = {
  authLoading: false, onStatsRefresh: async () => {}, onCompleted: () => {},
};

beforeEach(() => { apiGet.mockReset(); apiPut.mockReset(); });

describe('LOT07/07-C real Agenda hook session and permission firewall', () => {
  it('removes privileged rows during render before the revoked-permission HTTP fetch completes', async () => {
    apiGet.mockResolvedValueOnce({ data: [canonical] });
    let releaseRestricted: ((v: unknown) => void) | undefined;
    apiGet.mockImplementationOnce(() => new Promise(resolve => { releaseRestricted = resolve; }));
    const { result, rerender } = renderHook(
      ({ user }: { user: AppUser }) => useTodayAppointments({ ...options, user }),
      { initialProps: { user: owner } },
    );
    await waitFor(() => expect(result.current.appointments?.[0]?.patient?.nom).toBe('SECRET-CABINET-PATIENT'));
    rerender({ user: restricted });
    expect(result.current.appointments).toBeNull();
    expect(result.current.appointmentsState).toBe('loading');
    expect(JSON.stringify(result.current.appointments)).not.toContain('SECRET-CABINET-PATIENT');
    await act(async () => { releaseRestricted!({ data: [canonical] }); });
    await waitFor(() => expect(result.current.appointments?.[0]?.patient).toBeNull());
    expect(result.current.appointments?.[0]?.patient_id).toBeNull();
    expect(JSON.stringify(result.current.appointments)).not.toContain('SECRET-CABINET-PATIENT');
  });

  it('ignores an older privileged response arriving after a permission or cabinet switch', async () => {
    let releaseOld: ((v: unknown) => void) | undefined;
    let releaseNew: ((v: unknown) => void) | undefined;
    apiGet.mockImplementationOnce(() => new Promise(resolve => { releaseOld = resolve; }));
    apiGet.mockImplementationOnce(() => new Promise(resolve => { releaseNew = resolve; }));
    const { result, rerender } = renderHook(
      ({ user }: { user: AppUser }) => useTodayAppointments({ ...options, user }),
      { initialProps: { user: owner } },
    );
    await waitFor(() => expect(apiGet).toHaveBeenCalledTimes(1));
    rerender({ user: { ...restricted, employer_id: 99 } });
    await waitFor(() => expect(apiGet).toHaveBeenCalledTimes(2));
    await act(async () => { releaseNew!({ data: [canonical] }); });
    await waitFor(() => expect(result.current.appointmentsState).toBe('ready'));
    expect(result.current.appointments?.[0]?.patient).toBeNull();
    await act(async () => { releaseOld!({ data: [canonical] }); });
    expect(result.current.appointments?.[0]?.patient).toBeNull();
    expect(result.current.appointments?.[0]?.patient_id).toBeNull();
  });


  it('keeps a frontdesk name visible as schedule text without inventing a linked Patient', async () => {
    apiGet.mockResolvedValue({ data: [{ ...canonical, patient_id: null, patient_name: 'FRONTDESK UNLINKED' }] });
    apiPut.mockResolvedValue({ data: {} });
    const onCompleted = vi.fn();
    const { result } = renderHook(() => useTodayAppointments({ ...options, user: owner, onCompleted }));
    await waitFor(() => expect(result.current.appointmentsState).toBe('ready'));
    expect(result.current.appointments?.[0]?.patient_name).toBe('FRONTDESK UNLINKED');
    expect(result.current.appointments?.[0]?.patient_id).toBeNull();
    expect(result.current.appointments?.[0]?.patient).toBeNull();
    await act(async () => { await result.current.updateAppointmentStatus(50, 'TERMINÉ'); });
    expect(apiPut).toHaveBeenCalledWith('/appointments/50', { status: 'TERMINÉ' });
    expect(onCompleted).not.toHaveBeenCalled();
  });

  it('preserves Ghost Action callback for a canonical linked patient after completion', async () => {
    apiGet.mockResolvedValue({ data: [canonical] });
    apiPut.mockResolvedValue({ data: {} });
    const onCompleted = vi.fn();
    const { result } = renderHook(() => useTodayAppointments({ ...options, user: owner, onCompleted }));
    await waitFor(() => expect(result.current.appointments?.[0]?.patient?.id).toBe(500));
    await act(async () => { await result.current.updateAppointmentStatus(50, 'TERMINÉ'); });
    expect(onCompleted).toHaveBeenCalledTimes(1);
    expect(onCompleted).toHaveBeenCalledWith(expect.objectContaining({ id: 500 }));
  });
});
