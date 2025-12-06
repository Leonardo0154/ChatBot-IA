<template>
  <div class="page">
    <header class="page-header">
      <h1>Asignaciones</h1>
      <div class="actions">
        <router-link v-if="isStudent" class="btn" to="/chat">Volver al chat</router-link>
        <router-link v-else-if="isParent" class="btn" to="/parent-summary">Volver</router-link>
        <router-link v-else class="btn" to="/teacher-dashboard">Panel docente</router-link>
      </div>
    </header>

    <section class="card">
      <div v-if="loading" class="status">Cargando asignaciones...</div>
      <div v-else-if="error" class="status error">{{ error }}</div>
      <div v-else>
        <div v-if="!visibleAssignments.length" class="status">No hay asignaciones disponibles.</div>
        <div v-else class="assignments-grid">
          <div v-for="assignment in visibleAssignments" :key="assignment.timestamp" class="assignment">
            <div class="assignment-head">
              <h3>{{ assignment.title }}</h3>
              <span class="type" :class="assignment.type || 'assignment'">{{ labelType(assignment.type) }}</span>
            </div>
            <p class="task">{{ assignment.task }}</p>
            <p class="meta">Autor: {{ assignment.author }} · {{ formatDate(assignment.timestamp) }}</p>
            <p class="meta">Palabras: {{ assignment.words?.length || 0 }}</p>
            <div class="actions">
              <button class="btn" @click="openAssignment(assignment)">{{ isStudent ? 'Comenzar' : 'Ver' }}</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { fetchAssignments } from '@/services/api'
import { getSession } from '@/services/session'

const ROLE_STUDENT = ['student', 'child']
const ROLE_INSTRUCTORS = ['teacher', 'parent', 'therapist']

export default {
  name: 'AssignmentsView',
  data() {
    return {
      assignments: [],
      loading: false,
      error: '',
      session: null
    }
  },
  computed: {
    isStudent() {
      return ROLE_STUDENT.includes(this.session?.user?.role)
    },
    isParent() {
      return this.session?.user?.role === 'parent'
    },
    visibleAssignments() {
      if (!this.assignments.length) return []
      const role = this.session?.user?.role
      const username = this.session?.user?.username
      if (ROLE_INSTRUCTORS.includes(role)) {
        return this.assignments.filter((a) => a.author === username)
      }
      // Students: only assignments targeted to them or without target
      return this.assignments.filter((a) => !a.target_students?.length || a.target_students.includes(username))
    }
  },
  created() {
    this.session = getSession()
    if (!this.session?.token) {
      this.$router.replace({ name: 'login', query: { redirect: '/assignments' } })
      return
    }
    this.loadAssignments()
  },
  methods: {
    async loadAssignments() {
      this.loading = true
      this.error = ''
      try {
        this.assignments = await fetchAssignments(this.session.token)
      } catch (err) {
        this.error = err?.message || 'No se pudieron cargar las asignaciones.'
      } finally {
        this.loading = false
      }
    },
    formatDate(ts) {
      if (!ts) return 'Sin fecha'
      const d = new Date(ts)
      return d.toLocaleDateString()
    },
    labelType(type) {
      if (type === 'guided_session') return 'Sesión guiada'
      return 'Asignación'
    },
    openAssignment(assignment) {
      this.$router.push({ name: 'assignment-detail', params: { id: assignment.timestamp } })
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24px;
  background: #f4f6fb;
  min-height: 100vh;
  color: #0a0c19;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.assignments-grid {
  display: grid;
  gap: 12px;
}

.assignment {
  border: 1px solid #e6e8f0;
  border-radius: 12px;
  padding: 14px;
  background: #fafbff;
}

.assignment-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 8px;
  background: #e8f4ff;
  color: #0057b8;
}

.type.guided_session {
  background: #e8fff6;
  color: #0c8b65;
}

.task {
  margin: 8px 0;
}

.meta {
  font-size: 13px;
  color: #4a4f5c;
}

.btn {
  background: #0a0c19;
  color: #00c8b3;
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

.btn:hover {
  opacity: 0.9;
}

.status {
  text-align: center;
  color: #4a4f5c;
}

.status.error {
  color: #c22;
}
</style>
