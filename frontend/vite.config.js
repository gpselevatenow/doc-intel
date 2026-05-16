import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
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
