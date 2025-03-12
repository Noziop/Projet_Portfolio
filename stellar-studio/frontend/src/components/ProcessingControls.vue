<template>
    <v-card>
      <v-card-title>Processing Controls</v-card-title>
      <v-card-text>
        <!-- Workflow Selection -->
        <v-select 
          v-model="selectedFilter"
          :items="localFilters"
          :preview-urls="previewUrls"
          item-title="title"
          item-value="value"
          label="Filtre d'affichage"
          prepend-icon="mdi-filter-outline"
        ></v-select>
  
        <!-- Processing Parameters -->
        <v-expansion-panels :disabled="!processingEnabled">
          <!-- Basic Adjustments -->
          <v-expansion-panel>
            <v-expansion-panel-title>Basic Adjustments</v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12">
                  <v-slider
                    v-model="params.stretch"
                    label="Stretch"
                    min="0"
                    max="100"
                    thumb-label
                  ></v-slider>
                </v-col>
                <v-col cols="12">
                  <v-slider
                    v-model="params.blackPoint"
                    label="Black Point"
                    min="0"
                    max="100"
                    thumb-label
                  ></v-slider>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
  
          <!-- Color Balance -->
          <v-expansion-panel>
            <v-expansion-panel-title>Color Balance</v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12">
                  <v-slider
                    v-model="params.saturation"
                    label="Saturation"
                    min="0"
                    max="200"
                    thumb-label
                  ></v-slider>
                </v-col>
                <v-col cols="12">
                  <v-slider
                    v-model="params.temperature"
                    label="Temperature"
                    min="-100"
                    max="100"
                    thumb-label
                  ></v-slider>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
  
          <!-- Noise Reduction -->
          <v-expansion-panel>
            <v-expansion-panel-title>Noise Reduction</v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12">
                  <v-slider
                    v-model="params.denoise"
                    label="Denoise Strength"
                    min="0"
                    max="100"
                    thumb-label
                  ></v-slider>
                </v-col>
                <v-col cols="12">
                  <v-select
                    v-model="params.denoiseMethod"
                    :items="denoiseMethods"
                    label="Denoise Method"
                  ></v-select>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
  
        <!-- Action Buttons -->
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="outlined"
            @click="resetParams"
            :disabled="!processingEnabled || isProcessing"
          >
            Reset
          </v-btn>
          <v-btn
            color="primary"
            @click="processImage"
            :loading="isProcessing"
            :disabled="!processingEnabled || !canProcess"
          >
            Process Image
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </template>
  
  <script>
  export default {
    name: 'ProcessingControls',
    props: {
      targetId: String,
      presetId: String,
      previewUrls: {
        type: Object,
        default: () => ({}),
      },
      availableFilters: {
        type: Array,
        default: () => []
      },
      processingEnabled: {
        type: Boolean,
        default: false
      }
    },
    data() {
      return {
        selectedWorkflow: null,
        isProcessing: false,
        selectedFilter: null,
        localFilters: [], 
        workflows: [
          { id: 'basic', name: 'Basic Processing' },
          { id: 'hdr', name: 'HDR Processing' },
          { id: 'narrowband', name: 'Narrowband Processing' }
        ],
        denoiseMethods: [
          'Gaussian',
          'Median',
          'Non-local Means'
        ],
        params: {
          stretch: 50,
          blackPoint: 0,
          saturation: 100,
          temperature: 0,
          denoise: 0,
          denoiseMethod: 'Gaussian'
        }
      }
    },
    created() {
      // Initialise avec les props
      this.localFilters = this.availableFilters;
    },
    mounted() {
      console.log("[ProcessingControls] mounted, localFilters =", this.localFilters);
      console.log("[ProcessingControls] monté avec targetId =", this.targetId);
      if (this.targetId) {
        this.loadFilterOptions();
      }
    },
    updated() {
      console.log("[ProcessingControls] updated, localFilters =", this.localFilters);
    },
    computed: {
      canProcess() {
        return this.selectedWorkflow && !this.isProcessing
      }
    },
    methods: {
      async loadFilterOptions() {
        if (!this.targetId) {
          console.warn("Impossible de charger les filtres : targetId manquant");
          return;
        }
        
        try {
          console.log("Chargement des filtres pour", this.targetId);
          const response = await fetch(`/api/v1/targets/${this.targetId}/preview`);
          const data = await response.json();
          
          if (data && data.preview_urls) {
            // Transformer les URLs en options pour le v-select
            const options = Object.entries(data.preview_urls).map(([key, url]) => ({
              title: key,
              value: key,
              url: url
            }));
            this.localFilters = options;
            console.log("Filtres chargés :", this.localFilters);
          }
        } catch (error) {
          console.error("Erreur lors du chargement des filtres :", error);
        }
      },
      updateFilters(filters) {
        console.log('Mise à jour des filtres:', filters);
        this.localFilters = filters;

        if (filters && filters.length > 0) {
          this.selectedFilter = filters[0].value;
          this.$emit('filter-selected', this.selectedFilter);
        }
      },
      async processImage() {
        this.isProcessing = true
        try {
          // Émettre un événement avec les paramètres de traitement
          this.$emit('process', {
            workflow: this.selectedWorkflow,
            params: this.params
          })
        } catch (error) {
          console.error('Processing error:', error)
        } finally {
          this.isProcessing = false
        }
      },
      resetParams() {
        this.params = {
          stretch: 50,
          blackPoint: 0,
          saturation: 100,
          temperature: 0,
          denoise: 0,
          denoiseMethod: 'Gaussian'
        }
      },
      selectFilter() {
        this.$emit('filter-selected', this.selectedFilter);
      },
    },
    watch: {
      targetId(newId) {
        if (newId) {
          this.loadFilterOptions();
        }
      },
      availableFilters: {
        handler(newFilters) {
          console.log('[ProcessingControls] availableFilters changé:', newFilters);
          // Vérification du format des données
          if (newFilters && newFilters.length > 0) {
            console.log('Premier élément:', newFilters[0]);
            // S'assurer que chaque objet a title et value
            this.localFilters = newFilters.map(filter => {
              if (typeof filter === 'object' && filter.title && filter.value) {
                return filter;
              } else if (typeof filter === 'object' && filter.value) {
                return { ...filter, title: filter.value };
              } else {
                return { 
                  title: String(filter),
                  value: filter
                };
              }
            });
          } else {
            this.localFilters = [];
          }
        },
        immediate: true
      }
    }
  }
  </script>
  
  <style scoped>
  .v-card-text {
    padding-top: 20px;
  }
  </style>
  