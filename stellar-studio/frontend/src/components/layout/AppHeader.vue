<!-- src/components/layout/AppHeader.vue -->
<template>
    <v-app-bar app>
      <v-app-bar-title>
        <router-link to="/" class="text-decoration-none text-white">
          Stellar Studio
        </router-link>
      </v-app-bar-title>
  
      <v-spacer></v-spacer>
      
      <!-- Sélecteur de langue -->
      <v-btn-toggle
        v-model="currentLocale"
        mandatory
        class="mx-4"
        density="comfortable"
        @update:model-value="changeLocale"
      >
        <v-btn value="fr" variant="text">FR</v-btn>
        <v-btn value="en" variant="text">EN</v-btn>
      </v-btn-toggle>
  
      <!-- Menu pour utilisateurs non authentifiés -->
      <template v-if="!isAuthenticated">
        <v-btn to="/auth?mode=login" text>
          <v-icon start>mdi-login</v-icon>
          {{ $t('auth.login') }}
        </v-btn>
        <v-btn to="/auth?mode=register" text>
          <v-icon start>mdi-account-plus</v-icon>
          {{ $t('auth.register') }}
        </v-btn>
      </template>
  
      <!-- Menu pour utilisateurs authentifiés -->
      <template v-else>
        <v-btn to="/" text>
          <v-icon start>mdi-home</v-icon>
          {{ $t('navigation.home') }}
        </v-btn>
        <v-btn to="/processing" text>
          <v-icon start>mdi-image-filter</v-icon>
          {{ $t('navigation.processing') }}
        </v-btn>
        
        <!-- Menu utilisateur -->
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn icon v-bind="props">
              <v-icon>mdi-account-circle</v-icon>
            </v-btn>
          </template>
  
          <v-list>
            <v-list-item>
              <v-list-item-title class="text-subtitle-2">
                {{ user?.username }}
              </v-list-item-title>
            </v-list-item>
            
            <v-divider></v-divider>
            
            <v-list-item @click="handleLogout">
              <template v-slot:prepend>
                <v-icon>mdi-logout</v-icon>
              </template>
              <v-list-item-title>{{ $t('auth.logout') }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-app-bar>
  </template>
  
  <script>
  import { useAuthStore } from '../../stores/auth'
  import { storeToRefs } from 'pinia'
  import { getCurrentInstance, ref } from 'vue'
  import { useRouter } from 'vue-router'
  
  export default {
    name: 'AppHeader',
    
    emits: ['show-notification'],
  
    setup(props, { emit }) {
      const authStore = useAuthStore()
      const { isAuthenticated, user } = storeToRefs(authStore)
      const instance = getCurrentInstance()
      const router = useRouter()
      
      // Référence réactive pour la locale courante
      const currentLocale = ref(localStorage.getItem('locale') || 'fr')
      
      // Fonction pour changer la langue
      const changeLocale = (newLocale) => {
        if (instance && instance.proxy.$setLocale) {
          instance.proxy.$setLocale(newLocale)
          currentLocale.value = newLocale
        }
      }
  
      const handleLogout = async () => {
        try {
          authStore.logout()
          
          // Utilisation de i18n pour les messages
          const message = instance?.proxy?.$t('auth.logoutSuccess') || 'Successfully logged out'
          
          emit('show-notification', {
            text: message,
            color: 'success'
          })
          
          router.push('/auth')
        } catch (error) {
          // Utilisation de i18n pour les messages d'erreur
          const errorMessage = instance?.proxy?.$t('auth.logoutError') || 'Error during logout'
          
          emit('show-notification', {
            text: errorMessage,
            color: 'error'
          })
          console.error("Erreur lors de la déconnexion:", error)
        }
      }
  
      return { 
        isAuthenticated,
        user,
        handleLogout,
        currentLocale,
        changeLocale
      }
    }
  }
  </script>
  
  <style scoped>
  .v-app-bar-title {
    cursor: pointer;
  }
  
  .text-decoration-none {
    text-decoration: none;
  }
  </style>
  