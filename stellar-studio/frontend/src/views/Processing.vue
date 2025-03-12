<template>
  <default-layout>
    <v-container fluid>
      <v-row>
        <!-- Panneau de gauche : Sélection et contrôles -->
        <v-col cols="12" md="3">
          <v-row>
            <v-col cols="12">
              <object-selector
                @download-started="handleDownloadStarted"
                @download-complete="handleDownloadComplete"
                @download-progress="handleDownloadProgress"
                @error="handleError"
              />
            </v-col>
            <v-col cols="12">
              <processing-controls
                :targetId="currentTargetId"
                :presetId="selectedPresetId"
                :availableFilters="filteredAvailableFilters"
                :processingEnabled="downloadCompleted"
                @filter-selected="handleFilterSelected"
                ref="processingControls"
                @process="handleProcessing"
              />
            </v-col>
          </v-row>
        </v-col>

        <!-- Zone principale : Visualisation -->
        <v-col cols="12" md="9">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              Image Workspace
              <v-spacer></v-spacer>
              <v-chip
                v-if="processingStatus"
                :color="processingStatus.color"
                class="ml-2"
              >
                {{ processingStatus.text }}
              </v-chip>
            </v-card-title>
            
            <v-card-text>
              <image-viewer
                ref="imageViewer"
                :targetId="currentTargetId"
                :selectedFilter="selectedFilter"
                @previews-loaded="handlePreviewsLoaded"
                :image-url="currentImage"
                @update:parameters="handleParameterUpdate"
              />
            </v-card-text>
          </v-card>

          <!-- Historique des traitements -->
          <v-card>
            <v-card-title>Processing History</v-card-title>
            <v-card-text>
              <v-timeline density="compact">
                <v-timeline-item
                  v-for="(action, index) in processingHistory"
                  :key="index"
                  :dot-color="getStatusColor(action.status)"
                  size="small"
                >
                  <template v-slot:opposite>
                    {{ action.timestamp }}
                  </template>
                  <div class="d-flex flex-column">
                    <span>{{ action.description }}</span>
                    
                    <!-- Barre de progression pour les actions en cours -->
                    <v-progress-linear
                      v-if="action.status === 'progress' && action.progress !== undefined"
                      :model-value="action.progress"
                      color="primary"
                      height="5"
                      class="mt-2"
                    ></v-progress-linear>
                    
                    <v-expand-transition>
                      <div v-if="action.files && action.files.length > 0" class="mt-2">
                        <v-chip
                          size="small"
                          color="primary"
                          class="mr-2"
                        >
                          {{ action.files.length }} fichiers
                        </v-chip>
                        <v-chip
                          v-if="action.status === 'success'"
                          size="small"
                          color="success"
                        >
                          Prêt pour le traitement
                        </v-chip>
                      </div>
                    </v-expand-transition>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Snackbar pour les notifications -->
      <v-snackbar
        v-model="snackbar.show"
        :color="snackbar.color"
        :timeout="3000"
      >
        {{ snackbar.text }}
      </v-snackbar>
    </v-container>
  </default-layout>
</template>

<script>
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ObjectSelector from '../components/ObjectSelector.vue'
import ProcessingControls from '../components/ProcessingControls.vue'
import ImageViewer from '../components/ImageViewer.vue'
import websocketService, { createWebSocket } from '../services/websocket'
import axios from 'axios'

export default {
  name: 'Processing',
  components: {
    DefaultLayout,
    ObjectSelector,
    ProcessingControls,
    ImageViewer
  },
  data() {
    return {
      currentTargetId: null,
      selectedPresetId: null,
      selectedFilter: null,
      availableFilters: [],
      filteredAvailableFilters: [],
      currentImage: null,
      currentTarget: null,
      processingHistory: [],
      previewUrls: {},
      processingStatus: null,
      activeTaskId: null,
      downloadCompleted: false,
      enableWebSocket: true, // WebSocket désactivé par défaut
      snackbar: {
        show: false,
        text: '',
        color: 'info'
      },
      pollingInterval: null
    }
  },
  mounted() {
    // WebSocket est désactivé par défaut, on utilise le polling à la place
    console.log('Processing: WebSocket est désactivé, utilisation du polling à la place');

    console.log("Initial filteredAvailableFilters:", this.filteredAvailableFilters);
    console.log("Initial localFilters:", this.localFilters);
    
    // Pour activer le WebSocket plus tard, utiliser:
    // this.enableWebSocket = true;
    // this.initWebSocket();
  },
  async mounted() {
    const { data } = await axios.get(`/api/v1/targets/${this.targetId}/preview`);
    this.previewUrls = data.preview_urls;
  },
  methods: {
    initWebSocket() {
      if (this.enableWebSocket) {
        try {
          createWebSocket(true); // activer explicitement
          websocketService.addListener('processing_update', this.handleWebSocketMessage);
          console.log('Processing: Écouteur WebSocket ajouté pour processing_update');
        } catch (error) {
          console.error('Processing: Erreur lors de l\'initialisation WebSocket:', error);
        }
      }
    },
    
    beforeUnmount() {
      if (this.enableWebSocket) {
        try {
          websocketService.removeListener('processing_update', this.handleWebSocketMessage);
          console.log('Processing: Écouteur WebSocket supprimé');
        } catch (error) {
          console.error('Processing: Erreur lors du nettoyage WebSocket:', error);
        }
      }
    },

    // Pour filtrer les filtres selon preset (HOO, RGB, etc.)
    filterAvailableFilters(filters, presetType) {
      if (!filters || !filters.length) return [];
      
      // Convertir chaque nom de fichier en nom de filtre
      const extractedFilters = filters.map(filename => {
        const match = filename.match(/_(f\d+\w+)_/i);
        return match ? match[1].toUpperCase() : filename;
      });
      
      // Filtres pour les presets HOO
      if (presetType === 'HOO') {
        return extractedFilters.filter(filter => 
          filter.includes('F187N') || // H-alpha
          filter.includes('F444W') || // OIII
          filter.includes('F470N')    // OIII
        );
      } 
      // Filtres pour les presets RGB
      else {
        return extractedFilters.filter(filter => 
          filter.includes('F090W') || // Bleu
          filter.includes('F200W') || 
          filter.includes('F335M') || // Vert
          filter.includes('F444W') || 
          filter.includes('F770W') || // Rouge
          filter.includes('F1130W')
        );
      }
    },
    
    // Gérer la réception des prévisualisations
    handlePreviewsLoaded(data) {
      console.log('Prévisualisations chargées:', data);
      
      if (data && data.preview_urls) {
        // Transforme l'objet preview_urls en un tableau d'objets {title, value, url}
        const filtersArray = Object.entries(data.preview_urls).map(([key, url]) => ({
          title: this.getFilterDisplayName(key),  // Le nom affiché dans la dropdown
          value: key,                             // La valeur utilisée pour identifier le filtre
          url: url                                // L'URL présignée pour afficher l'image
        }));
        
        this.availableFilters = filtersArray;
        this.filteredAvailableFilters = filtersArray;
        
        // Sélectionne automatiquement le premier filtre
        if (filtersArray.length > 0 && !this.selectedFilter) {
          this.handleFilterSelected(filtersArray[0].value);
        }
        
        console.log("Filtres disponibles:", this.filteredAvailableFilters);
        
        // Met à jour le composant ProcessingControls
        if (this.$refs.processingControls) {
          console.log("Reference ProcessingControls trouvée, mise à jour des filtres");
          this.$refs.processingControls.updateFilters(this.filteredAvailableFilters);
        } else {
          console.warn("Reference ProcessingControls non trouvée!");
          // Ajouter un délai pour laisser le temps au composant d'être monté
          setTimeout(() => {
            if (this.$refs.processingControls) {
              this.$refs.processingControls.updateFilters(this.filteredAvailableFilters);
            }
          }, 500);
        }
      }
    },
    
    // Gérer la sélection d'un filtre
    handleFilterSelected(filter) {
      console.log('Filtre sélectionné:', filter);
      this.selectedFilter = filter;
      
      // Trouve l'URL correspondant au filtre sélectionné
      const selectedFilterObj = this.filteredAvailableFilters.find(f => f.value === filter);
      if (selectedFilterObj) {
        this.currentImage = selectedFilterObj.url;
      }
    },
    
    // Obtenir le type de preset à partir de l'ID
    getPresetType(presetId) {
      const presetMap = {
        '7ae3ea6c-348b-4ea3-a5cc-217d49eb7d6f': 'HOO', // JWST HOO
        'e80ca27a-6e9d-44ba-a8b5-af37d2f06ec5': 'HOO', // Autre HOO
        '34d29d25-d87c-4ab6-9e4f-f80a5540dab8': 'RGB', // RGB
        'ddf815bd-f82e-11ef-8e51-0242ac120002': 'RGB', // RGB
        'eb8eb0af-e6ec-4f96-a5cf-64037734cb09': 'RGB'  // RGB
      };
      
      return presetMap[presetId] || 'RGB';
    },
    
    handleWebSocketMessage(data) {
      try {
        console.log('Message WebSocket reçu dans Processing:', data);
        
        if (!data || typeof data !== 'object') return;
        
        if (data.task_id === this.activeTaskId) {
          if (data.type === 'download_progress') {
            this.processingStatus = {
              text: data.message,
              color: 'info'
            };
            
            const progress = data.progress || 0;
            if (progress === 0 || progress % 25 === 0 || progress === 100) {
              this.addUniqueHistoryItem({
                description: data.message,
                timestamp: new Date().toLocaleTimeString(),
                status: 'progress',
                progress: progress
              });
            }
          } else if (data.type === 'download_complete') {
            this.processingStatus = {
              text: 'Téléchargement terminé',
              color: 'success'
            };
            
            if (data.files && data.files.length > 0) {
              if (!this.currentImage) {
                this.currentImage = data.files[0].file_path;
              }
            }
            
            this.addUniqueHistoryItem({
              description: data.message || `Téléchargement terminé : ${data.files ? data.files.length : 0} fichiers disponibles`,
              timestamp: new Date().toLocaleTimeString(),
              status: 'success',
              files: data.files || []
            });
            
            this.showNotification(data.message || `Téléchargement terminé : ${data.files ? data.files.length : 0} fichiers disponibles`, 'success');
          }
        }
      } catch (error) {
        console.error('Erreur lors du traitement du message WebSocket:', error);
      }
    },
    
    addUniqueHistoryItem(item) {
      // Pour les téléchargements terminés, vérifier si c'est cohérent
      if (item.description && item.description.includes('Téléchargement terminé')) {
        // Nettoyer l'historique des anciens téléchargements terminés
        this.processingHistory = this.processingHistory.filter(
          h => !h.description.includes('Téléchargement terminé')
        );
        
        // Ajouter seulement l'entrée actuelle
        this.processingHistory.unshift(item);
        return;
      }
      
      // Comportement normal pour les autres types d'entrées
      const existingItem = this.processingHistory.find(
        h => h.description === item.description && h.status === item.status
      );
      
      if (existingItem) {
        Object.assign(existingItem, item);
        this.processingHistory = [...this.processingHistory];
      } else {
        this.processingHistory.unshift(item);
      }
    },

    handleDownloadStarted(data) {
      this.showNotification(`Téléchargement démarré pour ${data.message}`, 'info')
      this.activeTaskId = data.taskId;
      
      this.addUniqueHistoryItem({
        description: `Started download: ${data.message}`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'pending'
      });
      
      this.processingStatus = {
        text: 'Téléchargement en cours...',
        color: 'info'
      }
    },

    handleDownloadComplete(result) {
      this.downloadCompleted = true;
      const filesCount = result.files ? result.files.length : 0;
      const successMessage = `Téléchargement terminé : ${filesCount} fichiers disponibles`;
      this.showNotification(successMessage, 'success');

      if (result.target_id) {
        this.currentTargetId = result.target_id;
        this.loadFilterOptions(result.target_id);
      }

      if (result.files && result.files.length > 0) {
        this.currentImage = result.files[0];
      }

      this.addUniqueHistoryItem({
        description: successMessage,
        timestamp: new Date().toLocaleTimeString(),
        status: 'success',
        files: result.files
      });

      this.processingStatus = {
        text: 'Prêt pour le traitement',
        color: 'success'
      };
    },

    handleFilterSelected(filter) {
      console.log('Filtre sélectionné:', filter);
      this.selectedFilter = filter;
      const selectedFilterObj = this.filteredAvailableFilters.find(f => f.value === filter);
      if (selectedFilterObj) {
        this.currentImage = selectedFilterObj.url;
      }
    },

    async loadFilterOptions(targetId) {
      if (!targetId) return;
      console.log("✨ Chargement direct des prévisualisations pour:", targetId);
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`/api/v1/targets/${targetId}/preview`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log("🌌 Données brutes reçues:", response.data);

        if (response.data && response.data.preview_urls) {
          const filtersArray = Object.entries(response.data.preview_urls).map(([key, url]) => ({
            title: key,
            value: key,
            url: url
          }));
          this.availableFilters = filtersArray;
          this.filteredAvailableFilters = filtersArray;

          if (this.$refs.processingControls) {
            this.$refs.processingControls.updateFilters(filtersArray);
          }

          if (filtersArray.length > 0) {
            this.currentImage = filtersArray[0].url;
          }
        }
      } catch (error) {
        console.error("Erreur chargement des prévisualisations:", error);
      }
    },

    handleDownloadProgress(data) {
      this.processingStatus = {
        text: data.message,
        color: 'info'
      }
      
      if (data.status === 'progress' && data.progress !== undefined && 
          (data.progress === 0 || data.progress % 25 === 0 || data.progress === 100)) {
        this.addUniqueHistoryItem({
          description: data.message,
          timestamp: new Date().toLocaleTimeString(),
          status: 'progress',
          progress: data.progress
        });
      }
    },

    handleError(message) {
      this.showNotification(message, 'error')
      this.addUniqueHistoryItem({
        description: `Error: ${message}`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'error'
      });
      this.processingStatus = {
        text: 'Erreur',
        color: 'error'
      }
    },

    handleProcessing(params) {
      this.processingStatus = {
        text: 'Traitement en cours...',
        color: 'info'
      }
      this.activeTaskId = params.taskId;
      
      this.addUniqueHistoryItem({
        description: `Applied ${params.workflow} processing`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'success'
      });
    },

    handleParameterUpdate(params) {
      console.log('Parameters updated:', params)
    },

    revertToState(index) {
      this.showNotification('Retour à l\'état précédent', 'success')
    },

    addToHistory(action) {
      this.addUniqueHistoryItem(action);
    },

    showNotification(text, color = 'info') {
      this.snackbar = {
        show: true,
        text,
        color
      }
    },

    getStatusColor(status) {
      switch(status) {
        case 'success': return 'success'
        case 'error': return 'error'
        case 'pending': return 'warning'
        case 'progress': return 'info'
        default: return 'grey'
      }
    },

    async checkTaskStatus() {
      if (!this.activeTaskId) return;
      
      try {
        // Récupérer le token d'authentification depuis le localStorage
        const token = localStorage.getItem('token');
        
        // Ajouter le header d'authentification
        const { data } = await axios.get(`/api/v1/tasks/${this.activeTaskId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        console.log('Polling task status:', data);
        
        if (data.status === 'COMPLETED') {
          this.downloadCompleted = true;
          console.log('appel api pour charger les filtres');
          this.loadFilterOptions(data.target_id);

          this.processingStatus = {
            text: 'Téléchargement terminé',
            color: 'success'
          };
          
          // Extraction du nombre de fichiers depuis le champ error
          let nbFichiers = 0;
          if (data.error && typeof data.error === 'string') {
            const match = data.error.match(/(\d+) fichiers disponibles/);
            if (match && match[1]) {
              nbFichiers = parseInt(match[1], 10);
            }
          }
          
          // Restaurer l'ajout à l'historique avec le nombre correct de fichiers
          this.addUniqueHistoryItem({
            description: `Téléchargement terminé : ${nbFichiers} fichiers disponibles`,
            timestamp: new Date().toLocaleTimeString(),
            status: 'success',
            files: [] // On n'a pas les chemins des fichiers individuels ici
          });
          
          this.showNotification(`Téléchargement terminé : ${nbFichiers} fichiers disponibles`, 'success');
          
          // Arrêter le polling si la tâche est terminée
          this.stopPolling();
        } else if (data.status === 'FAILED') {
          this.processingStatus = {
            text: 'Erreur lors du téléchargement',
            color: 'error'
          };
          
          this.addUniqueHistoryItem({
            description: data.error || 'Erreur lors du téléchargement',
            timestamp: new Date().toLocaleTimeString(),
            status: 'error'
          });
          
          this.showNotification(data.error || 'Erreur lors du téléchargement', 'error');
          
          // Arrêter le polling en cas d'erreur
          this.stopPolling();
        }
        // Les autres états (PENDING, RUNNING) sont déjà gérés
      } catch (error) {
        console.error('Erreur lors de la vérification du statut de la tâche:', error);
      }
    },

    startPolling() {
      if (this.pollingInterval) this.stopPolling();
      this.pollingInterval = setInterval(() => {
        this.checkTaskStatus();
      }, 5000); // Vérifier toutes les 5 secondes
    },
    
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    }
  },
  watch: {
    activeTaskId(newId, oldId) {
      console.log('activeTaskId changé:', newId);
      if (newId) {
        // Si une nouvelle tâche est active, démarrer le polling
        this.startPolling();
      } else {
        // Si plus de tâche active, arrêter le polling
        this.stopPolling();
      }
    }
  }
}
</script>

<style scoped>
.v-timeline {
  max-height: 300px;
  overflow-y: auto;
}
</style>
