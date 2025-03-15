// src/services/api/apiClient.js
import axios from 'axios'

// On garde ton URL relative pour que le proxy fonctionne
const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 10000
})

// L'injection du token se fera dans un middleware d'authentification
// qui utilisera le store ou localStorage selon le contexte
const injectAuthToken = (config) => {
  // Cette fonction sera importée ailleurs
  // mais le client API lui-même ne dépend pas directement du store
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}

apiClient.interceptors.request.use(injectAuthToken);

// Ajout de la gestion des erreurs
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // On pourrait émettre un événement ici
      // ou utiliser un gestionnaire d'erreurs centralisé
      console.error('Session expirée');
      // Redirection vers la page de login
    }
    return Promise.reject(error);
  }
);

export default apiClient;
