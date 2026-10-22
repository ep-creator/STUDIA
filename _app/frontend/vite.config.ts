/// <reference types="vitest/config" />
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig, type ProxyOptions } from 'vite'

// O motor só aceita escritas vindas da própria origem: o proxy de desenvolvimento se apresenta como ela,
// sem afrouxar a proteção do motor.
const MOTOR = 'http://127.0.0.1:8790'
const paraOMotor: ProxyOptions = {
  target: MOTOR,
  changeOrigin: true,
  configure: (proxy) => {
    proxy.on('proxyReq', (req) => req.setHeader('origin', MOTOR))
  },
}

export default defineConfig({
  plugins: [svelte()],
  server: { proxy: { '/api': paraOMotor, '/arquivos': paraOMotor } },
  resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'],
    setupFiles: ['src/teste-setup.ts'],
  },
})
