import { beforeEach, describe, expect, it, vi } from 'vitest';

const storage = vi.hoisted(() => ({ saveWallet: vi.fn() }));
vi.mock('./PatientCompanionStorage', () => ({ PatientCompanionStorage: storage }));
vi.mock('../../services/api', () => ({ API_BASE: '' }));

import { PatientCompanionSync } from './PatientCompanionSync';

beforeEach(() => {
  storage.saveWallet.mockReset();
  vi.stubGlobal('fetch', vi.fn());
});

describe('PatientCompanionSync PC-01', () => {
  it('fetches only the active opaque context and persists one encrypted wallet snapshot', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ items: [{ datetime_start: '2026-09-20T09:00:00', motif: 'Contrôle', status: 'CONFIRME' }] }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ items: [{ share_id: 'share-1', resource_type: 'document', title: 'Ordonnance' }] }) } as Response);
    storage.saveWallet.mockResolvedValue({});

    const result = await PatientCompanionSync.sync({
      accessToken: 'device-token',
      context: { access_id: 'opaque-access', relationship_type: 'SELF', patient: { display_name: 'Aya' } },
      pairedAt: '2026-09-19T18:00:00Z',
    });

    expect(fetch).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/contexts/opaque-access/appointments'),
      expect.objectContaining({ headers: { Authorization: 'Bearer device-token' }, cache: 'no-store' }),
    );
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/contexts/opaque-access/shares'),
      expect.objectContaining({ headers: { Authorization: 'Bearer device-token' }, cache: 'no-store' }),
    );
    expect(result.appointments).toHaveLength(1);
    expect(result.shares).toHaveLength(1);
    expect(storage.saveWallet).toHaveBeenCalledWith(expect.objectContaining({
      version: 1,
      accessId: 'opaque-access',
      appointments: expect.any(Array),
      shares: expect.any(Array),
    }));
  });

  it('does not replace the encrypted offline snapshot when a sync request fails', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'Session expirée' }) } as Response);

    await expect(PatientCompanionSync.sync({
      accessToken: 'expired-token',
      context: { access_id: 'opaque-access', relationship_type: 'SELF', patient: { display_name: 'Aya' } },
      pairedAt: '2026-09-19T18:00:00Z',
    })).rejects.toMatchObject({ status: 401 });

    expect(storage.saveWallet).not.toHaveBeenCalled();
  });
});
