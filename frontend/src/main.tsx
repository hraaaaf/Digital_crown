import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { ErrorBoundary } from './components/ErrorBoundary.tsx'
import './index.css' // <--- VERIFIE BIEN CETTE LIGNE
import * as Sentry from "@sentry/react";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

import { registerSW } from 'virtual:pwa-register'

const LEGACY_SW_RELOAD_KEY = 'dc_m62_legacy_sw_reload'

function isLegacyMobileWorker(worker: ServiceWorker | null): boolean {
  if (!worker) return false
  try {
    return new URL(worker.scriptURL).pathname === '/sw.js'
  } catch {
    return worker.scriptURL.endsWith('/sw.js')
  }
}

async function deleteLegacySyncDb(): Promise<void> {
  if (!('indexedDB' in window)) return
  await new Promise<void>((resolve) => {
    const request = indexedDB.deleteDatabase('sync-db')
    request.onsuccess = () => resolve()
    request.onerror = () => resolve()
    // Un ancien worker encore vivant peut garder une connexion ouverte pendant
    // quelques instants. La suppression reste demandée et se terminera à sa fermeture.
    request.onblocked = () => resolve()
  })
}

async function migrateLegacyMobileOfflineState(): Promise<boolean> {
  const legacyController = isLegacyMobileWorker(navigator.serviceWorker.controller)

  try {
    const registrations = await navigator.serviceWorker.getRegistrations()
    const legacyRegistrations = registrations.filter((registration) =>
      [registration.installing, registration.waiting, registration.active].some(isLegacyMobileWorker)
    )
    await Promise.all(legacyRegistrations.map((registration) => registration.unregister()))
  } catch { /* best effort: le nouveau Workbox remplacera le scope */ }

  try {
    if ('caches' in window) await caches.delete('dc-mobile-v10')
  } catch { /* cache legacy non accessible */ }
  await deleteLegacySyncDb().catch(() => undefined)

  if (legacyController) {
    try {
      if (sessionStorage.getItem(LEGACY_SW_RELOAD_KEY) !== '1') {
        sessionStorage.setItem(LEGACY_SW_RELOAD_KEY, '1')
        window.location.reload()
        return false
      }
    } catch { /* sessionStorage indisponible: ne jamais bloquer le nouveau SW */ }
  }

  try { sessionStorage.removeItem(LEGACY_SW_RELOAD_KEY) } catch { /* ignore */ }
  return true
}

if ('serviceWorker' in navigator) {
  void migrateLegacyMobileOfflineState().then((ready) => {
    if (!ready) return
    // Un seul Service Worker Workbox pour le shell statique. Les données métier
    // et mutations offline restent exclusivement dans MobileStorage.
    registerSW({ immediate: true })
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
