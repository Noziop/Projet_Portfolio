import { createI18n } from 'vue-i18n'
import fr from '../locales/fr.json'
import en from '../locales/en.json'

// Récupérer la langue préférée de l'utilisateur depuis le stockage local ou utiliser le français par défaut
const locale = localStorage.getItem('locale') || 'fr'

// Créer l'instance i18n
const i18n = createI18n({
  legacy: false, // Utiliser le mode Composition API
  globalInjection: true, // Injecter $t et $i18n dans tous les composants
  locale: locale, // Langue par défaut
  fallbackLocale: 'fr', // Langue de secours
  messages: {
    fr,
    en
  },
  silentTranslationWarn: process.env.NODE_ENV === 'production'
})

// Ajouter une méthode utilitaire pour changer la langue
export const setLocale = (newLocale) => {
  i18n.global.locale.value = newLocale
  localStorage.setItem('locale', newLocale)
  document.querySelector('html').setAttribute('lang', newLocale)
}

export default i18n 