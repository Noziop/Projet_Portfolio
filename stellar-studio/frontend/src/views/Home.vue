<template>
    <default-layout>
      <v-container>
        <v-row justify="center" align="center" class="text-center">
          <v-col cols="12">
            <h1 class="text-h2 mb-6">Welcome to Stellar Studio</h1>
            <p class="text-h5 mb-10">Your Advanced Astrophotography Processing Platform</p>
          </v-col>
        </v-row>
  
        <v-row>
          <v-col cols="12" md="4">
            <v-card class="mx-auto" max-width="400">
              <v-card-title>
                <v-icon start icon="mdi-telescope" class="mr-2"></v-icon>
                Telescope Data
              </v-card-title>
              <v-card-text>
                Access data from HST and JWST telescopes directly through our platform.
              </v-card-text>
              <v-card-actions>
                <v-btn
                  color="primary"
                  variant="tonal"
                  @click="$router.push('/processing')"
                >
                  Start Processing
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
  
          <v-col cols="12" md="4">
            <v-card class="mx-auto" max-width="400">
              <v-card-title>
                <v-icon start icon="mdi-image-filter" class="mr-2"></v-icon>
                Processing Tools
              </v-card-title>
              <v-card-text>
                Advanced image processing tools specifically designed for astrophotography.
              </v-card-text>
              <v-card-actions>
                <v-btn
                  color="primary"
                  variant="tonal"
                  @click="$router.push('/processing')"
                >
                  View Tools
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
  
          <v-col cols="12" md="4">
            <v-card class="mx-auto" max-width="400">
              <v-card-title>
                <v-icon start icon="mdi-book-open-variant" class="mr-2"></v-icon>
                Documentation
              </v-card-title>
              <v-card-text>
                Comprehensive guides and tutorials to help you get started.
              </v-card-text>
              <v-card-actions>
                <v-btn
                  color="primary"
                  variant="tonal"
                  @click="$router.push('/docs')"
                >
                  Read Docs
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </default-layout>
  </template>
  
  <script>
  import DefaultLayout from '../layouts/DefaultLayout.vue'
  
  export default {
    name: 'Home',
    components: {
      DefaultLayout
    }
  }
  </script>
  
  <style scoped>
  .v-card {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .v-card-text {
    flex-grow: 1;
  }
  </style>
  