import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Processing from '../views/Processing.vue'
import AuthContainer from '../views/auth/AuthContainer.vue'
import TelescopeData from '../views/TelescopeData.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { transition: 'lightspeed' }
  },
  {
    path: '/processing',
    name: 'Processing',
    component: Processing,
    meta: { requiresAuth: true, transition: 'lightspeed' }
  },
  {
    path: '/telescopes',
    name: 'TelescopeData',
    component: TelescopeData,
    meta: { requiresAuth: true, transition: 'lightspeed' }
  },  
  {
    path: '/auth',
    name: 'Auth',
    component: AuthContainer,
    meta: { requiresUnauth: true, transition: 'lightspeed' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Vérifie l'authentification au démarrage
  if (authStore.token && !authStore.user) {
    authStore.getMe()
  }

  // Gestion des routes protégées
  if (to.meta.requiresAuth) {
    if (!authStore.checkAuth()) {
      next('/auth')
    } else {
      next()
    }
  } 
  // Empêche l'accès à /auth si déjà connecté
  else if (to.meta.requiresUnauth && authStore.checkAuth()) {
    next('/')
  }
  else {
    next()
  }
})

export default router
