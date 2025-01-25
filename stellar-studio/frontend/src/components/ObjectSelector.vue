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

    const telescopes = [
      { id: 'HST', name: 'Hubble Space Telescope' },
      { id: 'JWST', name: 'James Webb Space Telescope' }
    ]

    const loadTargets = async () => {
      if (!selectedTelescope.value) return
      
      loading.value = true
      try {
        const response = await apiClient.get(`/telescopes/telescopes/${selectedTelescope.value}/targets`)
        availableTargets.value = response.data
      } catch (error) {
        console.error('Failed to load targets:', error)
        emit('error', 'Failed to load targets')
      } finally {
        loading.value = false
      }
    }

    const downloadFits = async () => {
      if (!selectedTarget.value || !selectedTelescope.value) return

      downloadLoading.value = true
      try {
        const response = await apiClient.get(`/telescopes/objects/${selectedTarget.value}/fits`, {
          params: { telescope: selectedTelescope.value }
        })
        
        emit('download-started', {
          taskId: response.data.task_id,
          message: `Download started for ${selectedTarget.value}`
        })
        
        // Commencer à surveiller le statut du téléchargement
        monitorDownload(response.data.task_id)
      } catch (error) {
        console.error('Failed to start download:', error)
        emit('error', 'Failed to start download')
      } finally {
        downloadLoading.value = false
      }
    }

    const monitorDownload = async (taskId) => {
      const checkStatus = async () => {
        try {
          const response = await apiClient.get(`/telescopes/tasks/${taskId}`)
          if (response.data.status === 'SUCCESS') {
            emit('download-complete', response.data.result)
            return true
          } else if (response.data.status === 'FAILURE') {
            emit('error', 'Download failed')
            return true
          }
          return false
        } catch (error) {
          console.error('Failed to check status:', error)
          return true
        }
      }

      const interval = setInterval(async () => {
        const done = await checkStatus()
        if (done) clearInterval(interval)
      }, 2000)
    }

    return {
      selectedTelescope,
      selectedTarget,
      telescopes,
      availableTargets,
      loading,
      downloadLoading,
      loadTargets,
      downloadFits
    }
  }
}
</script>
