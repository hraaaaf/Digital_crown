import { useEffect, useState } from 'react';
import { api } from '../services/api';

export interface CabinetHealth {
  database: { status: 'ok' | 'error'; detail: string | null };
  disk: {
    status: 'ok' | 'warning' | 'critical' | 'unknown';
    free_gb: number | null;
    total_gb: number | null;
  };
  backup_local: {
    status: 'ok' | 'warning' | 'critical' | 'none';
    overall_status: string | null;
    age_hours: number | null;
    run_id: string | null;
  };
  offsite: {
    status: 'NOT_CONFIGURED' | 'ok' | 'warning';
    offsite_status: string | null;
    db_copied: boolean | null;
    media_copied: boolean | null;
  };
  overall_severity: 'ok' | 'warning' | 'critical';
}

export type CabinetHealthState =
  | { status: 'loading'; data: null }
  | { status: 'not_allowed'; data: null }
  | { status: 'unverified'; data: null }
  | { status: 'ready'; data: CabinetHealth };

export interface CabinetHealthDisplayState {
  label: string;
  dotClassName: string;
  isLoading: boolean;
}

export type CabinetHealthFetcher = () => Promise<CabinetHealth>;

const HEALTH_POLL_MS = 120_000;
const HEALTH_REQUEST_TIMEOUT_MS = 5_000;

const fetchCabinetHealth: CabinetHealthFetcher = async () => {
  const response = await api.get('/admin/cabinet-health', {
    timeout: HEALTH_REQUEST_TIMEOUT_MS,
  });
  return response.data as CabinetHealth;
};

export const getCabinetHealthDisplayState = (
  state: CabinetHealthState,
): CabinetHealthDisplayState => {
  if (state.status === 'loading') {
    return {
      label: 'Vérification en cours',
      dotClassName: 'bg-slate-400',
      isLoading: true,
    };
  }

  if (state.status === 'not_allowed') {
    return {
      label: 'Statut non disponible',
      dotClassName: 'bg-slate-400',
      isLoading: false,
    };
  }

  if (state.status === 'unverified') {
    return {
      label: 'Système non vérifié',
      dotClassName: 'bg-amber-500',
      isLoading: false,
    };
  }

  if (state.data.overall_severity === 'ok') {
    return {
      label: 'Système opérationnel',
      dotClassName: 'bg-emerald-500',
      isLoading: false,
    };
  }

  if (state.data.overall_severity === 'warning') {
    return {
      label: 'Vigilance requise',
      dotClassName: 'bg-amber-500',
      isLoading: false,
    };
  }

  return {
    label: 'Problème critique',
    dotClassName: 'bg-red-500',
    isLoading: false,
  };
};

export const useCabinetHealth = ({
  enabled,
  authLoading,
  pollMs = HEALTH_POLL_MS,
  fetcher = fetchCabinetHealth,
}: {
  enabled: boolean;
  authLoading: boolean;
  pollMs?: number;
  fetcher?: CabinetHealthFetcher;
}): CabinetHealthState => {
  const [state, setState] = useState<CabinetHealthState>({
    status: 'loading',
    data: null,
  });

  useEffect(() => {
    if (authLoading) {
      setState({ status: 'loading', data: null });
      return;
    }

    if (!enabled) {
      setState({ status: 'not_allowed', data: null });
      return;
    }

    let cancelled = false;

    const refresh = async () => {
      try {
        const data = await fetcher();
        if (!cancelled) {
          setState({ status: 'ready', data });
        }
      } catch {
        if (!cancelled) {
          setState({ status: 'unverified', data: null });
        }
      }
    };

    setState({ status: 'loading', data: null });
    void refresh();
    const interval = window.setInterval(() => {
      void refresh();
    }, pollMs);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [authLoading, enabled, fetcher, pollMs]);

  return state;
};
