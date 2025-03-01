// src/services/api.js
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const apiClient = axios.create({
  baseURL: 'https://api.stellarstudio.fassih.ch/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Ajouter un intercepteur pour injecter le token dans chaque requête
apiClient.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  const token = authStore.token
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  return config
})

export default apiClient
