import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    host: true,
    allowedHosts: ["www.stellarstudio.app"],
    proxy: {
      '/api/v1': {
        target: 'https://api.stellarstudio.app',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path,  // Ne pas modifier le chemin
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.error('Erreur proxy:', err);
          });
        }
      },
      '/minio': {
        target: 'http://minio:9000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/minio/, '')
      }
    }
  }
})
