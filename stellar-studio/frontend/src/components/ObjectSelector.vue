<template>
  <v-card>
    <v-card-title>Select Target</v-card-title>
    <v-card-text>
      <v-select
        v-model="selectedTelescope"
        :items="telescopes"
        label="Select Telescope"
        item-title="name"
        item-value="id"
        @update:model-value="loadTargets"
        :loading="loadingTelescopes"
        :disabled="loadingTelescopes"
      ></v-select>

      <v-select
        v-model="selectedTarget"
        :items="availableTargets"
        label="Select Target"
        item-title="name"
        item-value="id"
        :disabled="!selectedTelescope || loading"
        :loading="loading"
      ></v-select>

      <v-btn
        block
        color="primary"
        :disabled="!selectedTarget"
        :loading="downloadLoading"
        @click="downloadFits"
      >
        Download FITS
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api'

export default {
  name: 'ObjectSelector',
  
  setup(props, { emit }) {
    const selectedTelescope = ref(null)
    const selectedTarget = ref(null)
    const availableTargets = ref([])
    const telescopes = ref([])
    const loading = ref(false)
    const loadingTelescopes = ref(false)
    const downloadLoading = ref(false)
    const downloadStatus = ref('idle') // 'idle', 'downloading', 'success', 'error'

    // Récupération des télescopes disponibles depuis l'API
    const loadTelescopes = async () => {
      loadingTelescopes.value = true
      try {
        console.log("Tentative de récupération des télescopes via:", apiClient.defaults.baseURL);
        
        // Forcer HTTPS pour résoudre le problème de mixed content
        const url = '/telescopes/';
        console.log("URL complète:", window.location.origin + apiClient.defaults.baseURL + url);
        
        const response = await apiClient.get(url, { 
          params: { status: 'online' }
        })
        telescopes.value = response.data
        console.log("Télescopes récupérés:", response.data);
        
        // Si aucun télescope n'est sélectionné mais qu'on a des télescopes disponibles
        if (!selectedTelescope.value && telescopes.value.length > 0) {
          selectedTelescope.value = telescopes.value[0].id
          loadTargets() // Charger les cibles pour le premier télescope
        }
      } catch (error) {
        console.error('Échec du chargement des télescopes:', error);
        
        if (error.message && error.message.includes('Mixed Content')) {
          console.error('Erreur de mixed content détectée - problème avec HTTPS');
        }
        
        emit('error', 'Échec du chargement des télescopes');
        // Utilisation de valeurs par défaut en cas d'erreur
        telescopes.value = [
          { id: 'HST', name: 'Hubble Space Telescope' },
          { id: 'JWST', name: 'James Webb Space Telescope' }
        ]
      } finally {
        loadingTelescopes.value = false
      }
    }

    const loadTargets = async () => {
      if (!selectedTelescope.value) return
      
      loading.value = true
      selectedTarget.value = null // Réinitialiser la cible sélectionnée
      
      try {
        console.log(`Chargement des cibles pour le télescope ${selectedTelescope.value}`);
        
        // Essayer avec différentes variantes de paramètres pour résoudre le problème de filtrage
        const params = {
          telescope_id: selectedTelescope.value,
        };
        
        console.log("Paramètres de requête:", params);
        
        const response = await apiClient.get(`/targets/`, { params })
        
        console.log("Réponse brute:", response);
        console.log("Cibles récupérées:", response.data);
        console.log("Nombre de cibles:", response.data.length);
        
        // Filtrer côté client si le backend ne le fait pas correctement
        const filteredTargets = response.data.filter(target => {
          // On vérifie si le target possède une propriété telescope qui correspond
          return target.telescope === selectedTelescope.value || 
                 target.telescope_id === selectedTelescope.value;
        });
        
        console.log("Nombre de cibles après filtrage client:", filteredTargets.length);
        
        // Utiliser les cibles filtrées si le nombre est différent (ce qui indiquerait un problème de filtrage backend)
        if (filteredTargets.length !== response.data.length && filteredTargets.length > 0) {
          console.log("Filtrage appliqué côté client car le backend ne filtre pas correctement");
          availableTargets.value = filteredTargets;
        } else {
          availableTargets.value = response.data;
        }
      } catch (error) {
        console.error('Échec du chargement des cibles:', error);
        
        if (error.message && error.message.includes('Mixed Content')) {
          console.error('Erreur de mixed content détectée lors du chargement des cibles - problème avec HTTPS');
        }
        
        emit('error', 'Échec du chargement des cibles')
        availableTargets.value = []
      } finally {
        loading.value = false
      }
    }

    const downloadFits = async () => {
      if (!selectedTarget.value || !selectedTelescope.value) return

      downloadLoading.value = true
      downloadStatus.value = 'downloading'
      
      try {
        // Trouver le target sélectionné pour avoir son nom
        const target = availableTargets.value.find(t => t.id === selectedTarget.value)
        
        const response = await apiClient.post(`/tasks/download`, {
          telescope: selectedTelescope.value,
          object_name: target.name  // On envoie le nom au lieu de l'ID
        })
        
        emit('download-started', {
          taskId: response.data.task_id,
          message: `Téléchargement démarré pour ${target.name}`
        })
        
        monitorDownload(response.data.task_id)
      } catch (error) {
        console.error('Échec du démarrage du téléchargement:', error)
        emit('error', 'Échec du démarrage du téléchargement')
        downloadStatus.value = 'error'
      } finally {
        downloadLoading.value = false
      }
    }

    const monitorDownload = async (taskId) => {
      const checkStatus = async () => {
        try {
          const response = await apiClient.get(`/tasks/${taskId}`)
          
          if (response.data.status === 'SUCCESS') {
            if (response.data.result.status === 'success') {
              downloadStatus.value = 'success'
              emit('download-complete', {
                files: response.data.result.files,
                message: response.data.result.message  // On transmet le message de succès
              })
              return true
            } else if (response.data.result.status === 'error') {
              downloadStatus.value = 'error'
              emit('error', response.data.result.message)
              return true
            }
          } else if (response.data.status === 'PENDING') {
            emit('download-progress', 'Téléchargement en cours...')
          } else if (response.data.status === 'PROGRESS') {
            emit('download-progress', {
              status: 'progress',
              message: response.data.result?.status || 'Téléchargement en cours...'
            })
          } else if (response.data.status === 'FAILURE') {
            downloadStatus.value = 'error'
            emit('error', response.data.result || 'Échec du téléchargement')
            return true
          }
          return false
        } catch (error) {
          console.error('Échec de la vérification du statut:', error)
          downloadStatus.value = 'error'
          emit('error', 'Erreur lors de la vérification du statut')
          return true
        }
      }

      const interval = setInterval(async () => {
        const done = await checkStatus()
        if (done) clearInterval(interval)
      }, 2000)

      // Nettoyage après 5 minutes
      setTimeout(() => {
        clearInterval(interval)
        if (downloadStatus.value === 'downloading') {
          downloadStatus.value = 'error'
          emit('error', 'Le téléchargement a expiré')
        }
      }, 300000)
    }

    // Charger les télescopes au montage du composant
    onMounted(() => {
      loadTelescopes()
    })

    return {
      selectedTelescope,
      selectedTarget,
      telescopes,
      availableTargets,
      loading,
      loadingTelescopes,
      downloadLoading,
      downloadStatus,
      loadTargets,
      downloadFits
    }
  }
}
</script>