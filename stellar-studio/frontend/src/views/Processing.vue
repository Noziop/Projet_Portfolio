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
                @process="handleProcessing"
                :disabled="!currentImage"
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
      currentImage: null,
      processingHistory: [],
      processingStatus: null,
      snackbar: {
        show: false,
        text: '',
        color: 'info'
      }
    }
  },
  methods: {
    handleDownloadStarted(data) {
      this.showNotification(`Téléchargement démarré pour ${data.message}`, 'info')
      this.addToHistory({
        description: `Started download: ${data.message}`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'pending'
      })
      this.processingStatus = {
        text: 'Téléchargement en cours...',
        color: 'info'
      }
    },

    handleDownloadComplete(result) {
      const filesCount = result.files ? result.files.length : 0
      const successMessage = `Téléchargement terminé : ${filesCount} fichiers disponibles`
      
      this.showNotification(successMessage, 'success')
      
      if (result.target_id) {
        this.currentTarget = result.target_id
      }
      
      if (result.files && result.files.length > 0) {
        this.currentImage = result.files[0]
      }
      
      this.addToHistory({
        description: successMessage,
        timestamp: new Date().toLocaleTimeString(),
        status: 'success',
        files: result.files
      })
      
      this.processingStatus = {
        text: 'Prêt pour le traitement',
        color: 'success'
      }
    },

    handleDownloadProgress(data) {
      this.processingStatus = {
        text: data.message,
        color: 'info'
      }
      
      if (data.status === 'progress' && data.progress !== undefined && 
          (data.progress === 0 || data.progress % 25 === 0 || data.progress === 100)) {
        this.addToHistory({
          description: data.message,
          timestamp: new Date().toLocaleTimeString(),
          status: 'progress',
          progress: data.progress
        })
      }
    },

    handleError(message) {
      this.showNotification(message, 'error')
      this.addToHistory({
        description: `Error: ${message}`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'error'
      })
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
      this.addToHistory({
        description: `Applied ${params.workflow} processing`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'success'
      })
    },

    handleParameterUpdate(params) {
      console.log('Parameters updated:', params)
    },

    revertToState(index) {
      this.showNotification('Retour à l\'état précédent', 'success')
    },

    addToHistory(action) {
      this.processingHistory.unshift(action)
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
