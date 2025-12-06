import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ChatbotView from '../views/ChatbotView.vue'
import { getSession } from '@/services/session'
import AssignmentsView from '../views/AssignmentsView.vue'
import MemoryGameView from '../views/MemoryGameView.vue'
import GuidedSessionView from '../views/GuidedSessionView.vue'
import AssignmentDetailView from '../views/AssignmentDetailView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/chat', name: 'chat', component: ChatbotView, meta: { requiresAuth: true } },
  { path: '/assignments', name: 'assignments', component: AssignmentsView, meta: { requiresAuth: true } },
  { path: '/assignments/:id', name: 'assignment-detail', component: AssignmentDetailView, meta: { requiresAuth: true } },
  { path: '/memory-game', name: 'memory-game', component: MemoryGameView, meta: { requiresAuth: true } },
  { path: '/guided-session', name: 'guided-session', component: GuidedSessionView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory('/'),
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
