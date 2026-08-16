import { useCallback, useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type { DashboardStats, DataState } from '../types';

const EMPTY_STATS: DashboardStats = {
  total_patients: 0,
  total_analyses: 0,
  in_waiting: 0,
  weekly_activity: [0, 0, 0, 0, 0, 0, 0],
  weekly_patient_counts: [0, 0, 0, 0, 0, 0, 0],
  recent_patients: [],
};

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
      console.warn('Route API manquante ou invalide, injection des données de secours.', error);
      setStats(EMPTY_STATS);
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
