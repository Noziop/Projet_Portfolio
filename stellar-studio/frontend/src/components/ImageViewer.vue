<template>
  <div class="image-viewer">
    <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
    
    <v-card v-else-if="imageUrl" class="mx-auto" max-width="700">
      <v-img
        :src="imageUrl"
        height="400"
        contain
        class="grey lighten-2"
      >
        <template v-slot:placeholder>
          <v-row class="fill-height ma-0" align="center" justify="center">
            <v-progress-circular indeterminate color="grey"></v-progress-circular>
          </v-row>
        </template>
      </v-img>
      
      <v-card-title class="text-center">{{ getFilterDisplayName(selectedFilter) }}</v-card-title>
    </v-card>
    
    <v-alert v-else type="info" outlined>
      Sélectionnez un filtre pour afficher l'image correspondante
    </v-alert>
  </div>
</template>

<script>
export default {
  name: 'ImageViewer',
  
  props: {
    targetId: String,
    selectedFilter: String,
    'image-url': String  // Reçoit directement l'URL présignée du parent
  },
  
  data() {
    return {
      loading: false,
      previewUrls: {},
      error: null
    }
  },
  
  computed: {
    imageUrl() {
      return this['image-url'];
    }
  },
  
  methods: {
    async loadPreviews() {
      if (!this.targetId) return;
      
      this.loading = true;
      
      try {
        console.log('Chargement des prévisualisations pour la cible', this.targetId);
        const response = await fetch(`/api/v1/targets/${this.targetId}/preview`);
        const data = await response.json();
        
        this.previewUrls = data.preview_urls || {};
        this.$emit('previews-loaded', data);
        console.log('Prévisualisations chargées:', this.previewUrls);
      } catch (error) {
        console.error('Erreur de chargement des prévisualisations:', error);
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    
    getFilterDisplayName(filterName) {
      if (!filterName) return 'Image prévisualisée';
      
      // Extraire le nom du filtre pour un affichage plus convivial
      const filterMatch = filterName.match(/_(f\d+\w+)_/i);
      if (filterMatch) {
        const filter = filterMatch[1].toUpperCase();
        
        // Mapper les codes de filtres aux noms
        const filterNames = {
          'F187N': 'Filtre H-alpha (1.87 µm)',
          'F444W': 'Filtre OIII (4.44 µm)',
          'F470N': 'Filtre OIII étroit (4.70 µm)',
          'F090W': 'Filtre Bleu (0.90 µm)',
          'F200W': 'Filtre Vert-Bleu (2.00 µm)',
          'F335M': 'Filtre Vert (3.35 µm)',
          'F770W': 'Filtre Rouge (7.70 µm)',
          'F1130W': 'Filtre Rouge lointain (11.30 µm)',
          'F1500W': 'Filtre Infrarouge (15.00 µm)'
        };
        
        return filterNames[filter] || `Filtre ${filter}`;
      }
      
      return 'Image prévisualisée';
    }
  },
  
  watch: {
    targetId() {
      this.loadPreviews();
    }
  },
  
  mounted() {
    console.log("ImageViewer monté avec targetId =", this.targetId);
    if (this.targetId) {
      this.loadPreviews();
    } else {
      console.warn("targetId est vide, appel API impossible!");
    }

    if (this.targetId) {
      this.loadPreviews();
    }
  }
}
</script>

<style scoped>
.image-viewer {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 450px;
}
</style>
