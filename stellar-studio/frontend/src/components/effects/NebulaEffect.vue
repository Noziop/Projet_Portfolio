<!-- src/components/effects/NebulaEffect.vue -->
<template>
    <div ref="nebulaContainer" class="nebula-effect"></div>
  </template>
  
  <script>
  import { useNebulaEffect } from '@/composables/useNebulaEffect';
  import { computed, watch } from 'vue';
  
  export default {
    name: 'NebulaEffect',
    
    props: {
      color: {
        type: String,
        default: '#3366ff'
      },
      density: {
        type: Number,
        default: 0.5
      },
      speed: {
        type: Number,
        default: 0.2
      },
      intensity: {
        type: Number,
        default: 1.5
      }
    },
    
    setup(props) {
      // Convertir la couleur hex en numérique pour Three.js
      const hexToColor = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!result) return 0x3366ff;
        
        return parseInt(`0x${result[1]}${result[2]}${result[3]}`, 16);
      };
      
      const colorValue = computed(() => hexToColor(props.color));
      
      const {
        containerRef: nebulaContainer,
        updateColor,
        updateDensity,
        updateSpeed,
        updateIntensity
      } = useNebulaEffect({
        color: colorValue.value,
        density: props.density,
        speed: props.speed,
        intensity: props.intensity
      });
      
      // Réagir aux changements de props
      watch(() => colorValue.value, (newColor) => updateColor(newColor));
      watch(() => props.density, (newValue) => updateDensity(newValue));
      watch(() => props.speed, (newValue) => updateSpeed(newValue));
      watch(() => props.intensity, (newValue) => updateIntensity(newValue));
      
      return {
        nebulaContainer
      };
    }
  }
  </script>
  
  <style scoped>
  .nebula-effect {
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    overflow: hidden;
  }
  </style>
  