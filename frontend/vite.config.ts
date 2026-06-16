/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      includeAssets: ['logo.svg', 'logo.png'],
      manifest: false, // On garde le manifest.json public existant (VitePWA le prendra de public/manifest.json par défaut)
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'api-cache-get',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 jours
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkOnly',
            method: 'POST',
            options: {
              backgroundSync: {
                name: 'api-sync-post',
                options: { maxRetentionTime: 24 * 60 }
              }
            }
          },
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkOnly',
            method: 'PUT',
            options: {
              backgroundSync: {
                name: 'api-sync-put',
                options: { maxRetentionTime: 24 * 60 }
              }
            }
          },
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkOnly',
            method: 'PATCH',
            options: {
              backgroundSync: {
                name: 'api-sync-patch',
                options: { maxRetentionTime: 24 * 60 }
              }
            }
          },
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkOnly',
            method: 'DELETE',
            options: {
              backgroundSync: {
                name: 'api-sync-delete',
                options: { maxRetentionTime: 24 * 60 }
              }
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
    // HTTPS désactivé — backend en HTTP, mixed-content bloqué sinon
    // Pour réactiver : supprimer ce commentaire et ajouter les certs
    // https: { cert: fs.readFileSync('../certs/cert.pem'), key: fs.readFileSync('../certs/key.pem') },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  }
})
