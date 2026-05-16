import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5178,
    strictPort: true,
    proxy: { '/api': 'http://localhost:8005' }
  },
  optimizeDeps: {
    include: ['framer-motion', '@react-pdf-viewer/search'],
    force: true
  },
  resolve: {
    dedupe: ['framer-motion', 'react', 'react-dom']
  }
})
