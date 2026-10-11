import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { useMobileDashboard } from './useMobileDashboard';

vi.mock('../../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(),
    getLastSnapshot: vi.fn(),
    getActionQueue: vi.fn(),
    saveLastSnapshot: vi.fn(),
    enqueueAction: vi.fn(),
    removeActionFromQueue: vi.fn(),
  },
  isReplayablePocketAction: vi.fn().mockReturnValue(true),
}));
vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/mobileApi', () => ({ mobileApiJson: vi.fn() }));
vi.mock('react-hot-toast', () => ({
  default: Object.assign(vi.fn(), { error: vi.fn(), success: vi.fn() }),
}));

const credentials = {
  publicId: 'abcdef1234567890',
  masterKey: 'a'.repeat(64),
  access_token: 'paired-token',
  refresh_token: 'refresh-token',
  device_id: 'device-a',
  api_base_url: 'http://127.0.0.1:8005',
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(MobileStorage.getCredentials).mockResolvedValue(credentials);
  vi.mocked(MobileStorage.getLastSnapshot).mockResolvedValue(null);
  vi.mocked(MobileStorage.getActionQueue).mockResolvedValue([]);
  vi.mocked(MobileStorage.saveLastSnapshot).mockResolvedValue(undefined);
  vi.mocked(mobileFetch).mockImplementation(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ appointments: [], role: 'DENTISTE', debtors: [] }),
  } as Response));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Pocket P0 — deletion must be server-confirmed online', () => {
  it('never attempts a DELETE or asks for deletion confirmation while offline', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const { result } = renderHook(() => useMobileDashboard());

    await act(async () => {
      await result.current.actions.handleDeleteAppt(41);
    });

    expect(confirm).not.toHaveBeenCalled();
    expect(vi.mocked(mobileFetch).mock.calls.some(([, options]) => options?.method === 'DELETE')).toBe(false);
    expect(MobileStorage.enqueueAction).not.toHaveBeenCalled();
    expect(toast.error).toHaveBeenCalledWith('Suppression impossible hors ligne. Reconnectez-vous au cabinet.');
  });

  it('does not enqueue or optimistically erase a deletion on a network failure', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.mocked(mobileFetch).mockImplementation(async (_url, options) => {
      if (options?.method === 'DELETE') throw new TypeError('Network disconnected');
      return {
        ok: true,
        status: 200,
        json: async () => ({ appointments: [{ id: 41, patient_name: 'Patient test', status: 'PLANIFIE' }], role: 'DENTISTE', debtors: [] }),
      } as Response;
    });
    const { result } = renderHook(() => useMobileDashboard());

    await act(async () => {
      await result.current.actions.handleDeleteAppt(41);
    });

    expect(vi.mocked(mobileFetch).mock.calls.filter(([, options]) => options?.method === 'DELETE')).toHaveLength(1);
    expect(MobileStorage.enqueueAction).not.toHaveBeenCalled();
    expect(toast.success).not.toHaveBeenCalledWith('Rendez-vous supprimé');
    expect(toast.error).toHaveBeenCalledWith('Suppression non confirmée par le cabinet. Réessayez en ligne.');
  });

  it('does not claim success on a server rejection or a revoked session', async () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.mocked(mobileFetch).mockImplementation(async (_url, options) => {
      if (options?.method === 'DELETE') return { ok: false, status: 403 } as Response;
      return { ok: true, status: 200, json: async () => ({ appointments: [], role: 'DENTISTE' }) } as Response;
    });
    const { result } = renderHook(() => useMobileDashboard());

    await act(async () => {
      await result.current.actions.handleDeleteAppt(41);
    });

    expect(MobileStorage.enqueueAction).not.toHaveBeenCalled();
    expect(toast.success).not.toHaveBeenCalledWith('Rendez-vous supprimé');
    expect(toast.error).toHaveBeenCalledWith('Suppression refusée (403)');
  });
});

describe('Pocket P2 — neutral appointment communication', () => {
  it('never prepopulates patient identity, treatment motif or fabricated dates into a WhatsApp URL', async () => {
    const { result } = renderHook(() => useMobileDashboard());
    await act(async () => {
      result.current.actions.setWhatsappApt({
        id: 41,
        patient_id: 8,
        patient_name: 'Patiente Confidentielle',
        phone: '+212600000001',
        date: '2026-11-20',
        time: '09:30',
        motif: 'Endodontie clinique',
        status: 'PLANIFIE',
        duration_minutes: 45,
      });
    });
    expect(result.current.state.customMessage).toContain('rappel de votre rendez-vous');
    expect(result.current.state.customMessage).not.toContain('Patiente Confidentielle');
    expect(result.current.state.customMessage).not.toContain('Endodontie');
    expect(result.current.state.customMessage).not.toContain('demain');

    await act(async () => {
      result.current.actions.setWhatsappTemplate('confirmation');
    });
    expect(result.current.state.customMessage).toContain('votre rendez-vous au cabinet est confirmé');
    expect(result.current.state.customMessage).not.toContain('Patiente Confidentielle');
    expect(result.current.state.customMessage).not.toContain('Endodontie');
    expect(result.current.state.customMessage).not.toContain('09:30');
  });
});
