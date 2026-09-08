import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    allowedHosts: ['localhost'],
    proxy: { '/api': { target: process.env.BASE_DEV_API ?? 'http://127.0.0.1:8000' } },
  },
  build: { sourcemap: false, target: 'es2022', chunkSizeWarningLimit: 1200 },
  test: { environment: 'jsdom', environmentOptions: { jsdom: { url: 'http://localhost' } }, include: ['src/**/*.test.ts', 'src/**/*.test.tsx'], setupFiles: ['src/test/setup.ts'] },
})
