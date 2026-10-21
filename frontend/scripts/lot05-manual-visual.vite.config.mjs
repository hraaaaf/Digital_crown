import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Isolated screenshot harness: no PWA service worker, no dependency-discovery
// re-optimisation reload after a viewport switch. Production Vite config
// remains unchanged.
export default defineConfig({
  plugins: [react()],
  optimizeDeps: { noDiscovery: true },
  server: {
    host: '127.0.0.1',
    port: 5199,
    strictPort: true,
  },
});
