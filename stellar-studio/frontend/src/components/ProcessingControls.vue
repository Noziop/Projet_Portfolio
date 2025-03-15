<template>
  <v-card>
    <v-card-title>Processing Controls</v-card-title>
    <v-card-text>
      <!-- Workflow Selection -->
      <v-select 
        v-model="selectedFilter"
        :items="localFilters"
        item-title="title"
        item-value="value"
        label="Filtre d'affichage"
        prepend-icon="mdi-filter-outline"
        @update:model-value="selectFilter"
      ></v-select>

      <!-- Processing Parameters -->
      <v-expansion-panels :disabled="!processingEnabled">
        <!-- Panels restent inchangés -->
        <v-expansion-panel>
          <v-expansion-panel-title>Basic Adjustments</v-expansion-panel-title>
          <v-expansion-panel-text>
            <!-- Contenu inchangé -->
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

        <!-- Autres panels inchangés -->
        <v-expansion-panel>
          <v-expansion-panel-title>Color Balance</v-expansion-panel-title>
          <v-expansion-panel-text>
            <!-- Contenu inchangé -->
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

        <v-expansion-panel>
          <v-expansion-panel-title>Noise Reduction</v-expansion-panel-title>
          <v-expansion-panel-text>
            <!-- Contenu inchangé -->
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

      <!-- Action Buttons inchangés -->
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
    // Ajout d'une prop filtersOptions qui remplace l'appel API
    filterOptions: {
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

  computed: {
    canProcess() {
      return this.selectedFilter && !this.isProcessing
    }
  },

  methods: {
    // SUPPRIME la méthode loadFilterOptions qui faisait l'appel API
    
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
        this.$emit('process', {
          filter: this.selectedFilter,
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
    }
  },

  watch: {
    // REMPLACE la watch sur targetId qui appelait loadFilterOptions
    // par une watch sur filterOptions directement
    filterOptions: {
      handler(newFilters) {
        console.log('[ProcessingControls] filterOptions changé:', newFilters);
        if (newFilters && newFilters.length > 0) {
          this.localFilters = newFilters;
          
          // Sélectionner automatiquement le premier filtre si aucun n'est sélectionné
          if (!this.selectedFilter) {
            this.selectedFilter = newFilters[0].value;
            this.$emit('filter-selected', this.selectedFilter);
          }
        } else {
          this.localFilters = [];
        }
      },
      immediate: true
    },

    selectedFilter(newValue) {
      if(newValue) {
        this.$emit('filter-selected', newValue);
        console.log("Filtre sélectionné :", newValue);
      }
    }
  },
  
  // Pas besoin d'appeler loadFilterOptions dans mounted
  mounted() {
    console.log("[ProcessingControls] mounted, localFilters =", this.localFilters);
  }
}
</script>

<style scoped>
.v-card-text {
  padding-top: 20px;
}
</style>
