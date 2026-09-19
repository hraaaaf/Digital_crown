import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../services/zka/mobileFetch';
import { unlockMobilePasskey } from '../../../services/zka/mobilePasskey';
import { useMobileSuperAdmin } from './useMobileSuperAdmin';

vi.mock('../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(),
    getBiometricAccessToken: vi.fn(),
    clearBiometricAccessToken: vi.fn(),
  },
}));

vi.mock('../../../services/zka/mobileFetch', () => ({
  mobileFetch: vi.fn(),
}));

vi.mock('../../../services/zka/mobilePasskey', () => ({
  unlockMobilePasskey: vi.fn(),
}));

const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

function pathOf(input: RequestInfo | URL) {
  const url = new URL(String(input));
  return url.pathname + url.search;
}

let refuseGoldDowngrade = false;

beforeEach(() => {
  vi.clearAllMocks();
  refuseGoldDowngrade = false;
  vi.mocked(MobileStorage.getCredentials).mockResolvedValue({
    publicId: '0123456789abcdef',
    masterKey: '',
    access_token: 'durable-mobile-token',
    refresh_token: 'refresh-token',
    device_id: 'device-test',
    api_base_url: 'http://127.0.0.1:8005',
  });
  vi.mocked(MobileStorage.getBiometricAccessToken).mockReturnValue(null);
  vi.mocked(unlockMobilePasskey).mockResolvedValue(undefined as never);

  vi.mocked(mobileFetch).mockImplementation(async (input, init) => {
    const path = pathOf(input);
    const method = init?.method || 'GET';

    if (path === '/api/superadmin/clients' && method === 'GET') {
      return jsonResponse([{
        id: 42,
        nom_complet: 'Dr Pack Test',
        email: 'pack@example.test',
        cabinet_name: 'Cabinet Pack Test',
        is_active: true,
        is_licensed: true,
        license_expires_at: '2030-01-01T00:00:00.000Z',
        is_archived: false,
        is_suspended: false,
        internal_notes: null,
        subscription_plan: 'ELITE',
        stats: { total_patients: 0, total_ia_panoramique: 0, total_ia_cephalo: 0 },
      }]);
    }
    if (path === '/api/superadmin/trial-codes' && method === 'GET') return jsonResponse([]);

    if (path.startsWith('/api/superadmin/clients/42/plan?plan=') && method === 'PATCH') {
      if (path.endsWith('plan=GOLD') && refuseGoldDowngrade) {
        return jsonResponse({
          detail: 'Passage au pack GOLD impossible : équipe réservée 2 dentiste(s) / 3 assistante(s), limites cibles 1 / 2.',
        }, 409);
      }
      return jsonResponse({ status: 'success' });
    }

    if (path.startsWith('/api/superadmin/clients/42/grant-license?action=') && method === 'POST') {
      return jsonResponse({ status: 'success' });
    }
    if (path === '/api/superadmin/clients/42/archive' && method === 'PATCH') {
      return jsonResponse({ status: 'success', is_archived: true });
    }
    if (path === '/api/superadmin/clients/42/suspend' && method === 'PATCH') {
      return jsonResponse({ status: 'success', is_suspended: true });
    }
    if (path === '/api/superadmin/clients/42/notes' && method === 'PATCH') {
      return jsonResponse({ status: 'success', internal_notes: 'Audit note' });
    }
    if (path === '/api/superadmin/clients/42/license-history' && method === 'GET') {
      return jsonResponse([{ id: 1, action: 'grant', duration: 30 }]);
    }
    if (path === '/api/superadmin/clients/42/send-renewal-email' && method === 'POST') {
      return jsonResponse({ status: 'success', message: 'WhatsApp de relance envoyé avec succès à 0600000000.' });
    }
    if (path === '/api/superadmin/clients/42/validate' && method === 'POST') {
      return jsonResponse({ status: 'success' });
    }

    throw new Error(`Unexpected mobileFetch ${method} ${path}`);
  });
});

describe('useMobileSuperAdmin commercial pack actions', () => {
  it('executes GOLD, PREMIUM and ELITE pack changes through the real request layer', async () => {
    const { result } = renderHook(() => useMobileSuperAdmin());
    await waitFor(() => expect(result.current.loadingCore).toBe(false));

    for (const plan of ['GOLD', 'PREMIUM', 'ELITE']) {
      let ok = false;
      await act(async () => {
        ok = await result.current.coreActions.setPlan(42, plan);
      });
      expect(ok).toBe(true);
      expect(result.current.lastMessage).toBe(`Pack ${plan} attribué.`);
      expect(mobileFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/superadmin/clients/42/plan?plan=${plan}`),
        expect.objectContaining({ method: 'PATCH' }),
      );
    }
  });

  it('surfaces the exact server downgrade refusal instead of inventing a generic reason', async () => {
    refuseGoldDowngrade = true;
    const { result } = renderHook(() => useMobileSuperAdmin());
    await waitFor(() => expect(result.current.loadingCore).toBe(false));

    let ok = true;
    await act(async () => {
      ok = await result.current.coreActions.setPlan(42, 'GOLD');
    });

    expect(ok).toBe(false);
    expect(result.current.error).toContain('Passage au pack GOLD impossible');
    expect(result.current.error).toContain('2 dentiste(s) / 3 assistante(s)');
  });

  it('executes every licence action plus archive, suspend, notes, history, renewal and validate', async () => {
    const { result } = renderHook(() => useMobileSuperAdmin());
    await waitFor(() => expect(result.current.loadingCore).toBe(false));

    for (const action of ['1m', '3m', '6m', '1y', 'revoke']) {
      let ok = false;
      await act(async () => {
        ok = await result.current.coreActions.grantLicense(42, action);
      });
      expect(ok).toBe(true);
      expect(mobileFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/superadmin/clients/42/grant-license?action=${action}`),
        expect.objectContaining({ method: 'POST' }),
      );
    }

    await act(async () => {
      expect(await result.current.coreActions.toggleArchive(42)).toBe(true);
      expect(await result.current.coreActions.toggleSuspend(42)).toBe(true);
      expect(await result.current.coreActions.saveNotes(42, 'Audit note')).toBe(true);
      expect(await result.current.coreActions.sendRenewal(42, 'Renouvellement')).toBe(true);
      expect(await result.current.coreActions.validateClient(42)).toBe(true);
    });

    let history: Array<Record<string, unknown>> = [];
    await act(async () => {
      history = await result.current.coreActions.getHistory(42);
    });
    expect(history).toHaveLength(1);
    expect(history[0].action).toBe('grant');
  });
});
