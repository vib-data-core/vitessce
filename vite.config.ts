import { defineConfig } from 'vite';

export default defineConfig({
  base: '/vitessce/',
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/data': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
