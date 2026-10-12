import { mergeConfig } from 'vite';
import base from './vite.config';

// Isolated Actions-only phone link. The browser and both runner actors use one
// temporary HTTPS origin; only the FastAPI backend owns /api and /field-lab.
export default mergeConfig(base, {
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/api': { target: 'http://127.0.0.1:8005', changeOrigin: true },
      '/field-lab': { target: 'http://127.0.0.1:8005', changeOrigin: true },
    },
  },
});
