<template>
    <v-card>
      <v-card-title>Image Viewer</v-card-title>
      <v-card-text>
        <div class="image-container">
          <!-- Zone de visualisation de l'image -->
          <div class="image-display" ref="imageDisplay">
            <!-- L'image sera rendue ici -->
          </div>
          
          <!-- Contrôles de base -->
          <v-row class="controls">
            <v-col>
              <v-slider
                v-model="contrast"
                label="Contrast"
                min="0"
                max="200"
                step="1"
              ></v-slider>
            </v-col>
            <v-col>
              <v-slider
                v-model="brightness"
                label="Brightness"
                min="0"
                max="200"
                step="1"
              ></v-slider>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
    </v-card>
  </template>
  
  <script>
  export default {
    name: 'ImageViewer',
    data() {
      return {
        contrast: 100,
        brightness: 100
      }
    },
    props: {
      imageUrl: {
        type: String,
        required: false
      }
    }
  }
  </script>
  
  <style scoped>
  .image-container {
    width: 100%;
    height: 500px;
    position: relative;
  }
  
  .image-display {
    width: 100%;
    height: 100%;
    background: #1a1a1a;
    border-radius: 4px;
  }
  
  .controls {
    padding: 1rem;
  }
  </style>
  