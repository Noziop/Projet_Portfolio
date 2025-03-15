<!-- src/modules/telescope/components/ObjectSelector.vue -->
<template>
    <v-card>
      <v-card-title>{{ $t('telescope.objectSelector.title') }}</v-card-title>
      <v-card-text>
        <v-autocomplete
          v-model="selectedObject"
          :items="objects"
          :loading="loading"
          :label="$t('telescope.objectSelector.label')"
          item-title="name"
          item-value="id"
          return-object
          prepend-icon="mdi-telescope"
          @update:model-value="handleObjectSelected"
        >
          <template v-slot:item="{ item }">
            <v-list-item-title>{{ item.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ item.type }}</v-list-item-subtitle>
          </template>
        </v-autocomplete>
        
        <div v-if="selectedObject" class="selected-object-details mt-3">
          <v-chip v-if="selectedObject.type" class="mb-2">
            {{ selectedObject.type }}
          </v-chip>
          <p v-if="selectedObject.description" class="text-body-2">
            {{ selectedObject.description }}
          </p>
        </div>
      </v-card-text>
    </v-card>
  </template>
  
  <script>
  import { ref, computed, watch, onMounted } from 'vue';
  import telescopeService from '@/modules/telescope/services/telescopeService';
  
  export default {
    name: 'ObjectSelector',
    props: {
      telescopeId: String,
      modelValue: Object
    },
    
    emits: ['update:modelValue', 'object-selected'],
    
    setup(props, { emit }) {
      const objects = ref([]);
      const loading = ref(false);
      const selectedObject = ref(null);
      
      // Synchroniser le modelValue avec la sélection interne
      watch(() => props.modelValue, (newValue) => {
        if (newValue && (!selectedObject.value || newValue.id !== selectedObject.value.id)) {
          selectedObject.value = newValue;
        }
      });
      
      // Charger les objets disponibles
      const loadObjects = async () => {
        if (!props.telescopeId) return;
        
        loading.value = true;
        try {
          const { data } = await telescopeService.getTargets(props.telescopeId);
          objects.value = data;
          
          // Si un objet était sélectionné, on récupère sa version à jour
          if (selectedObject.value) {
            const updatedObject = objects.value.find(o => o.id === selectedObject.value.id);
            if (updatedObject) {
              selectedObject.value = updatedObject;
            }
          }
        } catch (error) {
          console.error('Erreur lors du chargement des objets:', error);
        } finally {
          loading.value = false;
        }
      };
      
      // Gérer la sélection d'un objet
      const handleObjectSelected = (object) => {
        if (!object) return;
        
        emit('update:modelValue', object);
        emit('object-selected', object);
      };
      
      // Réactions aux changements de props
      watch(() => props.telescopeId, () => {
        loadObjects();
      });
      
      // Chargement initial
      onMounted(() => {
        if (props.telescopeId) {
          loadObjects();
        }
      });
      
      return {
        objects,
        loading,
        selectedObject,
        handleObjectSelected
      };
    }
  }
  </script>
  
  <style scoped>
  .selected-object-details {
    border-left: 3px solid var(--v-primary-base);
    padding-left: 12px;
  }
  </style>
  