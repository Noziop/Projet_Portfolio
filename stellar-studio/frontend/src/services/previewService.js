// src/services/previewService.js
import axios from 'axios';

const previewService = {
  // Cache pour éviter les appels multiples
  _cache: {},
  
  // Stocker le target_id courant
  _currentTargetId: null,
  
  // Définir le target_id actif
  setCurrentTargetId(targetId) {
    console.log('✨ Target ID défini:', targetId);
    this._currentTargetId = targetId;
    // Stocker aussi dans localStorage comme solution de secours
    localStorage.setItem('stellarStudio_currentTargetId', targetId);
  },
  
  // Récupérer le target_id actif
  getCurrentTargetId() {
    // Si on a déjà un ID en mémoire, l'utiliser
    if (this._currentTargetId) return this._currentTargetId;
    
    // Sinon, essayer de le récupérer du localStorage
    const savedId = localStorage.getItem('stellarStudio_currentTargetId');
    if (savedId) {
      this._currentTargetId = savedId;
      return savedId;
    }
    
    return null;
  },
  
  // Charger les previews pour un target
  async loadPreviews(targetId) {
    // Utiliser l'ID fourni ou l'ID courant
    const idToUse = targetId || this.getCurrentTargetId();
    
    if (!idToUse) {
      console.error('❌ Aucun target_id disponible pour charger les previews');
      return null;
    }
    
    // Utiliser le cache si disponible
    if (this._cache[idToUse]) {
      return this._cache[idToUse];
    }
    
    try {
      const token = localStorage.getItem('token');
      console.log('🔍 Chargement des previews pour:', idToUse);
      
      const response = await axios.get(`/api/v1/targets/${idToUse}/preview`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('📊 Réponse preview reçue:', response.data);
      
      if (!response.data || !response.data.preview_urls) {
        throw new Error('Structure de réponse API invalide');
      }
      
      // Transformer les données pour l'UI
      const result = {
        previewUrls: response.data.preview_urls,
        filters: Object.entries(response.data.preview_urls).map(([key, url]) => ({
          title: key,
          value: key,
          url: url
        }))
      };
      
      // Sauvegarder dans le cache
      this._cache[idToUse] = result;
      
      return result;
    } catch (error) {
      console.error('❌ Erreur lors du chargement des previews:', error);
      return null;
    }
  }
};

export default previewService;
