/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

import { VitePWA } from 'vite-plugin-pwa'

const certPath = path.resolve(__dirname, '../certs/cert.pem')
const keyPath = path.resolve(__dirname, '../certs/key.pem')
const enableHttps = process.env.VITE_ENABLE_HTTPS === 'true'
const httpsConfig = enableHttps && fs.existsSync(certPath) && fs.existsSync(keyPath)
  ? {
      cert: fs.readFileSync(certPath),
      key: fs.readFileSync(keyPath),
    }
  : undefined

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      filename: 'pwa-sw.js', // Nom distinct pour ne pas écraser public/sw.js (mobile custom SW)
      includeAssets: ['logo.svg', 'logo.png'],
      manifest: false, // Utilise public/manifest.json
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        // Pas de BackgroundSync Workbox : la file offline est gérée par MobileStorage (localforage)
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/mobile\/snapshot.*/i,
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'api-snapshot-cache',
              expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [0, 200] }
            }
          }
        ]
      }
    })
  ],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    https: httpsConfig,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  }
})
