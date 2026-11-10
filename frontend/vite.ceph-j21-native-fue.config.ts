/** Separate FUE-only build. Never imported by the clinical frontend. */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
export default defineConfig({
  root: path.resolve(__dirname, 'fue-j21-native'),
  publicDir: false,
  plugins: [
    react(),
    {
      name: 'nonclinical-fue-removes-network-fonts',
      enforce: 'pre',
      transform(code, id) {
        if (!id.replace(/\\/g, '/').endsWith('/src/index.css')) return null
        const lines = code.split(/\r?\n/)
        const external = lines.filter(line => line.includes('fonts.googleapis.com'))
        if (external.length !== 1 || !external[0].startsWith('@import url(')) {
          throw new Error('Nonclinical FUE refuses an unknown external stylesheet configuration')
        }
        // Keep genuine source layout/styling, but NEVER request a Google Font
        // from an isolated patient-application test shell. System fonts suffice.
        return { code: lines.filter(line => !line.includes('fonts.googleapis.com')).join('\n'), map: null }
      },
    },
  ],
  base: '/__ceph_fue/',
  build: {
    outDir: path.resolve(__dirname, 'dist-ceph-j21-native-fue'),
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {host:'127.0.0.1', port:5187, strictPort:true},
})
