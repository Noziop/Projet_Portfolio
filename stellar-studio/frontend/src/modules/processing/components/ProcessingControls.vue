<!-- src/modules/processing/components/ProcessingControls.vue -->
<template>
    <v-card class="processing-controls">
      <v-card-title>Processing Controls</v-card-title>
      <v-card-text>
        <!-- Sélection de filtre -->
        <filter-selector
          v-model="selectedFilter"
          :filters="availableFilters"
          @filter-selected="handleFilterSelected"
        />
        
        <!-- Panneaux de paramètres -->
        <param-panel
          v-model:params="params"
          :disabled="!processingEnabled || isProcessing"
          class="mt-4"
        />
        
        <!-- Boutons d'action -->
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
  import { mapState, mapActions } from 'pinia';
  import FilterSelector from './FilterSelector.vue';
  import ParamPanel from './ParamPanel.vue';
  import { useProcessingStore } from '../store/processingStore';
  
  export default {
    name: 'ProcessingControls',
    components: {
      FilterSelector,
      ParamPanel
    },
    
    props: {
      targetId: String,
      processingEnabled: {
        type: Boolean,
        default: false
      }
    },
    
    emits: ['filter-selected', 'process'],
    
    computed: {
      ...mapState(useProcessingStore, [
        'selectedFilter', 
        'processingParams', 
        'isProcessing', 
        'availableFilters'
      ]),
      
      params: {
        get() {
          return this.processingParams;
        },
        set(newParams) {
          this.updateParams(newParams);
        }
      },
      
      canProcess() {
        return this.selectedFilter && !this.isProcessing && this.processingEnabled;
      }
    },
    
    methods: {
      ...mapActions(useProcessingStore, [
        'setCurrentTarget', 
        'setFilter', 
        'updateParams', 
        'resetParams', 
        'processTarget'
      ]),
      
      handleFilterSelected(filter) {
        this.setFilter(filter);
        this.$emit('filter-selected', filter);
      },
      
      async processImage() {
        if (!this.canProcess) return;
        
        try {
          const taskId = await this.processTarget({
            targetId: this.targetId,
            filter: this.selectedFilter
          });
          
          this.$emit('process', {
            taskId,
            filter: this.selectedFilter,
            params: this.params
          });
        } catch (error) {
          console.error('Processing error:', error);
        }
      }
    },
    
    watch: {
      targetId: {
        handler(newId) {
          if (newId) {
            this.setCurrentTarget(newId);
          }
        },
        immediate: true
      }
    }
  }
  </script>
  
  <style scoped>
  .processing-controls {
    height: 100%;
  }
  </style>
  