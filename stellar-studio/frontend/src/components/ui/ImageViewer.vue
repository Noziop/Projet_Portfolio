<!-- src/components/ui/ImageViewer.vue -->
<template>
    <div 
      class="image-viewer" 
      :class="{ 'image-viewer--loading': loading, 'image-viewer--error': error }"
    >
      <!-- Overlay de chargement -->
      <div v-if="loading" class="image-viewer__loading">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <span class="mt-2">{{ $t('imageViewer.loading') }}</span>
      </div>
      
      <!-- Message d'erreur -->
      <div v-else-if="error" class="image-viewer__error">
        <v-icon size="large" color="error">mdi-alert-circle</v-icon>
        <span class="mt-2">{{ errorMessage }}</span>
        <v-btn 
          v-if="imageSrc" 
          color="primary" 
          class="mt-4" 
          @click="reloadImage"
        >
          {{ $t('imageViewer.retry') }}
        </v-btn>
      </div>
      
      <!-- Image avec contrôles de visualisation -->
      <div v-else-if="imageSrc" ref="viewerContainer" class="image-viewer__container">
        <img 
          :src="imageSrc" 
          :alt="imageAlt || $t('imageViewer.defaultAlt')" 
          @load="handleImageLoaded" 
          @error="handleImageError"
          class="image-viewer__img"
        >
      </div>
      
      <!-- Message si pas d'image -->
      <div v-else class="image-viewer__empty">
        <v-icon size="large" color="grey">mdi-image-off</v-icon>
        <span class="mt-2">{{ $t('imageViewer.noImage') }}</span>
      </div>
      
      <!-- Contrôles de visualisation (zoom, rotation, etc.) -->
      <div v-if="showControls && imageSrc && !loading && !error" class="image-viewer__controls">
        <v-btn icon @click="zoomIn">
          <v-icon>mdi-magnify-plus</v-icon>
        </v-btn>
        <v-btn icon @click="zoomOut">
          <v-icon>mdi-magnify-minus</v-icon>
        </v-btn>
        <v-btn icon @click="rotateLeft">
          <v-icon>mdi-rotate-left</v-icon>
        </v-btn>
        <v-btn icon @click="rotateRight">
          <v-icon>mdi-rotate-right</v-icon>
        </v-btn>
        <v-btn icon @click="resetView">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
  import { directive as viewer } from 'v-viewer';

  
  export default {
    name: 'ImageViewer',
    directives: {
      viewer
    },
    props: {
      imageUrl: {
        type: String,
        default: ''
      },
      loading: {
        type: Boolean,
        default: false
      },
      error: {
        type: [Boolean, String, Error],
        default: false
      },
      imageAlt: String,
      showControls: {
        type: Boolean,
        default: true
      },
      viewerOptions: {
        type: Object,
        default: () => ({})
      }
    },
    
    emits: ['load', 'error', 'zoom', 'rotate'],
    
    setup(props, { emit }) {
      const viewerContainer = ref(null);
      const imageViewer = ref(null);
      
      // Propriétés calculées
      const imageSrc = computed(() => props.imageUrl);
      
      const errorMessage = computed(() => {
        if (typeof props.error === 'string') {
          return props.error;
        } else if (props.error === true) {
          return "Erreur lors du chargement de l'image";
        }
        return '';
      });
      
      // Méthodes de contrôle
      const initializeViewer = () => {
        if (!viewerContainer.value) return;
        
        const defaultOptions = {
          inline: false,
          button: true,
          navbar: false,
          title: false,
          toolbar: false,
          tooltip: true,
          movable: true,
          zoomable: true,
          rotatable: true,
          scalable: true,
          transition: true,
          fullscreen: true,
          keyboard: true,
        };
        
        // Fusionner les options par défaut avec celles fournies en props
        const options = { ...defaultOptions, ...props.viewerOptions };
        
        // Initialiser le viewer
        imageViewer.value = new Viewer(viewerContainer.value, options);
      };
      
      const destroyViewer = () => {
        if (imageViewer.value) {
          imageViewer.value.destroy();
          imageViewer.value = null;
        }
      };
      
      const handleImageLoaded = (event) => {
        emit('load', {
          width: event.target.naturalWidth,
          height: event.target.naturalHeight,
          src: event.target.src
        });
        
        // Réinitialiser le viewer lorsque l'image est chargée
        destroyViewer();
        initializeViewer();
      };
      
      const handleImageError = (event) => {
        emit('error', 'Impossible de charger l\'image');
      };
      
      const reloadImage = () => {
        // Forcer le rechargement de l'image
        const currentSrc = imageSrc.value;
        if (currentSrc.includes('?')) {
          // Ajouter un timestamp pour contourner le cache du navigateur
          const timestamp = new Date().getTime();
          return `${currentSrc}&_=${timestamp}`;
        } else {
          return `${currentSrc}?_=${new Date().getTime()}`;
        }
      };
      
      // Contrôles directs du viewer
      const zoomIn = () => {
        if (imageViewer.value) {
          imageViewer.value.zoom(0.1);
          emit('zoom', imageViewer.value.imageData.ratio);
        }
      };
      
      const zoomOut = () => {
        if (imageViewer.value) {
          imageViewer.value.zoom(-0.1);
          emit('zoom', imageViewer.value.imageData.ratio);
        }
      };
      
      const rotateLeft = () => {
        if (imageViewer.value) {
          imageViewer.value.rotate(-90);
          emit('rotate', imageViewer.value.imageData.rotate);
        }
      };
      
      const rotateRight = () => {
        if (imageViewer.value) {
          imageViewer.value.rotate(90);
          emit('rotate', imageViewer.value.imageData.rotate);
        }
      };
      
      const resetView = () => {
        if (imageViewer.value) {
          imageViewer.value.reset();
        }
      };
      
      // Lifecycle hooks
      onMounted(() => {
        if (imageSrc.value && !props.loading && !props.error) {
          initializeViewer();
        }
      });
      
      onUnmounted(() => {
        destroyViewer();
      });
      
      // Réagir aux changements de l'URL de l'image
      watch(() => props.imageUrl, (newUrl, oldUrl) => {
        if (newUrl !== oldUrl) {
          // Réinitialiser le viewer quand l'URL change
          destroyViewer();
          // Le nouveau viewer sera initialisé dans handleImageLoaded
        }
      });
      
      return {
        viewerContainer,
        imageSrc,
        errorMessage,
        handleImageLoaded,
        handleImageError,
        reloadImage,
        zoomIn,
        zoomOut,
        rotateLeft,
        rotateRight,
        resetView
      };
    }
  }
  </script>
  
  <style scoped>
  .image-viewer {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 300px;
    background: #f5f5f5;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .image-viewer__loading,
  .image-viewer__error,
  .image-viewer__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    width: 100%;
    color: #666;
  }
  
  .image-viewer__container {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .image-viewer__img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
  
  .image-viewer__controls {
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.5);
    border-radius: 20px;
    padding: 5px 10px;
    display: flex;
    gap: 5px;
    z-index: 10;
  }
  </style>
  