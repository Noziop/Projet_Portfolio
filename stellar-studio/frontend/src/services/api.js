// src/services/api.js
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

// Utiliser une URL relative plutôt qu'une URL absolue pour éviter le problème de mixed content
// Le proxy dans vite.config.js s'occupera de rediriger correctement
const API_BASE_URL = '/api/v1';

console.log('Configuration du client API avec baseURL relative:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
  
  // Débogage pour vérifier les URL construites
  console.log('Requête API vers:', window.location.origin + config.baseURL + config.url);
  
  return config
})

export default apiClient
