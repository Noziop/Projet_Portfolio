import { defineStore } from 'pinia'
import axios from 'axios'

export const useImageStore = defineStore('images', {
  state: () => ({
    currentImage: null,
    processingHistory: [],
    isLoading: false,
    error: null,
    downloadStatus: null,
    processingStatus: null
  }),

  actions: {
    async downloadFits(objectName, telescope) {
      this.isLoading = true
      this.error = null
      try {
        const response = await axios.get(
          `/api/v1/telescopes/objects/${encodeURIComponent(objectName)}/fits`,
          { params: { telescope } }
        )
        this.downloadStatus = {
          taskId: response.data.task_id,
          status: response.data.status,
          message: response.data.message
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.message || 'Download failed'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    clearError() {
      this.error = null
    }
  }
})
