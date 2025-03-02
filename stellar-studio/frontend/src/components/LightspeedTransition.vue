<template>
    <div class="lightspeed-container" :class="{ active: isActive }">
      <div v-for="n in 100" :key="n" class="star"></div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const isActive = ref(false);
  
  const activate = () => {
    isActive.value = true;
    setTimeout(() => {
      isActive.value = false;
    }, 500); // Durée de l'animation
  };
  
  defineExpose({ activate });
  </script>
  
  <style scoped>
  .lightspeed-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  .lightspeed-container.active {
    opacity: 1;
  }
  
  .star {
    position: absolute;
    width: 1px;
    height: 1px;
    background: white;
    opacity: 0;
  }
  
  .active .star {
    animation: lightspeed 1s linear forwards;
  }
  
  @keyframes lightspeed {
    0% {
      transform: translateZ(0) scale(1);
      opacity: 0;
    }
    50% {
      opacity: 1;
    }
    100% {
      transform: translateZ(1000px) scale(0);
      opacity: 0;
    }
  }
  </style>
  