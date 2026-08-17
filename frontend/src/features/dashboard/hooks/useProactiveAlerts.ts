import { useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type { DataState, ProactiveAlert } from '../types';

export const useProactiveAlerts = (
  user: AppUser | null,
  authLoading: boolean,
) => {
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([]);
  const [alertsState, setAlertsState] = useState<DataState>('idle');
  const canReadPatients = hasAccess(user, 'patients');

  useEffect(() => {
    if (authLoading) return;
    if (!user || !canReadPatients) {
      setAlerts([]);
      setAlertsState('idle');
      return;
    }

    let cancelled = false;
    setAlertsState('loading');
    api.get('/intelligence/alerts/today')
      .then(response => {
        if (!cancelled) {
          setAlerts(response.data.alerts || []);
          setAlertsState('ready');
        }
      })
      .catch(error => {
        console.warn('Erreur alerts', error);
        if (!cancelled) {
          setAlerts([]);
          setAlertsState('error');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [authLoading, canReadPatients, user]);

  const markRead = async (alertId: number) => {
    if (!canReadPatients) return;
    try {
      await api.patch(`/intelligence/alerts/${alertId}/read`);
      setAlerts(previous => previous.filter(alert => alert.id !== alertId));
    } catch (error) {
      console.warn("Erreur lors du marquage de l'alerte", error);
    }
  };

  const snooze = async (alertId: number) => {
    if (!canReadPatients) return;
    try {
      await api.patch(`/intelligence/alerts/${alertId}/snooze`);
      setAlerts(previous => previous.filter(alert => alert.id !== alertId));
    } catch (error) {
      console.warn("Erreur lors du report de l'alerte", error);
    }
  };

  return {
    alerts,
    alertsState,
    markRead,
    snooze,
  };
};
