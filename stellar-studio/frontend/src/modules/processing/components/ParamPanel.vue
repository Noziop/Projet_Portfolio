<!-- src/modules/processing/components/ParamPanel.vue -->
<template>
    <div class="param-panel">
      <v-expansion-panels :disabled="disabled">
        <!-- Basic Adjustments -->
        <v-expansion-panel>
          <v-expansion-panel-title>{{ $t('processing.panels.basic') }}</v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <v-col cols="12">
                <slider-control
                  v-model="localParams.stretch"
                  :label="$t('processing.params.stretch')"
                  :min="0"
                  :max="100"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></slider-control>
              </v-col>
              <v-col cols="12">
                <slider-control
                  v-model="localParams.blackPoint"
                  :label="$t('processing.params.blackPoint')"
                  :min="0"
                  :max="100"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></slider-control>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
  
        <!-- Color Balance -->
        <v-expansion-panel>
          <v-expansion-panel-title>{{ $t('processing.panels.color') }}</v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <v-col cols="12">
                <slider-control
                  v-model="localParams.saturation"
                  :label="$t('processing.params.saturation')"
                  :min="0"
                  :max="200"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></slider-control>
              </v-col>
              <v-col cols="12">
                <slider-control
                  v-model="localParams.temperature"
                  :label="$t('processing.params.temperature')"
                  :min="-100"
                  :max="100"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></slider-control>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
        
        <!-- Noise Reduction -->
        <v-expansion-panel>
          <v-expansion-panel-title>{{ $t('processing.panels.noise') }}</v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <v-col cols="12">
                <slider-control
                  v-model="localParams.denoise"
                  :label="$t('processing.params.denoise')"
                  :min="0"
                  :max="100"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></slider-control>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="localParams.denoiseMethod"
                  :items="denoiseMethods"
                  :label="$t('processing.params.denoiseMethod')"
                  :disabled="disabled"
                  @update:model-value="updateParams"
                ></v-select>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>
  </template>
  
  <script>
  import SliderControl from '@/components/ui/SliderControl.vue';
  
  export default {
    name: 'ParamPanel',
    components: {
      SliderControl
    },
    
    props: {
      params: {
        type: Object,
        required: true
      },
      disabled: {
        type: Boolean,
        default: false
      }
    },
    
    emits: ['update:params'],
    
    data() {
      return {
        localParams: { ...this.params },
        denoiseMethods: [
          'Gaussian',
          'Median',
          'Non-local Means'
        ]
      };
    },
    
    methods: {
      updateParams() {
        this.$emit('update:params', { ...this.localParams });
      }
    },
    
    watch: {
      params: {
        handler(newParams) {
          this.localParams = { ...newParams };
        },
        deep: true
      }
    }
  }
  </script>
  