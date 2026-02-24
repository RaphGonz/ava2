import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 3000,
    proxy: {
      // Proxy API calls to FastAPI backend (avoids CORS in dev)
      '/auth': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/preferences': 'http://localhost:8000',
      '/avatars': 'http://localhost:8000',
      '/photos': 'http://localhost:8000',
    },
  },
})
