// src/modules/processing/store/processingStore.js
import { defineStore } from 'pinia';
import processingService from '../services/processingService';

export const useProcessingStore = defineStore('processing', {
  state: () => ({
    currentTarget: null,
    processingParams: {
      stretch: 50,
      blackPoint: 0,
      saturation: 100,
      temperature: 0,
      denoise: 0,
      denoiseMethod: 'Gaussian'
    },
    selectedFilter: null,
    processingHistory: [],
    isProcessing: false,
    availableFilters: [],
    error: null
  }),
  
  getters: {
    canProcess: (state) => !!state.currentTarget && !!state.selectedFilter,
    hasHistory: (state) => state.processingHistory.length > 0
  },
  
  actions: {
    setCurrentTarget(targetId) {
      this.currentTarget = targetId;
      this.loadFilters(targetId);
    },
    
    async loadFilters(targetId) {
      if (!targetId) return;
      
      try {
        const response = await processingService.getTargetFilters(targetId);
        
        if (response.data && response.data.preview_urls) {
          this.availableFilters = Object.entries(response.data.preview_urls).map(([key, url]) => ({
            title: key,
            value: key,
            url: url
          }));
          
          // Sélectionner le premier filtre par défaut
          if (this.availableFilters.length > 0 && !this.selectedFilter) {
            this.selectedFilter = this.availableFilters[0].value;
          }
        }
      } catch (error) {
        console.error("Erreur lors du chargement des filtres :", error);
        this.error = "Erreur lors du chargement des filtres";
      }
    },
    
    setFilter(filter) {
      this.selectedFilter = filter;
    },
    
    updateParams(params) {
      this.processingParams = { ...params };
    },
    
    resetParams() {
      this.processingParams = {
        stretch: 50,
        blackPoint: 0,
        saturation: 100,
        temperature: 0,
        denoise: 0,
        denoiseMethod: 'Gaussian'
      };
    },
    
    async processTarget({ targetId, filter, params }) {
      if (!targetId || !filter) return;
      
      this.isProcessing = true;
      
      try {
        const payload = {
          target_id: targetId,
          filter: filter,
          params: params || this.processingParams
        };
        
        const { data } = await processingService.processImage(payload);
        
        // Ajouter à l'historique
        this.processingHistory.unshift({
          id: data.task_id,
          timestamp: new Date().toISOString(),
          targetId: targetId,
          filter: filter,
          params: { ...params || this.processingParams },
          status: 'processing'
        });
        
        return data.task_id;
      } catch (error) {
        console.error('Error processing image:', error);
        this.error = 'Erreur lors du traitement de l\'image';
        throw error;
      } finally {
        this.isProcessing = false;
      }
    },
    
    async updateTaskStatus(taskId) {
      try {
        const { data } = await processingService.getTaskStatus(taskId);
        
        // Trouver et mettre à jour la tâche dans l'historique
        const taskIndex = this.processingHistory.findIndex(task => task.id === taskId);
        if (taskIndex !== -1) {
          this.processingHistory[taskIndex] = {
            ...this.processingHistory[taskIndex],
            status: data.status,
            result: data.result
          };
        }
        
        return data;
      } catch (error) {
        console.error('Error updating task status:', error);
      }
    }
  }
});
