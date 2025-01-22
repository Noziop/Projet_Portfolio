import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Processing from '../views/Processing.vue'
import AuthContainer from '../views/auth/AuthContainer.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/processing',
    name: 'Processing',
    component: Processing,
    meta: { requiresAuth: true }
  },
  {
    path: '/auth',
    name: 'Auth',
    component: AuthContainer
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/auth')
  } else {
    next()
  }
})

export default router
