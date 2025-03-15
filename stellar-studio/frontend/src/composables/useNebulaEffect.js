// src/composables/useNebulaEffect.js
import { ref, onMounted, onUnmounted } from 'vue';
import threeService from '@/services/three/threeService';
import * as THREE from 'three';

export function useNebulaEffect(options = {}) {
  const containerRef = ref(null);
  let threeContext = null;
  let mesh = null;
  let material = null;
  let isActive = false;
  let animationId = null;
  
  const init = () => {
    if (!containerRef.value) return;
    
    // Utiliser notre service pour créer une scène basique
    threeContext = threeService.createScene(containerRef.value, {
      cameraZ: 5,
      antialias: true
    });
    
    if (!threeContext) return;
    
    // Créer le matériau de nébuleuse via notre service
    material = threeService.createNebulaMaterial({
      color: options.color || 0x3366ff,
      density: options.density || 0.5,
      speed: options.speed || 0.2,
      intensity: options.intensity || 1.5
    });
    
    // Créer le mesh de nébuleuse
    const geometry = new THREE.PlaneGeometry(10, 10);
    mesh = new THREE.Mesh(geometry, material);
    threeContext.scene.add(mesh);
    
    isActive = true;
    animate();
    
    return () => {
      isActive = false;
      
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      
      if (threeContext) {
        threeContext.cleanup();
      }
      
      if (material) material.dispose();
      if (geometry) geometry.dispose();
    };
  };
  
  const animate = () => {
    if (!isActive || !threeContext) return;
    
    animationId = requestAnimationFrame(animate);
    
    // Mise à jour du temps
    const time = performance.now() * 0.001;
    if (material) {
      material.uniforms.time.value = time;
    }
    
    threeContext.renderer.render(threeContext.scene, threeContext.camera);
  };
  
  // Méthodes pour mettre à jour les paramètres
  const updateColor = (color) => {
    if (material) {
      material.uniforms.color.value = 
        typeof color === 'string' ? 
        threeService.hexToColor(color) : 
        new THREE.Color(color);
    }
  };
  
  const updateDensity = (value) => {
    if (material) material.uniforms.density.value = value;
  };
  
  const updateSpeed = (value) => {
    if (material) material.uniforms.speed.value = value;
  };
  
  const updateIntensity = (value) => {
    if (material) material.uniforms.intensity.value = value;
  };
  
  onMounted(() => {
    const cleanup = init();
    
    onUnmounted(() => {
      if (cleanup) cleanup();
    });
  });
  
  return {
    containerRef,
    updateColor,
    updateDensity,
    updateSpeed,
    updateIntensity
  };
}
