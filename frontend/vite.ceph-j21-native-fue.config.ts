/** Separate FUE-only build. Never imported by the clinical frontend. */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
export default defineConfig({
  root: path.resolve(__dirname, 'fue-j21-native'),
  publicDir: false,
  plugins: [react()],
  base: '/__ceph_fue/',
  build: {
    outDir: path.resolve(__dirname, 'dist-ceph-j21-native-fue'),
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {host:'127.0.0.1', port:5187, strictPort:true},
})
