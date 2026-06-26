import { useState, useEffect, useCallback } from 'react';
import { MobileStorage } from '../services/zka/MobileStorage';

export interface OfflineAction {
  id: string;
  url: string;
  method: string;
  timestamp: number;
}

export const useOfflineQueue = () => {
  const [queue, setQueue] = useState<OfflineAction[]>([]);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  const fetchQueue = useCallback(async () => {
    try {
      const actions = await MobileStorage.getActionQueue();
      setQueue(actions.map(a => ({
        id: a.id,
        url: a.url,
        method: a.method,
        timestamp: a.timestamp,
      })));
    } catch {
      setQueue([]);
    }
  }, []);

  useEffect(() => {
    fetchQueue();

    let intervalId: ReturnType<typeof setInterval> | null = null;

    const handleOffline = () => {
      setIsOffline(true);
      fetchQueue();
      intervalId = setInterval(fetchQueue, 5000);
    };

    const handleOnline = () => {
      setIsOffline(false);
      setTimeout(fetchQueue, 2000);
      if (intervalId) clearInterval(intervalId);
    };

    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);

    if (!navigator.onLine) {
      intervalId = setInterval(fetchQueue, 5000);
    }

    return () => {
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('online', handleOnline);
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchQueue]);

  return { queue, isOffline, refreshQueue: fetchQueue };
};
