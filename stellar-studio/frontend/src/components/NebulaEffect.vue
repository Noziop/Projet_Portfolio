<template>
    <div ref="nebulaRef" class="nebula-container"></div>
  </template>
  
  <script>
  import { onMounted, onUnmounted, ref } from 'vue'
  import * as THREE from 'three'
  import { createNoise2D } from 'simplex-noise'
  
  export default {
    name: 'NebulaEffect',
    
    setup() {
      const nebulaRef = ref(null)
      let scene, camera, renderer
      let animationFrameId
      const noise2D = createNoise2D()
  
      const createNebulaTexture = () => {
  const size = 512
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  
  const imageData = ctx.createImageData(size, size)
  const data = imageData.data
  
  const center = size / 2
  
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4
      
      const dx = x - center
      const dy = y - center
      const distance = Math.sqrt(dx * dx + dy * dy)
      const maxDistance = Math.sqrt(2) * center
      
      let noiseValue = 0
      let amplitude = 1
      let frequency = 1
      
      for (let o = 0; o < 4; o++) {
        noiseValue += amplitude * (noise2D(x * frequency / 100, y * frequency / 100) + 1) / 2
        amplitude *= 0.5
        frequency *= 2
      }
      
      // Adoucissement des bords avec une fonction de lissage
      const edgeFactor = Math.pow(Math.max(0, 1 - (distance / maxDistance)), 2)
      noiseValue = noiseValue * edgeFactor
      
      // Variation de couleur avec transition plus douce
      const colorPhase = (y / size) * Math.PI
      const edgeColorFactor = Math.pow(edgeFactor, 0.5) // Transition plus progressive des couleurs

      data[i] = noiseValue * (300 * Math.sin(colorPhase)) * edgeColorFactor
      data[i + 1] = noiseValue * (150 * Math.cos(colorPhase)) * edgeColorFactor
      data[i + 2] = noiseValue * (300 * Math.sin(colorPhase + Math.PI/2)) * edgeColorFactor
      data[i + 3] = noiseValue * 60 * edgeColorFactor
    }
  }
  
  ctx.putImageData(imageData, 0, 0)
  
  const texture = new THREE.CanvasTexture(canvas)
  texture.needsUpdate = true
  return texture
}


  
      const init = () => {
        scene = new THREE.Scene()
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000)
        
        renderer = new THREE.WebGLRenderer({ 
          antialias: true,
          alpha: true 
        })
        renderer.setSize(window.innerWidth, window.innerHeight)
        nebulaRef.value.appendChild(renderer.domElement)
  
        // Création de plusieurs plans de nébuleuse
        for (let i = 0; i < 3; i++) {
          const geometry = new THREE.PlaneGeometry(2000, 2000)
          const material = new THREE.MeshBasicMaterial({
            map: createNebulaTexture(),
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            opacity: 0.4, // Augmenté de 0.2 à 0.4
            side: THREE.DoubleSide
          })
  
          const mesh = new THREE.Mesh(geometry, material)
          mesh.position.z = -500 - (i * 200)
          mesh.rotation.z = Math.random() * Math.PI
          scene.add(mesh)
        }
  
        camera.position.z = 1000
      }
  
      const animate = () => {
        scene.children.forEach((mesh, index) => {
          // Augmentation de la vitesse (de 0.1 à 0.5)
          mesh.position.z += 0.5
          if (mesh.position.z > 1000) {
            mesh.position.z = -1000
          }
          
          mesh.rotation.z += 0.00005 * (index + 1)
        })

        renderer.render(scene, camera)
        animationFrameId = requestAnimationFrame(animate)
      }
  
      const handleResize = () => {
        if (camera && renderer) {
          camera.aspect = window.innerWidth / window.innerHeight
          camera.updateProjectionMatrix()
          renderer.setSize(window.innerWidth, window.innerHeight)
        }
      }
  
      onMounted(() => {
        init()
        animate()
        window.addEventListener('resize', handleResize)
      })
  
      onUnmounted(() => {
        window.removeEventListener('resize', handleResize)
        cancelAnimationFrame(animationFrameId)
        if (nebulaRef.value && renderer) {
          nebulaRef.value.removeChild(renderer.domElement)
        }
      })
  
      return { nebulaRef }
    }
  }
  </script>
  
  <style scoped>
  .nebula-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
  }
  </style>
  