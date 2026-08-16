import { useEffect, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type {
  ConversionData,
  DataState,
  FinanceToday,
  ForecastData,
  LatentCashData,
  ProjectionData,
} from '../types';

export const useDashboardFinance = (
  user: AppUser | null,
  authLoading: boolean,
) => {
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [conversion, setConversion] = useState<ConversionData | null>(null);
  const [projection, setProjection] = useState<ProjectionData | null>(null);
  const [latentCash, setLatentCash] = useState<LatentCashData | null>(null);
  const [financeToday, setFinanceToday] = useState<FinanceToday | null>(null);
  const [financeState, setFinanceState] = useState<DataState>('idle');

  const canReadAccounting = hasAccess(user, 'accounting');

  useEffect(() => {
    if (authLoading) return;

    if (!user || !canReadAccounting) {
      setForecast(null);
      setConversion(null);
      setProjection(null);
      setLatentCash(null);
      setFinanceToday(null);
      setFinanceState('idle');
      return;
    }

    let cancelled = false;
    setFinanceState('loading');

    const requests = [
      api.get('/intelligence/forecast-semaine')
        .then(response => { if (!cancelled) setForecast(response.data); })
        .catch(error => console.warn('Erreur forecast', error)),
      api.get('/intelligence/taux-conversion')
        .then(response => { if (!cancelled) setConversion(response.data); })
        .catch(error => console.warn('Erreur conversion', error)),
      api.get('/intelligence/projection-mensuelle')
        .then(response => { if (!cancelled) setProjection(response.data); })
        .catch(error => console.warn('Erreur projection', error)),
      api.get('/intelligence/latent-cash')
        .then(response => { if (!cancelled) setLatentCash(response.data); })
        .catch(error => console.warn('Erreur latent cash', error)),
      api.get('/stats/financial')
        .then(response => {
          if (!cancelled) {
            setFinanceToday({
              today_revenue: response.data.today_revenue ?? 0,
              month_revenue: response.data.month_revenue ?? 0,
              total_debt: response.data.total_debt ?? 0,
            });
          }
        })
        .catch(error => console.warn('Erreur finance today', error)),
    ];

    void Promise.allSettled(requests).then(results => {
      if (cancelled) return;
      const allFailed = results.every(result => result.status === 'rejected');
      setFinanceState(allFailed ? 'error' : 'ready');
    });

    return () => {
      cancelled = true;
    };
  }, [authLoading, canReadAccounting, user]);

  return {
    forecast,
    conversion,
    projection,
    latentCash,
    financeToday,
    financeState,
  };
};
