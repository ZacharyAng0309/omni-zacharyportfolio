import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';

const projectRoot = import.meta.dirname;

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  optimizeDeps: {
    include: ['three'],
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(projectRoot, 'index.html'),
      },
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/three')) {
            return 'three';
          }
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react';
          }
          if (id.includes('node_modules/lucide-react')) {
            return 'lucide';
          }
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
