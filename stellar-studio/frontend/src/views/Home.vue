<template>
  <default-layout>
    <animated-stars :star-count="800" />
    <nebula-effect />
    <v-container class="content-overlay">
      <v-row justify="center" align="center" class="text-center">
        <v-col cols="12">
          <h1 class="text-h2 mb-6 stellar-title">Welcome to Stellar Studio</h1>
          <p class="text-h5 mb-10 stellar-subtitle">
            {{ isAuthenticated ? 'Your Advanced Astrophotography Processing Platform' : 'Sign in to start processing your astronomical images' }}
          </p>
        </v-col>
      </v-row>

      <v-row v-if="isAuthenticated">
        <v-col cols="12" md="4">
          <v-card class="feature-card mx-auto" max-width="400">
            <v-card-title>
              <v-icon start icon="mdi-telescope" class="mr-2"></v-icon>
              Telescope Data
            </v-card-title>
            <v-card-text>
              Access data from HST and JWST telescopes directly through our platform.
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="pink-accent-2"
                variant="tonal"
                @click="$router.push('/telescopes')"
              >
                Browse Telescopes
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card class="feature-card mx-auto" max-width="400">
            <v-card-title>
              <v-icon start icon="mdi-image-filter" class="mr-2"></v-icon>
              Processing Tools
            </v-card-title>
            <v-card-text>
              Advanced image processing tools specifically designed for astrophotography.
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="pink-accent-2"
                variant="tonal"
                @click="$router.push('/processing')"
              >
                Start Processing
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card class="feature-card mx-auto" max-width="400">
            <v-card-title>
              <v-icon start icon="mdi-book-open-variant" class="mr-2"></v-icon>
              Documentation
            </v-card-title>
            <v-card-text>
              Comprehensive guides and tutorials to help you get started.
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="pink-accent-2"
                variant="tonal"
                @click="$router.push('/docs')"
              >
                Read Docs
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
            @click="$router.push('/auth')"
          >
            Login
          </v-btn>
          <v-btn
            color="cyan-accent-2"
            size="x-large"
            class="auth-btn mx-2"
            @click="$router.push('/auth')"
          >
            Register
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </default-layout>
</template>

<script>
import DefaultLayout from '../layouts/DefaultLayout.vue'
import AnimatedStars from '../components/AnimatedStars.vue'
import NebulaEffect from '../components/NebulaEffect.vue'
import { useAuthStore } from '../stores/auth'
import { storeToRefs } from 'pinia'

export default {
  name: 'Home',
  components: {
    DefaultLayout,
    AnimatedStars,
    NebulaEffect
  },

  setup() {
    const authStore = useAuthStore()
    const { isAuthenticated } = storeToRefs(authStore)
    return { isAuthenticated }
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
