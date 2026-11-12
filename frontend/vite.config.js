import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// При разработке (npm run dev) запросы к backend идут через прокси.
// В Docker то же самое делает nginx.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
    },
  },
})
