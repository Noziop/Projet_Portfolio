<template>
  <div class="image-viewer">
    <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
    
    <v-card v-else-if="displayImageUrl" class="mx-auto" width="100%">
      <v-img
        :src="displayImageUrl"
        min-height="100%"
        max-width="100%"
        contain
        class="grey lighten-2 image-container"
        @error="handleImageError"
        @click="isZoomed = !isZoomed"
        :style="isZoomed ? 'height: 80vh; cursor: zoom-out;' : 'height: 50vh; cursor: zoom-in;'"
      >
        <template v-slot:placeholder>
          <v-row class="fill-height ma-0" align="center" justify="center">
            <v-progress-circular indeterminate color="grey"></v-progress-circular>
          </v-row>
        </template>
      </v-img>
      
      <v-card-title class="text-center">{{ getFilterDisplayName(selectedFilter) }}</v-card-title>
      
      <!-- Debug info visible seulement en dev -->
      <v-card-text v-if="imageError" class="error--text">
        Erreur: {{ imageError }}
      </v-card-text>
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
    previewUrls: {
      type: Object,
      default: () => ({})
    },
    'image-url': String  // Support direct de l'URL d'image
  },
  
  data() {
    return {
      loading: false,
      imageError: null,
      isZoomed: false,
      fixedUrl: null  // URL réparée en cas de problème avec l'URL originale
    }
  },
  
  computed: {
    displayImageUrl() {
      console.log("🧪 Débogage props:", {
        // ton code de débogage actuel
      });
      
      // Ajouter les returns nécessaires!
      if (this.fixedUrl) return this.fixedUrl;
      if (this['image-url']) return this.fixImageUrl(this['image-url']);
      if (this.selectedFilter && this.previewUrls && this.previewUrls[this.selectedFilter]) {
        return this.fixImageUrl(this.previewUrls[this.selectedFilter]);
      }
      
      return null;
    }
  },

  methods: {
    // Version simplifiée qui ajoute juste le token d'authentification aux URLs d'API
    fixImageUrl(url) {
      if (!url) return null;
      
      // Si c'est déjà une URL de notre API
      if (url.startsWith('/api/v1/')) {
        // Récupérer le token depuis localStorage
        const token = localStorage.getItem('token');
        
        if (token) {
          // Créer une URL complète avec l'authentification dans les en-têtes
          const headers = new Headers();
          headers.append('Authorization', `Bearer ${token}`);
          
          // On utilise fetch pour charger l'image avec le token
          fetch(url, { headers })
            .then(response => response.blob())
            .then(blob => {
              // Créer une URL d'objet temporaire pour l'image
              const imageUrl = URL.createObjectURL(blob);
              this.fixedUrl = imageUrl; // Stocker l'URL transformée
            })
            .catch(error => {
              console.error('Erreur chargement image avec token:', error);
              this.imageError = "Erreur d'authentification";
            });
            
          // Retourner une URL vide en attendant que l'image soit chargée
          return url;
        }
      }
      
      // Pour les anciennes URLs (à supprimer à terme)
      if (url.includes('minio:9000')) {
        return null; // On ne gère plus les URLs minio directes
      }
      
      return url;
    },
    
    handleImageError(e) {
      console.error('Erreur de chargement d\'image:', e);
      this.imageError = "Impossible de charger l'image";
      
      // Si c'est une URL d'API, probablement un problème d'authentification
      if (this.displayImageUrl && this.displayImageUrl.startsWith('/api/v1/')) {
        // Essayer de recharger avec fetch + token
        const token = localStorage.getItem('token');
        
        if (token) {
          fetch(this.displayImageUrl, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          .then(response => {
            if (!response.ok) throw new Error(`${response.status}: ${response.statusText}`);
            return response.blob();
          })
          .then(blob => {
            const imageUrl = URL.createObjectURL(blob);
            this.fixedUrl = imageUrl;
            this.imageError = null;
          })
          .catch(err => {
            console.error('Échec du chargement avec token:', err);
          });
        }
      }
    },    
    // Teste plusieurs transformations d'URL pour trouver celle qui fonctionne
    async testUrlTransformations(urlOptions) {
      for (const url of urlOptions) {
        try {
          const response = await fetch(url, { method: 'HEAD' });
          if (response.ok) {
            console.log('URL réparée trouvée:', url);
            this.fixedUrl = url;
            this.imageError = null;
            return;
          }
        } catch (err) {
          console.log('Transformation échouée:', url);
        }
      }
      console.error('Toutes les transformations ont échoué');
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
        
        // Extraction du nom de la cible (M16 = Eagle Nebula)
        const targetName = "M16";
        
        // Construction du message formaté
        return `${this.targetId || 'Target'} : ${filter} / Vue de ${targetName} avec un ${filterNames[filter] || `Filtre ${filter}`}`;
      }
      
      return 'Image prévisualisée';
    }
  },
  
  watch: {
    // Surveille les changements d'URL ou de filtre
    displayImageUrl(newUrl) {
      if (newUrl) {
        this.loading = true;
        this.imageError = null;
        setTimeout(() => {
          this.loading = false;
        }, 300);
      }
    },
    
    // Réinitialiser l'URL fixée quand le filtre change
    selectedFilter() {
      this.fixedUrl = null;
      this.imageError = null;
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
