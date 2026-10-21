import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Isolated screenshot harness: no PWA service worker, no PWA service worker; scan the actual fixture at startup to reduce
// late dependency re-optimisation during a viewport switch. Production Vite config
// remains unchanged.
export default defineConfig({
  plugins: [react()],
  // Scan the fixture entry up-front; allow Vite to optimize nested CommonJS deps.
  optimizeDeps: { entries: ['lot05-j10d-manual-visual.html'] },
  server: {
    host: '127.0.0.1',
    port: 5199,
    strictPort: true,
  },
});
