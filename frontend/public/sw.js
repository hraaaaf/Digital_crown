const CACHE = 'dc-mobile-v9';
const SNAPSHOT_URL = '/api/mobile/snapshot';

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

  // Routes mobiles : Cache-first (app shell)
  if (url.pathname.startsWith('/mobile/')) {
    e.respondWith(
      caches.match(e.request).then((cached) => cached || fetch(e.request))
    );
  }
});
