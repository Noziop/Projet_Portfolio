import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    host: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // On pointe directement vers le service backend
        changeOrigin: true
      }
    }
  }
})
