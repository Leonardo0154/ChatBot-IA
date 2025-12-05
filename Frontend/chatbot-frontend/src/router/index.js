import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ChatbotView from '../views/ChatbotView.vue'
import { getSession } from '@/services/session'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/chat', name: 'chat', component: ChatbotView, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const session = getSession()
  if (to.meta.requiresAuth && !session) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  if ((to.name === 'login' || to.name === 'register') && session) {
    next({ name: 'chat' })
    return
  }
  next()
})

export default router
