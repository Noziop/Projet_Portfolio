<!-- src/components/effects/AnimatedStars.vue -->
<template>
    <div ref="starsContainer" class="stars-effect"></div>
  </template>
  
  <script>
  import { useStarFieldEffect } from '@/composables/useStarFieldEffect';
  import { watch } from 'vue';
  
  export default {
    name: 'AnimatedStars',
    
    props: {
      count: {
        type: Number,
        default: 1000
      },
      size: {
        type: Number,
        default: 0.7
      },
      speed: {
        type: Number,
        default: 0.05
      },
      color: {
        type: String,
        default: '#ffffff'
      }
    },
    
    setup(props) {
      // Utilisation du composable pour toute la logique Three.js
      const { containerRef, updateSpeed, updateColor } = useStarFieldEffect({
        count: props.count,
        size: props.size,
        speed: props.speed,
        color: props.color
      });
      
      // Observer les changements de props pour mettre à jour l'effet
      watch(() => props.speed, (newSpeed) => {
        updateSpeed(newSpeed);
      });
      
      watch(() => props.color, (newColor) => {
        updateColor(newColor);
      });
      
      return {
        starsContainer: containerRef
      };
    }
  }
  </script>
  
  <style scoped>
  .stars-effect {
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    overflow: hidden;
  }
  </style>
  