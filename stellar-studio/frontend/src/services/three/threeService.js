// src/services/three/threeService.js
import * as THREE from 'three';

export default {
  // Crée une scène Three.js de base
  createScene(container, options = {}) {
    if (!container) return null;
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Configuration de base
    const scene = new THREE.Scene();
    
    // Caméra avec paramètres personnalisables
    const fov = options.fov || 75;
    const near = options.near || 0.1;
    const far = options.far || 1000;
    
    const camera = new THREE.PerspectiveCamera(fov, width / height, near, far);
    camera.position.z = options.cameraZ || 5;
    
    // Renderer avec options
    const renderer = new THREE.WebGLRenderer({ 
      alpha: true, 
      antialias: options.antialias !== false 
    });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Gestionnaire de redimensionnement
    const handleResize = () => {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    
    window.addEventListener('resize', handleResize);
    
    // Fonction de nettoyage
    const cleanup = () => {
      window.removeEventListener('resize', handleResize);
      
      if (renderer) {
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
        renderer.dispose();
      }
    };
    
    return {
      scene,
      camera,
      renderer,
      cleanup
    };
  },
  
  // Crée des étoiles pour les fonds
  createStarField(scene, count = 1000, size = 0.7) {
    const starsGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
      positions[i * 3 + 2] = Math.random() * 2000 - 1000;
    }
    
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const starsMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: size,
      transparent: true,
      sizeAttenuation: true
    });
    
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);
    
    return {
      stars,
      geometry: starsGeometry,
      material: starsMaterial,
      
      // Méthode pour nettoyer les ressources
      dispose: () => {
        scene.remove(stars);
        starsGeometry.dispose();
        starsMaterial.dispose();
      }
    };
  },
  
  // Crée un shader de nébuleuse
  createNebulaMaterial(options = {}) {
    return new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color: { value: new THREE.Color(options.color || 0x3366ff) },
        density: { value: options.density || 0.5 },
        speed: { value: options.speed || 0.2 },
        intensity: { value: options.intensity || 1.5 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform vec3 color;
        uniform float density;
        uniform float speed;
        uniform float intensity;
        varying vec2 vUv;
        
        // Fonction de bruit simplifiée
        float noise(vec2 p) {
          return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
        }
        
        void main() {
          vec2 uv = vUv;
          
          // Animation basée sur le temps
          float t = time * speed;
          
          // Génération de brume nébuleuse
          float n1 = noise(uv * 3.0 + vec2(t * 0.5, t * 0.3));
          float n2 = noise(uv * 6.0 - vec2(t * 0.2, t * 0.4));
          
          float nebula = smoothstep(0.3, 0.7, mix(n1, n2, 0.5)) * density;
          
          // Ajout d'étoiles
          float stars = pow(noise(uv * 40.0), 20.0) * intensity;
          
          // Mélange de la nébuleuse et des étoiles
          vec3 finalColor = color * nebula + vec3(stars);
          
          gl_FragColor = vec4(finalColor, nebula * 0.8 + stars);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending
    });
  },
  
  // Utilitaire pour convertir une couleur hexadécimale en objet THREE.Color
  hexToColor(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return new THREE.Color(0x3366ff);
    
    return new THREE.Color(
      parseInt(result[1], 16) / 255,
      parseInt(result[2], 16) / 255,
      parseInt(result[3], 16) / 255
    );
  }
};
