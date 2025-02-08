<template>
    <v-card>
      <v-card-title>Processing Controls</v-card-title>
      <v-card-text>
        <!-- Workflow Selection -->
        <v-select
          v-model="selectedWorkflow"
          :items="workflows"
          label="Processing Workflow"
          item-title="name"
          item-value="id"
          prepend-icon="mdi-cog-outline"
        ></v-select>
  
        <!-- Processing Parameters -->
        <v-expansion-panels>
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
            :disabled="isProcessing"
          >
            Reset
          </v-btn>
          <v-btn
            color="primary"
            @click="processImage"
            :loading="isProcessing"
            :disabled="!canProcess"
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
    data() {
      return {
        selectedWorkflow: null,
        isProcessing: false,
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
        return this.selectedWorkflow && !this.isProcessing
      }
    },
    methods: {
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
      }
    }
  }
  </script>
  
  <style scoped>
  .v-card-text {
    padding-top: 20px;
  }
  </style>
  