import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  getCabinetHealthDisplayState,
  type CabinetHealth,
  useCabinetHealth,
} from './useCabinetHealth';

const healthy: CabinetHealth = {
  database: { status: 'ok', detail: null },
  disk: { status: 'ok', free_gb: 120, total_gb: 500 },
  backup_local: {
    status: 'ok',
    overall_status: 'SUCCESS',
    age_hours: 4,
    run_id: 'run-d2',
  },
  offsite: {
    status: 'NOT_CONFIGURED',
    offsite_status: null,
    db_copied: null,
    media_copied: null,
  },
  overall_severity: 'ok',
};

const flushPromises = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('useCabinetHealth — vérité système D2', () => {
  it('distingue chargement et absence d’autorisation sans état positif', () => {
    const fetcher = vi.fn().mockResolvedValue(healthy);

    const loading = renderHook(() =>
      useCabinetHealth({ enabled: true, authLoading: true, fetcher }),
    );
    expect(loading.result.current.status).toBe('loading');
    expect(getCabinetHealthDisplayState(loading.result.current).label).toBe('Vérification en cours');
    loading.unmount();

    const denied = renderHook(() =>
      useCabinetHealth({ enabled: false, authLoading: false, fetcher }),
    );
    expect(denied.result.current.status).toBe('not_allowed');
    expect(getCabinetHealthDisplayState(denied.result.current).label).toBe('Statut non disponible');
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('n’affiche opérationnel qu’après une réponse de santé réelle', async () => {
    const fetcher = vi.fn().mockResolvedValue(healthy);
    const { result } = renderHook(() =>
      useCabinetHealth({ enabled: true, authLoading: false, fetcher }),
    );

    expect(result.current.status).toBe('loading');
    await act(flushPromises);

    expect(result.current.status).toBe('ready');
    expect(getCabinetHealthDisplayState(result.current).label).toBe('Système opérationnel');
  });

  it('passe en non vérifié sur erreur réseau puis récupère au polling suivant', async () => {
    vi.useFakeTimers();
    const fetcher = vi
      .fn<() => Promise<CabinetHealth>>()
      .mockRejectedValueOnce(new Error('network unavailable'))
      .mockResolvedValueOnce(healthy);

    const { result } = renderHook(() =>
      useCabinetHealth({
        enabled: true,
        authLoading: false,
        pollMs: 1_000,
        fetcher,
      }),
    );

    await act(flushPromises);
    expect(result.current.status).toBe('unverified');
    expect(getCabinetHealthDisplayState(result.current).label).toBe('Système non vérifié');

    await act(async () => {
      vi.advanceTimersByTime(1_000);
      await flushPromises();
    });

    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(result.current.status).toBe('ready');
    expect(getCabinetHealthDisplayState(result.current).label).toBe('Système opérationnel');
  });

  it('mappe explicitement vigilance et critique', () => {
    const warning = getCabinetHealthDisplayState({
      status: 'ready',
      data: { ...healthy, overall_severity: 'warning' },
    });
    const critical = getCabinetHealthDisplayState({
      status: 'ready',
      data: { ...healthy, overall_severity: 'critical' },
    });

    expect(warning.label).toBe('Vigilance requise');
    expect(critical.label).toBe('Problème critique');
  });
});
