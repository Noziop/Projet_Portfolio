import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Processing from '../views/Processing.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/processing',
    name: 'Processing',
    component: Processing
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
