<!-- src/modules/processing/components/FilterSelector.vue -->
<template>
    <div class="filter-selector">
      <v-select 
        v-model="selectedFilter"
        :items="filters"
        item-title="title"
        item-value="value"
        :label="$t('processing.filterSelector.label')" 
        prepend-icon="mdi-filter-outline"
        @update:model-value="onFilterSelected"
      ></v-select>
    </div>
  </template>
  
  <script>
  export default {
    name: 'FilterSelector',
    
    props: {
      modelValue: String,
      filters: {
        type: Array,
        default: () => []
      }
    },
    
    emits: ['update:modelValue', 'filter-selected'],
    
    computed: {
      selectedFilter: {
        get() {
          return this.modelValue;
        },
        set(value) {
          this.$emit('update:modelValue', value);
        }
      }
    },
    
    methods: {
      onFilterSelected(filter) {
        this.$emit('filter-selected', filter);
      }
    }
  }
  </script>
  