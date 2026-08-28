import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary.tsx'
import { MobilePreviewDashboard } from './features/mobile/Dashboard/MobilePreviewDashboard.tsx'
import './index.css'
import './styles/mobileGlassSystem.css'
import * as Sentry from '@sentry/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { registerSW } from 'virtual:pwa-register'

const previewParams = new URLSearchParams(window.location.search)
const isDedicatedPreviewBuild = import.meta.env.VITE_DC_PREVIEW_DEMO === '1'
const isPreviewDemo = isDedicatedPreviewBuild
  && window.location.hostname.endsWith('.vercel.app')
  && window.location.pathname === '/mobile/demo'
  && previewParams.get('demo') === '1'

if (isPreviewDemo) {
  const policy = document.createElement('meta')
  policy.httpEquiv = 'Content-Security-Policy'
  policy.content = "connect-src 'none'; form-action 'none'"
  policy.dataset.dcPreviewIsolation = 'true'
  document.head.appendChild(policy)
}

if (!isPreviewDemo && import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  })
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

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

if (!isPreviewDemo && 'serviceWorker' in navigator) {
  void migrateLegacyMobileOfflineState().then((ready) => {
    if (!ready) return
    registerSW({ immediate: true })
  })
}

async function resolveApplication(): Promise<React.ReactNode> {
  if (isPreviewDemo) {
    return <BrowserRouter><MobilePreviewDashboard /></BrowserRouter>
  }

  const { default: App } = await import('./App.tsx')
  return <App />
}

async function bootstrap() {
  const application = await resolveApplication()
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          {application}
        </QueryClientProvider>
      </ErrorBoundary>
    </React.StrictMode>,
  )
}

void bootstrap()
