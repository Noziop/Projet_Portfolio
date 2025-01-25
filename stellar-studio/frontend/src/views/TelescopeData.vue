<!-- src/views/TelescopeData.vue -->
<template>
    <default-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-6">Available Telescopes</h1>
        </v-col>
  
        <!-- État de chargement -->
        <v-col v-if="loading" cols="12" class="text-center">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
        </v-col>
  
        <!-- État d'erreur -->
        <v-col v-else-if="error" cols="12">
          <v-alert
            type="error"
            variant="tonal"
            closable
          >
            {{ error }}
          </v-alert>
        </v-col>
  
        <!-- Contenu principal -->
        <template v-else>
          <v-col v-for="telescope in telescopes" 
                 :key="telescope.id" 
                 cols="12" md="6" lg="4">
            <v-card class="telescope-card">
              <v-img
                :src="telescope.image"
                height="200"
                cover
              ></v-img>
              
              <v-card-title>{{ telescope.name }}</v-card-title>
              
              <v-card-subtitle>
                {{ telescope.location }}
              </v-card-subtitle>
              
              <v-card-text>
                <v-list>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-telescope</v-icon>
                    </template>
                    <v-list-item-title>Aperture: {{ telescope.aperture }}</v-list-item-title>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-ruler</v-icon>
                    </template>
                    <v-list-item-title>Focal Length: {{ telescope.focalLength }}</v-list-item-title>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-camera</v-icon>
                    </template>
                    <v-list-item-title>Instruments: {{ telescope.instruments.join(', ') }}</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-card-text>
              
              <v-divider></v-divider>
              
              <v-card-text>
                <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      Available Targets
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <!-- État de chargement des cibles -->
                      <v-progress-circular
                        v-if="!telescope.availableTargets"
                        indeterminate
                        color="primary"
                        size="24"
                        class="ma-2"
                      ></v-progress-circular>
                      
                      <!-- Affichage des cibles -->
                      <v-chip-group v-else-if="telescope.availableTargets.length > 0">
                        <v-chip
                          v-for="target in telescope.availableTargets"
                          :key="target.id"
                          :to="{ name: 'Processing', query: { target: target.id }}"
                          color="primary"
                          variant="outlined"
                        >
                          {{ target.name }}
                        </v-chip>
                      </v-chip-group>
                      
                      <!-- Message si aucune cible -->
                      <v-alert
                        v-else
                        type="info"
                        variant="tonal"
                        density="compact"
                      >
                        No targets available for this telescope
                      </v-alert>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
              
              <v-card-actions>
                <v-btn
                  variant="tonal"
                  block
                  @click="showTelescopeDetails(telescope.id)"
                >
                  View Details
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </template>
      </v-row>
    </v-container>
</default-layout>
  </template>
  
  
  <script>
  import { ref, onMounted } from 'vue'
  import apiClient from '../services/api'
  import DefaultLayout from '../layouts/DefaultLayout.vue'

    
  export default {
    name: 'TelescopeData',

    components: {
    DefaultLayout
  },

    
    setup() {
      const telescopes = ref([
        {
          id: 'HST',
          name: 'Hubble Space Telescope',
          location: 'Low Earth Orbit',
          image: '/images/telescopes/hst.jpg',
          aperture: '2.4 meters',
          focalLength: '57.6 meters',
          instruments: ['WFC3', 'COS', 'ACS', 'STIS'],
          availableTargets: []
        },
        {
          id: 'JWST',
          name: 'James Webb Space Telescope',
          location: 'L2 Lagrange Point',
          image: '/images/telescopes/jwst.jpg',
          aperture: '6.5 meters',
          focalLength: '131.4 meters',
          instruments: ['NIRCam', 'NIRSpec', 'MIRI', 'FGS/NIRISS'],
          availableTargets: []
        }
      ])
  
      const loading = ref(false)
      const error = ref(null)
  
      const fetchTelescopeTargets = async (telescopeId) => {
  try {
    const response = await apiClient.get(`/telescopes/telescopes/${telescopeId}/targets`)
    const telescope = telescopes.value.find(t => t.id === telescopeId)
    if (telescope) {
      telescope.availableTargets = response.data
    }
  } catch (err) {
    console.error(`Error fetching targets for telescope ${telescopeId}:`, err)
    error.value = 'Failed to load telescope targets'
  }
}


  
      onMounted(async () => {
        loading.value = true
        try {
          // Charger les cibles pour chaque télescope
          await Promise.all(telescopes.value.map(telescope => 
            fetchTelescopeTargets(telescope.id)
          ))
        } catch (err) {
          error.value = 'Failed to load telescope data'
        } finally {
          loading.value = false
        }
      })
  
      return {
        telescopes,
        loading,
        error
      }
    }
  }
  </script>
  
  
  <style scoped>
  .telescope-card {
    transition: transform 0.3s;
  }
  
  .telescope-card:hover {
    transform: translateY(-5px);
  }
  </style>
  