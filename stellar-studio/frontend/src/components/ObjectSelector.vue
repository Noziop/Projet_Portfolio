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
      ></v-select>

      <v-select
        v-model="selectedTarget"
        :items="availableTargets"
        label="Select Target"
        item-title="name"
        item-value="id"
        :disabled="!selectedTelescope || loading"
        :loading="loading"
      ></v-select>

      <v-btn
        block
        color="primary"
        :disabled="!selectedTarget"
        :loading="downloadLoading"
        @click="downloadFits"
      >
        Download FITS
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref } from 'vue'
import apiClient from '../services/api'

export default {
  name: 'ObjectSelector',
  
  setup(props, { emit }) {
    const selectedTelescope = ref(null)
    const selectedTarget = ref(null)
    const availableTargets = ref([])
    const loading = ref(false)
    const downloadLoading = ref(false)
    const downloadStatus = ref('idle') // 'idle', 'downloading', 'success', 'error'

    const telescopes = [
      { id: 'HST', name: 'Hubble Space Telescope' },
      { id: 'JWST', name: 'James Webb Space Telescope' }
    ]

    const loadTargets = async () => {
      if (!selectedTelescope.value) return
      
      loading.value = true
      try {
        const response = await apiClient.get(`/observations/${selectedTelescope.value}/targets`)
        availableTargets.value = response.data
      } catch (error) {
        console.error('Failed to load targets:', error)
        emit('error', 'Échec du chargement des cibles')
      } finally {
        loading.value = false
      }
    }

    const downloadFits = async () => {
      if (!selectedTarget.value || !selectedTelescope.value) return

      downloadLoading.value = true
      downloadStatus.value = 'downloading'
      
      try {
        // Trouver le target sélectionné pour avoir son nom
        const target = availableTargets.value.find(t => t.id === selectedTarget.value)
        
        const response = await apiClient.post(`/tasks/download`, {
          telescope: selectedTelescope.value,
          object_name: target.name  // On envoie le nom au lieu de l'ID
        })
        
        emit('download-started', {
          taskId: response.data.task_id,
          message: `Téléchargement démarré pour ${target.name}`
        })
        
        monitorDownload(response.data.task_id)
      } catch (error) {
        console.error('Failed to start download:', error)
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
          
          if (response.data.status === 'SUCCESS') {
            if (response.data.result.status === 'success') {
              downloadStatus.value = 'success'
              emit('download-complete', {
                files: response.data.result.files,
                message: response.data.result.message  // On transmet le message de succès
              })
              return true
            } else if (response.data.result.status === 'error') {
              downloadStatus.value = 'error'
              emit('error', response.data.result.message)
              return true
            }
          } else if (response.data.status === 'PENDING') {
            emit('download-progress', 'Téléchargement en cours...')
          } else if (response.data.status === 'PROGRESS') {
            emit('download-progress', {
              status: 'progress',
              message: response.data.result?.status || 'Téléchargement en cours...'
            })
          } else if (response.data.status === 'FAILURE') {
            downloadStatus.value = 'error'
            emit('error', response.data.result || 'Échec du téléchargement')
            return true
          }
          return false
        } catch (error) {
          console.error('Failed to check status:', error)
          downloadStatus.value = 'error'
          emit('error', 'Erreur lors de la vérification du statut')
          return true
        }
      }

      const interval = setInterval(async () => {
        const done = await checkStatus()
        if (done) clearInterval(interval)
      }, 2000)

      // Nettoyage après 5 minutes
      setTimeout(() => {
        clearInterval(interval)
        if (downloadStatus.value === 'downloading') {
          downloadStatus.value = 'error'
          emit('error', 'Le téléchargement a expiré')
        }
      }, 300000)
    }

    return {
      selectedTelescope,
      selectedTarget,
      telescopes,
      availableTargets,
      loading,
      downloadLoading,
      downloadStatus,
      loadTargets,
      downloadFits
    }
  }
}
</script>