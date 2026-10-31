import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import fs from 'node:fs';
import { resolve } from 'node:path';

const projectRoot = import.meta.dirname;
const vaultAvatarGlb = resolve(
  projectRoot,
  '../../vault/01_Wiki/Projects/ZacharyPortfolio/03_Design/stitch_assets/models/Asian_M_3_Busi.glb'
);
const publicModelsDir = resolve(projectRoot, 'public/models');

function ensureAvatarModelsSynced(): void {
  try {
    fs.mkdirSync(publicModelsDir, { recursive: true });

    // Ensure rigged fallback avatar is synced from vault if not present in public
    if (fs.existsSync(vaultAvatarGlb)) {
      const asianBusi = resolve(publicModelsDir, 'Asian_M_3_Busi.glb');
      if (!fs.existsSync(asianBusi) || fs.statSync(asianBusi).size < 100000) {
        fs.copyFileSync(vaultAvatarGlb, asianBusi);
      }
    }
  } catch (e) {
    console.error('[Avatar Sync ERROR]', e);
  }
}

ensureAvatarModelsSynced();

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
