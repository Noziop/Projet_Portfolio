// src/composables/useStarFieldEffect.js
import { ref, onMounted, onUnmounted } from 'vue';
import threeService from '@/services/three/threeService';
import * as THREE from 'three';

export function useStarFieldEffect(options = {}) {
  const containerRef = ref(null);
  let threeContext = null;
  let starField = null;
  let isActive = false;
  let animationId = null;
  
  const init = () => {
    if (!containerRef.value) return;
    
    // Utiliser notre service pour créer une scène
    threeContext = threeService.createScene(containerRef.value, {
      cameraZ: 500,
      fov: 75,
      far: 2000
    });
    
    if (!threeContext) return;
    
    // Créer les étoiles
    starField = threeService.createStarField(
      threeContext.scene, 
      options.count || 1000, 
      options.size || 0.7
    );
    
    // Ajouter des vitesses aux étoiles
    const count = options.count || 1000;
    const velocities = new Float32Array(count);
    
    for (let i = 0; i < count; i++) {
      velocities[i] = Math.random() * (options.speed || 0.05) + 0.01;
    }
    
    starField.velocities = velocities;
    
    isActive = true;
    animate();
    
    return () => {
      isActive = false;
      
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      
      if (starField) {
        starField.dispose();
      }
      
      if (threeContext) {
        threeContext.cleanup();
      }
    };
  };
  
  const animate = () => {
    if (!isActive || !threeContext || !starField) return;
    
    animationId = requestAnimationFrame(animate);
    
    // Animation des étoiles
    const positions = starField.geometry.attributes.position.array;
    const velocities = starField.velocities;
    
    for (let i = 0; i < velocities.length; i++) {
      // Faire avancer les étoiles vers la caméra
      positions[i * 3 + 2] -= velocities[i];
      
      // Réinitialiser les étoiles qui sortent du champ de vision
      if (positions[i * 3 + 2] < -1000) {
        positions[i * 3] = (Math.random() - 0.5) * 2000;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
        positions[i * 3 + 2] = 1000;
      }
    }
    
    starField.geometry.attributes.position.needsUpdate = true;
    
    threeContext.renderer.render(threeContext.scene, threeContext.camera);
  };
  
  // Méthodes pour mettre à jour les paramètres
  const updateSpeed = (value) => {
    if (!starField || !starField.velocities) return;
    
    for (let i = 0; i < starField.velocities.length; i++) {
      starField.velocities[i] = Math.random() * value + 0.01;
    }
  };
  
  const updateColor = (color) => {
    if (starField && starField.material) {
      starField.material.color = 
        typeof color === 'string' ? 
        threeService.hexToColor(color) : 
        new THREE.Color(color);
    }
  };
  
  onMounted(() => {
    const cleanup = init();
    
    onUnmounted(() => {
      if (cleanup) cleanup();
    });
  });
  
  return {
    containerRef,
    updateSpeed,
    updateColor
  };
}
