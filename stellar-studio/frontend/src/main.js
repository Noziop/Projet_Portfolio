import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import i18n, { setLocale } from './i18n'
import { createWebSocket } from './services/websocket'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark'
  }
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(i18n)

// Ajouter une méthode globale pour changer la langue
app.config.globalProperties.$setLocale = setLocale

// Récupérer la langue actuelle et la définir comme attribut sur l'élément HTML
document.querySelector('html').setAttribute('lang', i18n.global.locale.value)

app.mount('#app')

// Initialiser le WebSocket mais en mode désactivé (false)
try {
  createWebSocket(false) // Le WebSocket est désactivé par défaut
  console.log('Service WebSocket initialisé mais désactivé')
} catch (error) {
  console.error('Erreur lors de l\'initialisation du service WebSocket:', error)
}

// Pour faciliter le débogage
window.__app = app
