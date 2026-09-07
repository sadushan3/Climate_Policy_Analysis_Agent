import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // `@vitejs/plugin-react` was declared as a dependency but never registered,
  // so JSX was never actually transformed by the configured pipeline.
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Dev requests go through Vite, so the browser sees one origin and CORS
      // never enters the picture locally.
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: true },
})
