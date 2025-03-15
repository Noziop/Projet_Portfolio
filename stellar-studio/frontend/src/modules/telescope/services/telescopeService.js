// src/modules/telescope/services/telescopeService.js
import apiClient from '@/services/api';

export default {
  // Obtenir tous les télescopes
  async getTelescopes(status = 'online') {
    return apiClient.get(`/telescopes/?status=${status}`);
  },
  
  // Obtenir un télescope spécifique
  async getTelescopeById(id) {
    return apiClient.get(`/telescopes/${id}`);
  },
  
  // Obtenir les cibles disponibles pour un télescope
  async getTargets(telescopeId) {
    return apiClient.get(`/targets/?telescope_id=${telescopeId}`);
  },
  
  // Obtenir les détails d'une cible
  async getTargetById(targetId) {
    return apiClient.get(`/targets/${targetId}`);
  },
  
  // Obtenir l'image d'une cible
  async getTargetImage(targetId) {
    return apiClient.get(`/targets/${targetId}/image`);
  }
};
