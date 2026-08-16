import { useCallback, useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type { DashboardStats, DataState } from '../types';

export const useDashboardStats = (
  user: AppUser | null,
  authLoading: boolean,
) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsState, setStatsState] = useState<DataState>('idle');
  const [praticienName, setPraticienName] = useState('Praticien');

  const canReadPatients = hasAccess(user, 'patients');

  const refreshStats = useCallback(async () => {
    if (!user || !canReadPatients) {
      setStats(null);
      setStatsState('idle');
      return;
    }

    setStatsState('loading');
    try {
      const response = await api.get('/admin/dashboard/stats');
      setStats(response.data);
      setStatsState('ready');
    } catch (error) {
      console.warn('Statistiques Dashboard indisponibles.', error);
      setStats(null);
      setStatsState('error');
    }
  }, [canReadPatients, user]);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !canReadPatients) {
      setStats(null);
      setStatsState('idle');
      return;
    }
    void refreshStats();
  }, [authLoading, canReadPatients, refreshStats, user]);

  useEffect(() => {
    if (authLoading || !user) return;

    let cancelled = false;
    const fetchConfig = async () => {
      try {
        const response = await api.get('/admin/cabinet/me');
        const config = response.data;
        if (!cancelled && config.header_lines_fr && config.header_lines_fr.length > 0) {
          setPraticienName(config.header_lines_fr[0]);
        }
      } catch (error) {
        console.warn('Erreur chargement configuration cabinet', error);
      }
    };

    void fetchConfig();
    return () => {
      cancelled = true;
    };
  }, [authLoading, user]);

  return {
    stats,
    statsState,
    praticienName,
    refreshStats,
  };
};
