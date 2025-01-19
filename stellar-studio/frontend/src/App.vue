<template>
  <v-app>
    <v-theme-provider :theme="theme">
      <!-- Loading Overlay -->
      <v-overlay
        :model-value="isLoading"
        class="align-center justify-center"
      >
        <v-progress-circular
          color="primary"
          indeterminate
          size="64"
        ></v-progress-circular>
      </v-overlay>

      <!-- Main Content -->
      <router-view></router-view>

      <!-- Global Error Snackbar -->
      <v-snackbar
        v-model="showError"
        color="error"
        timeout="5000"
        location="top"
      >
        {{ errorMessage }}
        <template v-slot:actions>
          <v-btn
            color="white"
            variant="text"
            @click="clearError"
          >
            Close
          </v-btn>
        </template>
      </v-snackbar>
    </v-theme-provider>
  </v-app>
</template>

<script>
import { useImageStore } from './stores/images'
import { storeToRefs } from 'pinia'

export default {
  name: 'App',
  
  setup() {
    const imageStore = useImageStore()
    const { isLoading, error } = storeToRefs(imageStore)
    return { imageStore, isLoading, error }
  },

  data() {
    return {
      theme: 'dark',
      showError: false,
      errorMessage: ''
    }
  },

  watch: {
    error(newError) {
      if (newError) {
        this.errorMessage = newError
        this.showError = true
      }
    }
  },

  methods: {
    clearError() {
      this.showError = false
      this.imageStore.clearError()
    }
  }
}
</script>

<style>
:root {
  --primary-color: #1976D2;
  --secondary-color: #424242;
  --accent-color: #82B1FF;
  --error-color: #FF5252;
  --success-color: #4CAF50;
}

.v-application {
  font-family: 'Roboto', sans-serif;
}

.theme--dark.v-application {
  background: #121212;
}

.v-card {
  border-radius: 8px;
}

.v-btn {
  text-transform: none;
}
</style>
