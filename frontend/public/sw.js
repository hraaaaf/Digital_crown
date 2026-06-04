const CACHE = 'dc-mobile-v10';
const SNAPSHOT_URL = '/api/mobile/snapshot';

// --- UTILITAIRES INDEXEDDB POUR LA SYNCHRONISATION HORS-LIGNE ---
const DB_NAME = 'sync-db';
const STORE_NAME = 'sync-store';

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (e) => {
      e.target.result.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function saveRequestToDB(url, method, headers, body) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const requestItem = { url, method, headers, body, timestamp: Date.now() };
    store.add(requestItem);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function getRequestsFromDB() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function clearRequestFromDB(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    store.delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

// Rejoue les requêtes en attente
async function syncOfflineRequests() {
  const requests = await getRequestsFromDB();
  for (const req of requests) {
    try {
      await fetch(req.url, {
        method: req.method,
        headers: req.headers,
        body: req.body
      });
      await clearRequestFromDB(req.id);
    } catch (err) {
      console.error('Erreur lors de la synchronisation de la requête:', err);
      // S'il y a encore une erreur de réseau, on arrête et on réessayera plus tard
      break; 
    }
  }
}

// Événement Background Sync déclenché par le navigateur au retour de la connexion
self.addEventListener('sync', (e) => {
  if (e.tag === 'sync-mobile-actions') {
    e.waitUntil(syncOfflineRequests());
  }
});

// Cache les assets statiques de l'app mobile à l'installation
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      c.addAll(['/mobile/onboarding', '/mobile/dashboard'])
    ).catch(() => null)
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Snapshot API : Network-first, fallback cache
  if (url.pathname === SNAPSHOT_URL) {
    e.respondWith(
      fetch(e.request.clone())
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(SNAPSHOT_URL, clone));
          }
          return res;
        })
        .catch(() => caches.match(SNAPSHOT_URL))
    );
    return;
  }

  // Intercepter les actions (POST/PUT) pour le mode hors-ligne
  if (e.request.method !== 'GET' && url.pathname.includes('/api/mobile/')) {
    e.respondWith((async () => {
      try {
        return await fetch(e.request.clone());
      } catch (err) {
        // En cas d'échec réseau (hors ligne), on sauvegarde dans IndexedDB
        const clonedReq = e.request.clone();
        
        // Extraire les headers
        const headers = {};
        for (const [key, value] of clonedReq.headers.entries()) {
          headers[key] = value;
        }

        // Extraire le body (on assume du texte ou JSON pour les actions API)
        const bodyText = await clonedReq.text();

        await saveRequestToDB(clonedReq.url, clonedReq.method, headers, bodyText);

        // Tenter d'enregistrer le background sync si supporté par le navigateur
        if ('sync' in self.registration) {
          try {
            await self.registration.sync.register('sync-mobile-actions');
          } catch (syncErr) {
            console.error('Erreur register sync:', syncErr);
          }
        }

        // Retourner une réponse mockée pour ne pas faire crasher l'UI
        return new Response(JSON.stringify({ status: 'queued_offline', signed: true }), {
          headers: { 'Content-Type': 'application/json' },
          status: 202
        });
      }
    })());
    return;
  }

  // Routes mobiles : Cache-first (app shell)
  if (url.pathname.startsWith('/mobile/')) {
    e.respondWith(
      caches.match(e.request).then((cached) => cached || fetch(e.request))
    );
  }
});

// Listener pour déclencher le sync manuellement depuis le Frontend (Safari fallback)
self.addEventListener('message', (e) => {
  if (e.data === 'force-sync') {
    e.waitUntil(syncOfflineRequests());
  }
});
