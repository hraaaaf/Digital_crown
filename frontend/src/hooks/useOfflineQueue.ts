import { useState, useEffect, useCallback } from 'react';

export interface OfflineAction {
  id: number;
  url: string;
  method: string;
  timestamp: number;
}

export const useOfflineQueue = () => {
  const [queue, setQueue] = useState<OfflineAction[]>([]);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  const fetchQueue = useCallback(async () => {
    try {
      // Workbox Background Sync uses IndexedDB under 'workbox-background-sync'
      const request = indexedDB.open('workbox-background-sync');

      request.onsuccess = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // Ensure the store exists
        if (!db.objectStoreNames.contains('requests')) {
          setQueue([]);
          return;
        }

        const transaction = db.transaction('requests', 'readonly');
        const store = transaction.objectStore('requests');
        const getAllRequest = store.getAll();

        getAllRequest.onsuccess = () => {
          const results = getAllRequest.result;
          if (results && results.length > 0) {
            // results are typically { queueName, requestData: { url, method, headers, ... }, timestamp }
            const actions = results.map((r: any, index: number) => ({
              id: index,
              url: r.requestData?.url || r.storableRequest?.url || 'URL inconnue',
              method: r.requestData?.method || r.storableRequest?.method || 'Action',
              timestamp: r.timestamp || Date.now(),
            }));
            setQueue(actions);
          } else {
            setQueue([]);
          }
        };
      };

      request.onerror = () => {
        console.warn('Erreur lecture IndexedDB pour Offline Queue');
      };
    } catch (e) {
      console.warn('Background sync not fully supported or accessible.', e);
    }
  }, []);

  useEffect(() => {
    fetchQueue();

    // Set intervals to check queue when offline
    let intervalId: any = null;

    const handleOffline = () => {
      setIsOffline(true);
      fetchQueue();
      intervalId = setInterval(fetchQueue, 5000);
    };

    const handleOnline = () => {
      setIsOffline(false);
      // Wait a bit for sync to happen, then fetch
      setTimeout(fetchQueue, 2000);
      setTimeout(fetchQueue, 5000);
      if (intervalId) clearInterval(intervalId);
    };

    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);

    if (isOffline) {
      intervalId = setInterval(fetchQueue, 5000);
    }

    return () => {
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('online', handleOnline);
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchQueue, isOffline]);

  return { queue, isOffline, refreshQueue: fetchQueue };
};
