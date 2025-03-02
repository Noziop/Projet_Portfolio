<!-- src/components/layout/AppHeader.vue -->
<template>
    <v-app-bar app>
      <v-app-bar-title>
        <router-link to="/" class="text-decoration-none text-white">
          <span class="glitch" data-text="Stellar Studio">Stellar Studio</span>
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
  import { Glitch } from 'vue-glitch'
  
  export default {
    name: 'AppHeader',
    
    components: {
      Glitch
    },
    
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
  
  /* Styles pour l'effet glitch subliminal */
  .glitch {
    position: relative;
    color: white;
    font-weight: bold;
  }
  
  .glitch::before,
  .glitch::after {
    content: attr(data-text);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    will-change: transform, opacity;
    pointer-events: none;
  }
  
  .glitch::before {
    color: #0ff; /* Bleu néon */
    text-shadow: 0 0 2px #0ff;
    animation: glitch-flash-1 23.9s step-end infinite;
  }
  
  .glitch::after {
    color: #f0f; /* Rose néon */
    text-shadow: 0 0 2px #f0f;
    animation: glitch-flash-2 23.9s step-end infinite;
  }

  /* Animation pour le bleu néon - les positions sont en pourcentage de la durée totale */
  @keyframes glitch-flash-1 {
    /* Flash 1 - Haut-gauche */
    7.213% { 
      opacity: 0.9; 
      transform: translate(-2px, -2px); 
    }
    8.923% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 2 - Bas-gauche */
    19.317% { 
      opacity: 0.9; 
      transform: translate(-1.5px, 1.5px); 
    }
    19.530% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 3 - Haut-droite avec flash prolongé légèrement */
    37.641% { 
      opacity: 0.95; 
      transform: translate(1.7px, -1.3px); 
    }
    37.755% { opacity: 0.5; transform: translate(0.7px, -0.7px); }
    37.860% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 4 - Décalage léger vertical */
    54.123% { 
      opacity: 0.95; 
      transform: translate(0, -2px); 
    }
    54.333% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 5 - Horizontal puis vertical (double flash très rapide) */
    67.871% { opacity: 0.92; transform: translate(2.5px, 0); }
    67.981% { opacity: 0.3; transform: translate(1px, 0); }
    68.085% { opacity: 0.98; transform: translate(0, 2.5px); }
    68.295% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 6 - Diagonal fort */
    89.431% { 
      opacity: 0.95; 
      transform: translate(-2.5px, 2px); 
    }
    89.641% { opacity: 0; transform: translate(0, 0); }
  }

  /* Animation pour le rose néon - en opposition de phase avec le bleu */
  @keyframes glitch-flash-2 {
    /* Flash 1 - Bas-droite (opposé au bleu) */
    7.213% { 
      opacity: 0.9; 
      transform: translate(2px, 2px); 
    }
    8.923% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 2 - Haut-droite */
    19.317% { 
      opacity: 0.9; 
      transform: translate(1.5px, -1.5px); 
    }
    19.530% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 3 - Bas-gauche avec flash prolongé légèrement */
    37.641% { 
      opacity: 0.95; 
      transform: translate(-1.7px, 1.3px); 
    }
    37.755% { opacity: 0.5; transform: translate(-0.7px, 0.7px); }
    37.860% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 4 - Décalage léger vertical opposé */
    54.123% { 
      opacity: 0.95; 
      transform: translate(0, 2px); 
    }
    54.333% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 5 - Vertical puis horizontal (double flash très rapide, inversé par rapport au bleu) */
    67.871% { opacity: 0.92; transform: translate(0, -2.5px); }
    67.981% { opacity: 0.3; transform: translate(0, -1px); }
    68.085% { opacity: 0.98; transform: translate(-2.5px, 0); }
    68.295% { opacity: 0; transform: translate(0, 0); }
    
    /* Flash 6 - Diagonal fort opposé */
    89.431% { 
      opacity: 0.95; 
      transform: translate(2.5px, -2px); 
    }
    89.641% { opacity: 0; transform: translate(0, 0); }
  }
  </style>
  