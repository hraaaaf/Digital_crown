import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
export default defineConfig({plugins:[react()],build:{rollupOptions:{input:resolve(process.cwd(),'command-target.html')},outDir:'dist-command-target',emptyOutDir:true},server:{host:'127.0.0.1',port:5193,strictPort:true}});
