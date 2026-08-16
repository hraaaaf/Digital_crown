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

    const request = async (
      run: () => Promise<void>,
      label: string,
    ): Promise<boolean> => {
      try {
        await run();
        return true;
      } catch (error) {
        console.warn(label, error);
        return false;
      }
    };

    const requests = [
      request(async () => {
        const response = await api.get('/intelligence/forecast-semaine');
        if (!cancelled) setForecast(response.data);
      }, 'Erreur forecast'),
      request(async () => {
        const response = await api.get('/intelligence/taux-conversion');
        if (!cancelled) setConversion(response.data);
      }, 'Erreur conversion'),
      request(async () => {
        const response = await api.get('/intelligence/projection-mensuelle');
        if (!cancelled) setProjection(response.data);
      }, 'Erreur projection'),
      request(async () => {
        const response = await api.get('/intelligence/latent-cash');
        if (!cancelled) setLatentCash(response.data);
      }, 'Erreur latent cash'),
      request(async () => {
        const response = await api.get('/stats/financial');
        if (!cancelled) {
          setFinanceToday({
            today_revenue: response.data.today_revenue ?? 0,
            month_revenue: response.data.month_revenue ?? 0,
            total_debt: response.data.total_debt ?? 0,
          });
        }
      }, 'Erreur finance today'),
    ];

    void Promise.all(requests).then(results => {
      if (cancelled) return;
      setFinanceState(results.some(Boolean) ? 'ready' : 'error');
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
