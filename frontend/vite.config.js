import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/conversations': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/memories': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/episodes': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
