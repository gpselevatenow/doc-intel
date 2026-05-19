import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5179,
    strictPort: true,
    proxy: { '/api': 'http://localhost:8006' }
  },
  optimizeDeps: {
    include: ['framer-motion', '@react-pdf-viewer/search'],
    force: true
  },
  resolve: {
    dedupe: ['framer-motion', 'react', 'react-dom']
  },
  server: {
    port: 5173,
    strictPort: true,
  }
})
