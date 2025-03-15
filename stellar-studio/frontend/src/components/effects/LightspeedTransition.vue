<!-- src/components/effects/LightspeedTransition.vue -->
<template>
    <div 
      ref="transitionContainer" 
      class="lightspeed-transition"
      :class="{ 'active': active }"
    ></div>
  </template>
  
  <script>
  import { ref, watch } from 'vue';
  import * as THREE from 'three';
  
  export default {
    name: 'LightspeedTransition',
    
    props: {
      active: {
        type: Boolean,
        default: false
      },
      duration: {
        type: Number,
        default: 2000
      },
      color: {
        type: String,
        default: '#ffffff'
      }
    },
    
    emits: ['transition-complete'],
    
    setup(props, { emit }) {
      const transitionContainer = ref(null);
      let scene, camera, renderer, stars, animationId;
      let startTime = 0;
      
      const init = () => {
        if (!transitionContainer.value) return;
        
        const container = transitionContainer.value;
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(90, width / height, 0.1, 2000);
        camera.position.z = 20;
        
        renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize(width, height);
        container.appendChild(renderer.domElement);
        
        // Créer l'effet de vitesse lumière
        const starsGeometry = new THREE.BufferGeometry();
        const starCount = 5000;
        
        const positions = new Float32Array(starCount * 3);
        const velocities = new Float32Array(starCount);
        const sizes = new Float32Array(starCount);
        
        for (let i = 0; i < starCount; i++) {
          positions[i * 3] = (Math.random() - 0.5) * 100;
          positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
          positions[i * 3 + 2] = Math.random() * 500;
          
          velocities[i] = Math.random() * 0.2 + 0.1;
          sizes[i] = Math.random() * 2 + 0.5;
        }
        
        starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        starsGeometry.setAttribute('velocity', new THREE.BufferAttribute(velocities, 1));
        starsGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        
        const starsMaterial = new THREE.PointsMaterial({
          color: props.color,
          size: 1,
          transparent: true,
          blending: THREE.AdditiveBlending,
          sizeAttenuation: true
        });
        
        stars = new THREE.Points(starsGeometry, starsMaterial);
        scene.add(stars);
        
        // Gestionnaire de redimensionnement
        const handleResize = () => {
          const newWidth = container.clientWidth;
          const newHeight = container.clientHeight;
          
          camera.aspect = newWidth / newHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(newWidth, newHeight);
        };
        
        window.addEventListener('resize', handleResize);
        
        return () => {
          window.removeEventListener('resize', handleResize);
          
          if (animationId) {
            cancelAnimationFrame(animationId);
          }
          
          if (renderer) {
            if (container.contains(renderer.domElement)) {
              container.removeChild(renderer.domElement);
            }
            renderer.dispose();
          }
          
          if (stars) {
            stars.geometry.dispose();
            stars.material.dispose();
          }
        };
      };
      
      const animate = (timestamp) => {
        if (!startTime) startTime = timestamp;
        
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / props.duration, 1);
        
        if (stars) {
          const positions = stars.geometry.attributes.position.array;
          const velocities = stars.geometry.attributes.velocity.array;
          const sizes = stars.geometry.attributes.size.array;
          
          for (let i = 0; i < velocities.length; i++) {
            // Accélération progressive pendant la transition
            const acceleration = props.active ? 
              Math.min(progress * 20, 15) : 
              Math.max((1 - progress) * 15, 0);
            
            positions[i * 3 + 2] -= velocities[i] * acceleration;
            
            // Effet de traînée
            const stretch = props.active ? 
              Math.min(progress * 3, 2) : 
              Math.max((1 - progress) * 2, 0);
            
            sizes[i] = (Math.random() * 2 + 0.5) * (1 + stretch);
            
            // Réinitialiser les étoiles qui sortent du champ de vision
            if (positions[i * 3 + 2] < -100) {
              positions[i * 3] = (Math.random() - 0.5) * 100;
              positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
              positions[i * 3 + 2] = 500;
            }
          }
          
          stars.geometry.attributes.position.needsUpdate = true;
          stars.geometry.attributes.size.needsUpdate = true;
        }
        
        renderer.render(scene, camera);
        
        if (progress < 1) {
          animationId = requestAnimationFrame(animate);
        } else {
          emit('transition-complete');
          startTime = 0;
        }
      };
      
      watch(() => props.active, (newActive) => {
        if (!transitionContainer.value) return;
        
        startTime = 0;
        
        if (animationId) {
          cancelAnimationFrame(animationId);
        }
        
        if (newActive) {
          animationId = requestAnimationFrame(animate);
        }
      });
      
      return {
        transitionContainer,
        init
      };
    }
  }
  </script>
  
  <style scoped>
  .lightspeed-transition {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .lightspeed-transition.active {
    opacity: 1;
  }
  </style>
  