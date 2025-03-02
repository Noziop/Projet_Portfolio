<template>
  <v-app>
    <v-theme-provider :theme="theme">
      <!-- Transition Lightspeed -->
      <lightspeed-transition :active="isTransitioning" @transitionend="onTransitionEnd" />

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

      <!-- Main Content with Transition -->
      <router-view v-slot="{ Component }">
        <transition :name="transitionName" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>

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
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LightspeedTransition from './components/LightspeedTransition.vue'

export default {
  name: 'App',
  components: {
    LightspeedTransition,
  },
  
  setup() {
    const imageStore = useImageStore()
    const { isLoading, error } = storeToRefs(imageStore)
    const router = useRouter()

    // Gestion des transitions
    const isTransitioning = ref(false)
    const transitionName = ref('')

    watch(() => router.currentRoute.value, (to, from) => {
      if (to.meta.transition === 'lightspeed' && from.meta.transition === 'lightspeed') {
        isTransitioning.value = true
        transitionName.value = 'lightspeed'
      } else {
        transitionName.value = 'fade'
      }
    })

    const onTransitionEnd = () => {
      isTransitioning.value = false
    }

    return { 
      imageStore, 
      isLoading, 
      error, 
      isTransitioning, 
      transitionName, 
      onTransitionEnd 
    }
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
/* Styles pour les transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.lightspeed-enter-active,
.lightspeed-leave-active {
  transition: all 0.5s ease;
}

.lightspeed-enter-from,
.lightspeed-leave-to {
  opacity: 0;
  transform: scale(1.5);
}

/* Autres styles globaux */
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
