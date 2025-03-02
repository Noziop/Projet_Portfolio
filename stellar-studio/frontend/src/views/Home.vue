<template>
  <default-layout>
    <animated-stars :star-count="2000" />
    <nebula-effect />
    <lightspeed-transition ref="lightspeedTransition" />
    <v-container class="content-overlay">
      <v-row justify="center" align="center" class="text-center">
        <v-col cols="12">
          <h1 class="text-h2 mb-6 stellar-title">{{ $t('home.welcome') }}</h1>
          <p class="text-h5 mb-10 stellar-subtitle">
            {{ isAuthenticated ? $t('home.subtitle.auth') : $t('home.subtitle.nonAuth') }}
          </p>
        </v-col>
      </v-row>

      <v-row v-if="isAuthenticated">
        <v-col cols="12" md="4" v-for="(feature, index) in features" :key="index">
          <v-card class="feature-card mx-auto" max-width="400">
            <v-card-title>
              <v-icon start :icon="feature.icon" class="mr-2"></v-icon>
              {{ $t(feature.title) }}
            </v-card-title>
            <v-card-text>
              {{ $t(feature.description) }}
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="pink-accent-2"
                variant="tonal"
                @click="navigateWithLightspeed(feature.route)"
              >
                {{ $t(feature.button) }}
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>

      <v-row v-else justify="center">
        <v-col cols="12" md="6" class="text-center">
          <v-btn
            color="pink-accent-2"
            size="x-large"
            class="auth-btn mx-2"
            @click="navigateWithLightspeed('/auth?mode=login')"
          >
            {{ $t('auth.login') }}
          </v-btn>
          <v-btn
            color="cyan-accent-2"
            size="x-large"
            class="auth-btn mx-2"
            @click="navigateWithLightspeed('/auth?mode=register')"
          >
            {{ $t('auth.register') }}
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </default-layout>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import AnimatedStars from '../components/AnimatedStars.vue'
import NebulaEffect from '../components/NebulaEffect.vue'
import LightspeedTransition from '../components/LightspeedTransition.vue'
import { useAuthStore } from '../stores/auth'
import { storeToRefs } from 'pinia'

export default {
  name: 'Home',
  components: {
    DefaultLayout,
    AnimatedStars,
    NebulaEffect,
    LightspeedTransition
  },

  setup() {
    const authStore = useAuthStore()
    const { isAuthenticated } = storeToRefs(authStore)
    const router = useRouter()
    const lightspeedTransition = ref(null)

    const features = [
      {
        icon: 'mdi-telescope',
        title: 'home.features.telescope.title',
        description: 'home.features.telescope.description',
        button: 'home.features.telescope.button',
        route: '/telescopes'
      },
      {
        icon: 'mdi-image-filter',
        title: 'home.features.processing.title',
        description: 'home.features.processing.description',
        button: 'home.features.processing.button',
        route: '/processing'
      },
      {
        icon: 'mdi-book-open-variant',
        title: 'home.features.docs.title',
        description: 'home.features.docs.description',
        button: 'home.features.docs.button',
        route: '/docs'
      }
    ]

    const navigateWithLightspeed = (route) => {
      lightspeedTransition.value.activate()
      setTimeout(() => {
        router.push(route)
      }, 500) // Attendre la moitié de l'animation avant de changer de page
    }

    return { 
      isAuthenticated, 
      lightspeedTransition, 
      navigateWithLightspeed,
      features
    }
  }
}
</script>

<style scoped>
.content-overlay {
  position: relative;
  z-index: 1;
}

.stellar-title {
  color: white;
  margin-top: 15%;
  text-shadow: 0 0 20px rgba(255, 105, 180, 0.5);
  animation: glow 2s ease-in-out infinite alternate;
}

.stellar-subtitle {
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.3);
}

.feature-card {
  background: rgba(0, 0, 0, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 105, 180, 0.3);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 0 20px rgba(255, 105, 180, 0.3) !important;
}

.auth-btn {
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: bold;
  padding: 0 32px;
}

.auth-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
}

@keyframes glow {
  from {
    text-shadow: 0 0 20px rgba(255, 105, 180, 0.5);
  }
  to {
    text-shadow: 0 0 30px rgba(255, 105, 180, 0.8),
                 0 0 40px rgba(64, 224, 208, 0.4);
  }
}
</style>
