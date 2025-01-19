<template>
    <v-card>
      <v-card-title>Object Selection</v-card-title>
      <v-card-text>
        <v-autocomplete
          v-model="selectedObject"
          :items="celestialObjects"
          label="Search celestial objects"
          :loading="isLoading"
          :search-input.sync="search"
          placeholder="Type to search (e.g., 'Orion Nebula')"
          prepend-icon="mdi-telescope"
          return-object
        ></v-autocomplete>
  
        <v-select
          v-model="selectedTelescope"
          :items="telescopes"
          label="Select Telescope"
          prepend-icon="mdi-satellite-variant"
        ></v-select>
  
        <v-btn
          block
          color="primary"
          :loading="isDownloading"
          :disabled="!selectedObject || !selectedTelescope"
          @click="downloadFits"
        >
          Download FITS Data
        </v-btn>
      </v-card-text>
    </v-card>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'ObjectSelector',
    data() {
      return {
        selectedObject: null,
        selectedTelescope: null,
        celestialObjects: [],
        telescopes: ['HST', 'JWST'],
        isLoading: false,
        isDownloading: false,
        search: null
      }
    },
    methods: {
      async downloadFits() {
        if (!this.selectedObject || !this.selectedTelescope) return
  
        this.isDownloading = true
        try {
          const response = await axios.get(
            `/api/v1/telescopes/objects/${encodeURIComponent(this.selectedObject)}/fits`,
            {
              params: {
                telescope: this.selectedTelescope
              }
            }
          )
          this.$emit('download-started', response.data)
        } catch (error) {
          console.error('Download error:', error)
        } finally {
          this.isDownloading = false
        }
      }
    },
    watch: {
      async search(val) {
        if (!val) return
        
        this.isLoading = true
        try {
          // TODO: Implement search functionality
          this.celestialObjects = ['Orion Nebula', 'Andromeda Galaxy', 'Crab Nebula']
        } catch (error) {
          console.error('Search error:', error)
        } finally {
          this.isLoading = false
        }
      }
    }
  }
  </script>
  