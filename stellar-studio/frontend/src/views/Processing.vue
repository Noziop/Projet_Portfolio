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
                    :dot-color="action.status === 'success' ? 'success' : 'error'"
                    size="small"
                  >
                    <template v-slot:opposite>
                      {{ action.timestamp }}
                    </template>
                    <div class="d-flex justify-space-between align-center">
                      <span>{{ action.description }}</span>
                      <v-btn
                        v-if="action.status === 'success'"
                        density="compact"
                        icon="mdi-undo"
                        variant="text"
                        @click="revertToState(index)"
                      ></v-btn>
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
        this.showNotification('Download started', 'info')
        this.addToHistory({
          description: `Started download: ${data.message}`,
          timestamp: new Date().toLocaleTimeString(),
          status: 'pending'
        })
      },
      handleProcessing(params) {
        this.processingStatus = {
          text: 'Processing...',
          color: 'info'
        }
        // TODO: Implement actual processing logic
        this.addToHistory({
          description: `Applied ${params.workflow} processing`,
          timestamp: new Date().toLocaleTimeString(),
          status: 'success'
        })
      },
      handleParameterUpdate(params) {
        // TODO: Handle real-time parameter updates
        console.log('Parameters updated:', params)
      },
      revertToState(index) {
        // TODO: Implement state reversion
        this.showNotification('Reverted to previous state', 'success')
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
  