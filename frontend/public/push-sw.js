/* Digital Crown M6-D2: fixed generic OS signal only. Never render push payload content. */
self.addEventListener('push', event => {
  const title = 'Digital Crown';
  const body = 'De nouvelles alertes sont disponibles. Ouvrez l\'application pour les consulter.';
  const url = '/mobile/dashboard';

  event.waitUntil(self.registration.showNotification(title, {
    body,
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: 'digital-crown-alerts',
    renotify: true,
    data: { url },
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = event.notification?.data?.url || '/mobile/dashboard';
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of windows) {
      if ('navigate' in client) await client.navigate(target);
      if ('focus' in client) return client.focus();
    }
    return self.clients.openWindow(target);
  })());
});
