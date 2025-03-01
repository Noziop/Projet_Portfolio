<template>
  <default-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-6">Télescopes Disponibles</h1>
        </v-col>
  
        <!-- État de chargement -->
        <v-col v-if="loading" cols="12" class="text-center">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        </v-col>
  
        <!-- État d'erreur -->
        <v-col v-else-if="error" cols="12">
          <v-alert type="error" variant="tonal" closable>
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
                :src="`/images/telescopes/${telescope.name.toLowerCase()}.jpg`"
                height="200"
                cover
              ></v-img>
              
              <v-card-title>{{ telescope.name }}</v-card-title>
              <v-card-subtitle>{{ telescope.location }}</v-card-subtitle>
              
              <v-card-text>
                <v-list>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-telescope</v-icon>
                    </template>
                    <v-list-item-title>Ouverture: {{ telescope.aperture }}</v-list-item-title>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-ruler</v-icon>
                    </template>
                    <v-list-item-title>Longueur focale: {{ telescope.focal_length }}</v-list-item-title>
                  </v-list-item>
                  
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-camera</v-icon>
                    </template>
                    <v-list-item-title>
                      Instruments: {{ Object.keys(telescope.instruments).join(', ') }}
                    </v-list-item-title>
                  </v-list-item>

                  <v-list-item v-if="telescope.description">
                    <template v-slot:prepend>
                      <v-icon>mdi-information</v-icon>
                    </template>
                    <v-list-item-title>
                      Description
                    </v-list-item-title>
                    <template v-slot:append>
                      <v-dialog
                        v-model="telescope.showFullDescription"
                        max-width="600px"
                      >
                        <template v-slot:activator="{ props }">
                          <v-btn
                            icon="mdi-text-box-outline"
                            variant="text"
                            size="small"
                            v-bind="props"
                          ></v-btn>
                        </template>
                        <v-card>
                          <v-card-title>
                            Description de {{ telescope.name }}
                          </v-card-title>
                          <v-card-text>
                            <p class="text-body-1 white-space-pre-wrap">{{ telescope.description }}</p>
                          </v-card-text>
                          <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn
                              text
                              @click="telescope.showFullDescription = false"
                            >
                              Fermer
                            </v-btn>
                          </v-card-actions>
                        </v-card>
                      </v-dialog>
                    </template>
                  </v-list-item>
                </v-list>
                
                <div v-if="telescope.description" class="mt-2 px-4">
                  <p class="text-body-2 text-truncate-3-lines">{{ telescope.description }}</p>
                </div>
              </v-card-text>
              
              <v-divider></v-divider>
              
              <v-card-text>
                <v-expansion-panels>
                  <!-- Panel for targets -->
                  <v-expansion-panel>
                    <v-expansion-panel-title>Cibles Disponibles</v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-progress-circular
                        v-if="telescope.loading && telescope.loading.targets"
                        indeterminate
                        color="primary"
                        size="24"
                        class="ma-2"
                      ></v-progress-circular>
                      
                      <v-chip-group v-else-if="telescope.availableTargets && telescope.availableTargets.length > 0">
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
                      
                      <v-alert
                        v-else
                        type="info"
                        variant="tonal"
                        density="compact"
                      >
                        Aucune cible disponible pour ce télescope
                      </v-alert>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  
                  <!-- Panel for filters -->
                  <v-expansion-panel>
                    <v-expansion-panel-title>Filtres Disponibles</v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-progress-circular
                        v-if="telescope.loading && telescope.loading.filters"
                        indeterminate
                        color="primary"
                        size="24"
                        class="ma-2"
                      ></v-progress-circular>
                      
                      <div v-else-if="telescope.filters && telescope.filters.length > 0">
                        <v-chip-group>
                          <v-chip
                            v-for="filter in telescope.filters"
                            :key="filter.id"
                            color="primary"
                            variant="outlined"
                            :title="`${filter.wavelength}nm - ${filter.description || 'Pas de description'}`"
                          >
                            {{ filter.name }}
                          </v-chip>
                        </v-chip-group>
                      </div>
                      
                      <v-alert
                        v-else
                        type="info"
                        variant="tonal"
                        density="compact"
                      >
                        Aucun filtre disponible pour ce télescope
                      </v-alert>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  
                  <!-- Panel for presets -->
                  <v-expansion-panel>
                    <v-expansion-panel-title>Préréglages</v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-progress-circular
                        v-if="telescope.loading && telescope.loading.presets"
                        indeterminate
                        color="primary"
                        size="24"
                        class="ma-2"
                      ></v-progress-circular>
                      
                      <v-list v-else-if="telescope.presets && telescope.presets.length > 0">
                        <v-list-item v-for="preset in telescope.presets" :key="preset.id">
                          <v-list-item-title>{{ preset.name }}</v-list-item-title>
                          <v-list-item-subtitle>{{ preset.description || 'Pas de description' }}</v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                      
                      <v-alert
                        v-else
                        type="info"
                        variant="tonal"
                        density="compact"
                      >
                        Aucun préréglage disponible pour ce télescope
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
                  Voir les détails
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
  components: { DefaultLayout },
    
  setup() {
    const telescopes = ref([])
    const loading = ref(false)
    const error = ref(null)
    const etags = ref({}) // Pour stocker les ETags par endpoint

    const fetchTelescopes = async () => {
      loading.value = true
      try {
        // Préparer les headers avec l'ETag si disponible
        const headers = {}
        if (etags.value.telescopes) {
          headers['If-None-Match'] = etags.value.telescopes
        }

        const response = await apiClient.get('/telescopes/?status=online', { headers })
        
        // Sauvegarder l'ETag pour les requêtes futures
        if (response.headers.etag) {
          etags.value.telescopes = response.headers.etag
        }
        
        // Vérifier si nous avons reçu des données (pas 304 Not Modified)
        if (response.data) {
          telescopes.value = response.data.map(telescope => ({
            ...telescope,
            availableTargets: [],
            filters: [],
            presets: [],
            showFullDescription: false,
            loading: {
              targets: false,
              filters: false,
              presets: false
            }
          }))
        }
        
        error.value = null
      } catch (err) {
        console.error('Error fetching telescopes:', err)
        if (err.response && err.response.status !== 304) {
          error.value = `Échec du chargement des télescopes: ${err.message}`
        }
      } finally {
        loading.value = false
      }
    }
  
    const fetchTelescopeTargets = async (telescopeId) => {
      const telescope = telescopes.value.find(t => t.id === telescopeId)
      if (!telescope) return
      
      telescope.loading.targets = true
      
      try {
        // Préparer les headers avec l'ETag si disponible
        const headers = {}
        if (etags.value[`targets_${telescopeId}`]) {
          headers['If-None-Match'] = etags.value[`targets_${telescopeId}`]
        }
        
        const response = await apiClient.get(`/targets/?telescope_id=${telescopeId}`, { headers })
        
        // Sauvegarder l'ETag pour les requêtes futures
        if (response.headers.etag) {
          etags.value[`targets_${telescopeId}`] = response.headers.etag
        }
        
        // Mettre à jour les données si ce n'est pas un 304
        if (response.data) {
          telescope.availableTargets = response.data
        }
      } catch (err) {
        console.error(`Error fetching targets for telescope ${telescopeId}:`, err)
        if (err.response && err.response.status !== 304) {
          // Ne pas afficher d'erreur pour les 304 Not Modified
          telescope.targetsError = `Échec du chargement des cibles: ${err.message}`
        }
      } finally {
        telescope.loading.targets = false
      }
    }

    const fetchTelescopeFilters = async (telescopeId) => {
      const telescope = telescopes.value.find(t => t.id === telescopeId)
      if (!telescope) return
      
      telescope.loading.filters = true
      
      try {
        // Préparer les headers avec l'ETag si disponible
        const headers = {}
        if (etags.value[`filters_${telescopeId}`]) {
          headers['If-None-Match'] = etags.value[`filters_${telescopeId}`]
        }
        
        const response = await apiClient.get(`/telescopes/${telescopeId}/filters`, { headers })
        
        // Sauvegarder l'ETag pour les requêtes futures
        if (response.headers.etag) {
          etags.value[`filters_${telescopeId}`] = response.headers.etag
        }
        
        // Mettre à jour les données si ce n'est pas un 304
        if (response.data) {
          telescope.filters = response.data
        }
      } catch (err) {
        console.error(`Error fetching filters for telescope ${telescopeId}:`, err)
        if (err.response && err.response.status !== 304) {
          telescope.filtersError = `Échec du chargement des filtres: ${err.message}`
        }
      } finally {
        telescope.loading.filters = false
      }
    }

    const fetchTelescopePresets = async (telescopeId) => {
      const telescope = telescopes.value.find(t => t.id === telescopeId)
      if (!telescope) return
      
      telescope.loading.presets = true
      
      try {
        // Préparer les headers avec l'ETag si disponible
        const headers = {}
        if (etags.value[`presets_${telescopeId}`]) {
          headers['If-None-Match'] = etags.value[`presets_${telescopeId}`]
        }
        
        const response = await apiClient.get(`/telescopes/${telescopeId}/presets`, { headers })
        
        // Sauvegarder l'ETag pour les requêtes futures
        if (response.headers.etag) {
          etags.value[`presets_${telescopeId}`] = response.headers.etag
        }
        
        // Mettre à jour les données si ce n'est pas un 304
        if (response.data) {
          telescope.presets = response.data
        }
      } catch (err) {
        console.error(`Error fetching presets for telescope ${telescopeId}:`, err)
        if (err.response && err.response.status !== 304) {
          telescope.presetsError = `Échec du chargement des préréglages: ${err.message}`
        }
      } finally {
        telescope.loading.presets = false
      }
    }

    const showTelescopeDetails = (telescopeId) => {
      // À implémenter : navigation vers la page de détails
      console.log('Show details for telescope:', telescopeId)
    }
  
    onMounted(async () => {
      try {
        await fetchTelescopes()
        
        // Chargement parallèle des données supplémentaires pour chaque télescope
        await Promise.all(telescopes.value.map(telescope => 
          Promise.all([
            fetchTelescopeTargets(telescope.id),
            fetchTelescopeFilters(telescope.id),
            fetchTelescopePresets(telescope.id)
          ])
        ))
      } catch (err) {
        error.value = `Échec du chargement des données: ${err.message}`
      }
    })
  
    return {
      telescopes,
      loading,
      error,
      showTelescopeDetails
    }
  }
}
</script>

<style scoped>
.telescope-card {
  transition: transform 0.3s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.telescope-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.v-card-text {
  flex-grow: 1;
}

.text-truncate-3-lines {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.white-space-pre-wrap {
  white-space: pre-wrap;
}
</style>
