<template>
  <v-card>
    <v-card-title>Select Target</v-card-title>
    <v-card-text>
      <v-select
        v-model="selectedTelescope"
        :items="telescopes"
        label="Select Telescope"
        item-title="name"
        item-value="id"
        @update:model-value="loadTargets"
        :loading="loadingTelescopes"
        :disabled="loadingTelescopes"
      ></v-select>

      <v-select
        v-model="selectedTarget"
        :items="availableTargets"
        label="Select Target"
        item-title="name"
        item-value="id"
        @update:model-value="loadPresets"
        :disabled="!selectedTelescope || loading"
        :loading="loading"
      ></v-select>

      <v-select
        v-model="selectedPreset"
        :items="availablePresets"
        label="Select Preset"
        item-title="name"
        item-value="id"
        :disabled="!selectedTarget || loadingPresets"
        :loading="loadingPresets"
      ></v-select>

      <v-btn
        block
        color="primary"
        :disabled="!selectedTarget || !selectedPreset"
        :loading="downloadLoading"
        @click="downloadFits"
      >
        Download FITS
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import apiClient from '../services/api'
import websocketService, { createWebSocket } from '../services/websocket'
import previewService from '../services/previewService';

export default {
  name: 'ObjectSelector',
  
  setup(props, { emit }) {
    const selectedTelescope = ref(null)
    const selectedTarget = ref(null)
    const selectedPreset = ref(null)
    const availableTargets = ref([])
    const telescopes = ref([])
    const availablePresets = ref([])
    const loading = ref(false)
    const loadingTelescopes = ref(false)
    const loadingPresets = ref(false)
    const downloadLoading = ref(false)
    const downloadStatus = ref('idle') // 'idle', 'downloading', 'success', 'error'
    const currentTaskId = ref(null)

    // Gestionnaire pour les messages WebSocket - avec sécurité
    const handleWebSocketMessage = (data) => {
      try {
        console.log('Message WebSocket reçu dans ObjectSelector:', data);
        
        // Vérifier si c'est bien un objet avec les propriétés attendues
        if (!data || typeof data !== 'object') return;
        
        // Vérifier si le message concerne la tâche en cours
        if (data.task_id === currentTaskId.value) {
          if (data.type === 'download_progress') {
            // Message de progression
            emit('download-progress', {
              status: 'progress',
              progress: data.progress,
              message: data.message
            });
          } else if (data.type === 'download_complete') {
            // Téléchargement terminé
            downloadStatus.value = 'success';
            emit('download-complete', {
              target_id: selectedTarget.value,
              files: data.files || [],
              message: data.message
            });
          }
        }
      } catch (error) {
        console.error('Erreur lors du traitement du message WebSocket:', error);
      }
    };

    // Récupération des télescopes disponibles depuis l'API
    const loadTelescopes = async () => {
      loadingTelescopes.value = true
      try {
        console.log("Tentative de récupération des télescopes via:", apiClient.defaults.baseURL);
        
        // Utiliser le proxy correctement avec une URL relative
        const url = '/telescopes/';
        
        const response = await apiClient.get(url, { 
          params: { status: 'online' }
        })
        telescopes.value = response.data
        console.log("Télescopes récupérés:", response.data);
        
        // Si aucun télescope n'est sélectionné mais qu'on a des télescopes disponibles
        if (!selectedTelescope.value && telescopes.value.length > 0) {
          selectedTelescope.value = telescopes.value[0].id
          loadTargets() // Charger les cibles pour le premier télescope
        }
      } catch (error) {
        console.error('Échec du chargement des télescopes:', error);
        
        if (error.message && error.message.includes('Mixed Content')) {
          console.error('Erreur de mixed content détectée - problème avec HTTPS');
        }
        
        emit('error', 'Échec du chargement des télescopes');
        // Utilisation de valeurs par défaut en cas d'erreur
        telescopes.value = [
          { id: 'HST', name: 'Hubble Space Telescope' },
          { id: 'JWST', name: 'James Webb Space Telescope' }
        ]
      } finally {
        loadingTelescopes.value = false
      }
    }

    const loadTargets = async () => {
      if (!selectedTelescope.value) return
      
      loading.value = true
      selectedTarget.value = null // Réinitialiser la cible sélectionnée
      
      try {
        console.log(`Chargement des cibles pour le télescope ${selectedTelescope.value}`);
        
        // Essayer avec différentes variantes de paramètres pour résoudre le problème de filtrage
        const params = {
          telescope_id: selectedTelescope.value,
        };
        
        console.log("Paramètres de requête:", params);
        
        const response = await apiClient.get(`/targets/`, { params })
        
        console.log("Réponse brute:", response);
        console.log("Cibles récupérées:", response.data);
        console.log("Nombre de cibles:", response.data.length);
        
        // Filtrer côté client si le backend ne le fait pas correctement
        const filteredTargets = response.data.filter(target => {
          // On vérifie si le target possède une propriété telescope qui correspond
          return target.telescope === selectedTelescope.value || 
                 target.telescope_id === selectedTelescope.value;
        });
        
        console.log("Nombre de cibles après filtrage client:", filteredTargets.length);
        
        // Utiliser les cibles filtrées si le nombre est différent (ce qui indiquerait un problème de filtrage backend)
        if (filteredTargets.length !== response.data.length && filteredTargets.length > 0) {
          console.log("Filtrage appliqué côté client car le backend ne filtre pas correctement");
          availableTargets.value = filteredTargets;
        } else {
          availableTargets.value = response.data;
        }
      } catch (error) {
        console.error('Échec du chargement des cibles:', error);
        
        if (error.message && error.message.includes('Mixed Content')) {
          console.error('Erreur de mixed content détectée lors du chargement des cibles - problème avec HTTPS');
        }
        
        emit('error', 'Échec du chargement des cibles')
        availableTargets.value = []
      } finally {
        loading.value = false
      }
      
      // Réinitialiser le preset quand on change de cible
      selectedPreset.value = null
    }

    const loadPresets = async () => {
      if (!selectedTarget.value) return
      
      loadingPresets.value = true
      selectedPreset.value = null
      
      try {
        console.log(`Chargement des presets disponibles`);
        
        const response = await apiClient.get(`/presets/`)
        console.log("Presets récupérés:", response.data);
        
        availablePresets.value = response.data;
        
        // Sélectionner le premier preset par défaut si disponible
        if (availablePresets.value.length > 0) {
          selectedPreset.value = availablePresets.value[0].id;
        }
      } catch (error) {
        console.error('Échec du chargement des presets:', error);
        emit('error', 'Échec du chargement des presets')
        availablePresets.value = []
      } finally {
        loadingPresets.value = false
      }
    }

    const downloadFits = async () => {
      if (!selectedTarget.value || !selectedTelescope.value || !selectedPreset.value) return

      downloadLoading.value = true
      downloadStatus.value = 'downloading'
      
      try {    
        // Sauvegarder immédiatement le target_id (généralement c'est le catalogId)
        previewService.setCurrentTargetId(selectedTarget.value);
        // Trouver le target sélectionné pour avoir son nom pour les logs
        const target = availableTargets.value.find(t => t.id === selectedTarget.value)
        
        // API mise à jour pour correspondre à l'attente du backend
        const response = await apiClient.post(`/tasks/download`, {
          target_id: selectedTarget.value,
          preset_id: selectedPreset.value,
          telescope_id: selectedTelescope.value
        })
        
        // Stocker l'ID de la tâche en cours
        currentTaskId.value = response.data.task_id;
        
        // Lors du téléchargement, émettre l'événement avec toutes les informations nécessaires
        emit('download-started', {
          taskId: response.data.task_id,
          message: target.name || target.id,
          // Ajouter d'autres informations utiles ici
        })
        
        // Garder le monitoring par polling comme fallback
        monitorDownload(response.data.task_id)
      } catch (error) {
        console.error('Échec du démarrage du téléchargement:', error)
        emit('error', 'Échec du démarrage du téléchargement')
        downloadStatus.value = 'error'
      } finally {
        downloadLoading.value = false
      }
    }

    const monitorDownload = async (taskId) => {
      const checkStatus = async () => {
        try {
          const response = await apiClient.get(`/tasks/${taskId}`)
          console.log("Statut de la tâche:", response.data)
          
          // Extraction des informations utiles
          const status = response.data.status
          const progressInfo = response.data.error || response.data.result?.message || ''
          
          // Gestion des différents états
          if (status === 'COMPLETED') {
            downloadStatus.value = 'success'
            
            // Ne pas émettre download-complete ici, le polling dans Processing.vue s'en occupe
            // avec les informations correctes sur le nombre de fichiers
            
            return true
          } else if (status === 'FAILED') {
            downloadStatus.value = 'error'
            emit('error', progressInfo || 'Échec du téléchargement')
            return true
          } else if (status === 'RUNNING' || status === 'PENDING') {
            // Extraire le progrès du message d'erreur (qui contient en fait l'état d'avancement)
            let progressMessage = progressInfo
            let progressValue = 0
            
            // Analyse du message de progression "(X/Y)"
            const progressMatch = /\((\d+)\/(\d+)\)/.exec(progressInfo)
            if (progressMatch) {
              const [_, current, total] = progressMatch
              progressValue = (parseInt(current) / parseInt(total)) * 100
              progressMessage = `Téléchargement des fichiers ${current}/${total} (${progressValue.toFixed(0)}%)`
            }
            
            emit('download-progress', {
              status: 'progress',
              progress: progressValue,
              message: progressMessage
            })
          }
          return false
        } catch (error) {
          console.error('Échec de la vérification du statut:', error)
          // Ne pas considérer une erreur réseau comme une erreur définitive
          emit('download-progress', {
            status: 'progress',
            message: 'Vérification du statut en cours...'
          })
          return false // Continuer à vérifier
        }
      }

      // Vérifier immédiatement la première fois
      checkStatus()
      
      // Puis vérifier toutes les 5 secondes
      const interval = setInterval(async () => {
        const done = await checkStatus()
        if (done) clearInterval(interval)
      }, 5000) // Augmenté à 5 secondes pour réduire le nombre de requêtes au serveur
      
      // Ne pas définir de timeout - laisser le téléchargement se terminer naturellement
      // Le téléchargement peut prendre un temps considérable selon la cible
    }

    // Charger les télescopes au montage du composant
    onMounted(() => {
      loadTelescopes()
      
      // Les WebSockets sont désactivés, mais on garde le code au cas où on en aurait besoin plus tard
      try {
        // Ajouter l'écouteur mais sans activer les WebSockets
        websocketService.addListener('processing_update', handleWebSocketMessage);
        console.log('Écouteur WebSocket enregistré (mode désactivé)');
      } catch (error) {
        console.error('Erreur lors de l\'initialisation WebSocket:', error);
      }
    })
    
    // Nettoyer les écouteurs WebSocket à la destruction du composant
    onUnmounted(() => {
      try {
        websocketService.removeListener('processing_update', handleWebSocketMessage);
        console.log('Écouteur WebSocket supprimé');
      } catch (error) {
        console.error('Erreur lors du nettoyage WebSocket:', error);
      }
    })

    return {
      selectedTelescope,
      selectedTarget,
      selectedPreset,
      telescopes,
      availableTargets,
      availablePresets,
      loading,
      loadingTelescopes,
      loadingPresets,
      downloadLoading,
      downloadStatus,
      loadTargets,
      loadPresets,
      downloadFits
    }
  }
}
</script>