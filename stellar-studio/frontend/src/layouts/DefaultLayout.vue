<template>
  <v-app>
    <app-header @show-notification="showNotification" />
    
    <v-main>
      <slot></slot>
    </v-main>

    <app-footer />

    <!-- Snackbar pour les notifications -->
    <v-snackbar
      v-model="showNotificationBar"
      :color="notificationColor"
      :timeout="3000"
    >
      {{ notificationText }}
    </v-snackbar>
  </v-app>
</template>

<script>
import AppHeader from '../components/layout/AppHeader.vue'
import AppFooter from '../components/layout/AppFooter.vue'

export default {
  name: 'DefaultLayout',
  
  components: {
    AppHeader,
    AppFooter
  },

  data() {
    return {
      showNotificationBar: false,
      notificationText: '',
      notificationColor: 'success'
    }
  },

  methods: {
    showNotification({ text, color }) {
      this.notificationText = text
      this.notificationColor = color
      this.showNotificationBar = true
    }
  }
}
</script>
