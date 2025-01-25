<template>
    <div ref="mountRef" class="animated-stars"></div>
  </template>
  
  <script>
  import { onMounted, onUnmounted, ref } from 'vue'
  import * as THREE from 'three'
  
  export default {
    name: 'AnimatedStars',
    props: {
      starCount: {
        type: Number,
        default: 500
      }
    },
    setup(props) {
      const mountRef = ref(null)
      let scene, camera, renderer, stars, gasClouds, animationFrameId
      let starData = []
      let gasData = []
  
      // Configuration des étoiles
      const starColors = {
        blueGiant: new THREE.Color(0x1E90FF),
        redGiant: new THREE.Color(0xFF4500),
        yellowDwarf: new THREE.Color(0xFFD700),
        whiteDwarf: new THREE.Color(0xFFFFFF),
        redDwarf: new THREE.Color(0xFF6347)
      }
  
      const starSizes = {
        blueGiant: 24,
        redGiant: 18,
        yellowDwarf: 6,
        whiteDwarf: 3,
        redDwarf: 2
      }
  
      const starDistribution = {
        blueGiant: 0.05,
        redGiant: 0.1,
        yellowDwarf: 0.2,
        whiteDwarf: 0.25,
        redDwarf: 0.4
      }
  
      // Configuration des nuages de gaz
      const gasCloudColors = {
        blueNebula: new THREE.Color(0x4B79E4),
        purpleNebula: new THREE.Color(0x9B4BE4),
        pinkNebula: new THREE.Color(0xE44B79)
      }
  
      const gasCloudSizes = {
        large: 100,
        medium: 75,
        small: 50
      }
  
      const gasCloudDistribution = {
        blueNebula: 0.3,
        purpleNebula: 0.3,
        pinkNebula: 0.4
      }
  
      const getStarType = () => {
        const rand = Math.random()
        let cumulative = 0
        for (const [type, probability] of Object.entries(starDistribution)) {
          cumulative += probability
          if (rand <= cumulative) return type
        }
        return 'redDwarf'
      }
  
      const getGasCloudType = () => {
        const rand = Math.random()
        let cumulative = 0
        for (const [type, probability] of Object.entries(gasCloudDistribution)) {
          cumulative += probability
          if (rand <= cumulative) return type
        }
        return 'pinkNebula'
      }
  
      const createStarTexture = () => {
        const canvas = document.createElement('canvas')
        canvas.width = 32
        canvas.height = 32
        const ctx = canvas.getContext('2d')
        
        const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16)
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)')
        gradient.addColorStop(0.8, 'rgba(255, 255, 255, 0.8)')
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
        
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, 32, 32)
        
        const texture = new THREE.Texture(canvas)
        texture.needsUpdate = true
        return texture
      }
  
      const createGasTexture = () => {
        const canvas = document.createElement('canvas')
        canvas.width = 64
        canvas.height = 64
        const ctx = canvas.getContext('2d')
        
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.2)')
        gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.1)')
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
        
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, 64, 64)
        
        const texture = new THREE.Texture(canvas)
        texture.needsUpdate = true
        return texture
      }
  
      const init = () => {
        scene = new THREE.Scene()
        camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000)
        renderer = new THREE.WebGLRenderer({ antialias: true })
        renderer.setSize(window.innerWidth, window.innerHeight)
        renderer.setClearColor(0x000000, 0)
        mountRef.value.appendChild(renderer.domElement)
  
        // Création des étoiles
        const starGeometry = new THREE.BufferGeometry()
        const starMaterial = new THREE.PointsMaterial({
          vertexColors: true,
          size: 4,
          sizeAttenuation: true,
          transparent: true,
          blending: THREE.AdditiveBlending,
          map: createStarTexture()
        })
  
        const positions = []
        const colors = []
        const sizes = []
  
        for (let i = 0; i < props.starCount; i++) {
          const x = Math.random() * 2000 - 1000
          const y = Math.random() * 2000 - 1000
          const z = Math.random() * 1000
          positions.push(x, y, z)
  
          const starType = getStarType()
          const color = starColors[starType]
          colors.push(color.r, color.g, color.b)
          
          const baseSize = starSizes[starType]
          sizes.push(baseSize)
          starData.push({ 
            velocity: Math.random() * 10 + 5,
            baseSize: baseSize
          })
        }
  
        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
        starGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
        starGeometry.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1))
  
        stars = new THREE.Points(starGeometry, starMaterial)
        scene.add(stars)
  
        // Création des nuages de gaz
        const gasGeometry = new THREE.BufferGeometry()
        const gasMaterial = new THREE.PointsMaterial({
          vertexColors: true,
          size: 50,
          sizeAttenuation: true,
          transparent: true,
          opacity: 0.15,
          blending: THREE.AdditiveBlending,
          map: createGasTexture()
        })
  
        const gasPositions = []
        const gasColors = []
        const gasSizes = []
        const gasCount = Math.floor(props.starCount / 5)
  
        for (let i = 0; i < gasCount; i++) {
          const x = Math.random() * 2000 - 1000
          const y = Math.random() * 2000 - 1000
          const z = Math.random() * 1000
          gasPositions.push(x, y, z)
  
          const cloudType = getGasCloudType()
          const color = gasCloudColors[cloudType]
          gasColors.push(color.r, color.g, color.b)
  
          const baseSize = gasCloudSizes[Math.random() > 0.5 ? 'large' : 'medium']
          gasSizes.push(baseSize)
          gasData.push({
            velocity: Math.random() * 5 + 2,
            baseSize: baseSize
          })
        }
  
        gasGeometry.setAttribute('position', new THREE.Float32BufferAttribute(gasPositions, 3))
        gasGeometry.setAttribute('color', new THREE.Float32BufferAttribute(gasColors, 3))
        gasGeometry.setAttribute('size', new THREE.Float32BufferAttribute(gasSizes, 1))
  
        gasClouds = new THREE.Points(gasGeometry, gasMaterial)
        scene.add(gasClouds)
  
        camera.position.z = 1000
      }
  
      const moveStars = () => {
        const positions = stars.geometry.attributes.position.array
        const sizes = stars.geometry.attributes.size.array
        
        for (let i = 0; i < props.starCount; i++) {
          const i3 = i * 3
          positions[i3 + 2] += starData[i].velocity
          
          sizes[i] = starData[i].baseSize * (1 + Math.sin(Date.now() * 0.001 + i) * 0.2)
          
          if (positions[i3 + 2] > 1000) {
            positions[i3] = Math.random() * 2000 - 1000
            positions[i3 + 1] = Math.random() * 2000 - 1000
            positions[i3 + 2] = 1
          }
        }
        
        stars.geometry.attributes.position.needsUpdate = true
        stars.geometry.attributes.size.needsUpdate = true
  
        // Animation des nuages de gaz
        const gasPositions = gasClouds.geometry.attributes.position.array
        const gasSizes = gasClouds.geometry.attributes.size.array
        const gasCount = gasData.length
  
        for (let i = 0; i < gasCount; i++) {
          const i3 = i * 3
          gasPositions[i3 + 2] += gasData[i].velocity * 0.5
  
          gasSizes[i] = gasData[i].baseSize * (1 + Math.sin(Date.now() * 0.0005 + i) * 0.3)
  
          if (gasPositions[i3 + 2] > 1000) {
            gasPositions[i3] = Math.random() * 2000 - 1000
            gasPositions[i3 + 1] = Math.random() * 2000 - 1000
            gasPositions[i3 + 2] = 1
          }
        }
  
        gasClouds.geometry.attributes.position.needsUpdate = true
        gasClouds.geometry.attributes.size.needsUpdate = true
      }
  
      const animate = () => {
        moveStars()
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
        if (mountRef.value && renderer) {
          mountRef.value.removeChild(renderer.domElement)
        }
      })
  
      return { mountRef }
    }
  }
  </script>
  
  <style scoped>
  .animated-stars {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
  }
  </style>
  