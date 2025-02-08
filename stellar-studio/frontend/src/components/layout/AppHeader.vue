<!-- src/components/layout/AppHeader.vue -->
<template>
    <v-app-bar app>
      <v-app-bar-title>
        <router-link to="/" class="text-decoration-none text-white">
          Stellar Studio
        </router-link>
      </v-app-bar-title>
  
      <v-spacer></v-spacer>
  
      <!-- Menu pour utilisateurs non authentifiés -->
      <template v-if="!isAuthenticated">
        <v-btn to="/auth" text>
          <v-icon start>mdi-login</v-icon>
          Login
        </v-btn>
        <v-btn to="/auth" text>
          <v-icon start>mdi-account-plus</v-icon>
          Register
        </v-btn>
      </template>
  
      <!-- Menu pour utilisateurs authentifiés -->
      <template v-else>
        <v-btn to="/" text>
          <v-icon start>mdi-home</v-icon>
          Home
        </v-btn>
        <v-btn to="/processing" text>
          <v-icon start>mdi-image-filter</v-icon>
          Processing
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
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-app-bar>
  </template>
  
  <script>
  import { useAuthStore } from '../../stores/auth'
  import { storeToRefs } from 'pinia'
  
  export default {
    name: 'AppHeader',
    
    emits: ['show-notification'],
  
    setup(props, { emit }) {
      const authStore = useAuthStore()
      const { isAuthenticated, user } = storeToRefs(authStore)
  
      const handleLogout = async () => {
        try {
          authStore.logout()
          emit('show-notification', {
            text: 'Successfully logged out',
            color: 'success'
          })
          router.push('/auth')
        } catch (error) {
          emit('show-notification', {
            text: 'Error during logout',
            color: 'error'
          })
        }
      }
  
      return { 
        isAuthenticated,
        user,
        handleLogout
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
  