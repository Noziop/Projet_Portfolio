// src/modules/processing/services/processingService.js
import apiClient from '@/services/api';

export default {
  async getPresets() {
    return apiClient.get('/presets/');
  },
  
  async processImage(payload) {
    return apiClient.post('/tasks/process', payload);
  },

  async getTargetFilters(targetId) {
    return apiClient.get(`/targets/${targetId}/preview`);
  },  
  
  async getTaskStatus(taskId) {
    return apiClient.get(`/tasks/${taskId}`);
  }
};
