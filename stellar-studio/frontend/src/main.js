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

// Pour faciliter le débogage
window.__app = app
