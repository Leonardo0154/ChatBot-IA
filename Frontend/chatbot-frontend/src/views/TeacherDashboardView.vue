<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Panel docente</h1>
        <p class="sub">Crea y monitorea asignaciones o sesiones guiadas.</p>
      </div>
      <div class="actions">
        <router-link class="btn" to="/assignments">Ver asignaciones</router-link>
        <button class="btn" @click="logout">Salir</button>
      </div>
    </header>

    <section class="card">
      <h3>Nueva asignación</h3>
      <form class="form" @submit.prevent="submit">
        <label>
          Título
          <input v-model="form.title" type="text" required />
        </label>
        <label>
          Descripción / tarea
          <textarea v-model="form.task" rows="2" required></textarea>
        </label>
        <label>
          Palabras objetivo (separadas por coma)
          <input v-model="form.words" type="text" placeholder="ej: caballo, manzana, correr" required />
        </label>
        <label>
          Tipo
          <select v-model="form.type">
            <option value="assignment">Asignación</option>
            <option value="guided_session">Sesión guiada</option>
          </select>
        </label>
        <button class="btn" type="submit" :disabled="loading">{{ loading ? 'Guardando...' : 'Guardar' }}</button>
        <p class="status error" v-if="error">{{ error }}</p>
        <p class="status success" v-if="success">Asignación guardada.</p>
      </form>
    </section>

    <section class="card">
      <div class="card-head">
        <h3>Asignaciones creadas por ti</h3>
        <button class="btn" @click="loadAssignments" :disabled="loading">Refrescar</button>
      </div>
      <div v-if="loading" class="status">Cargando...</div>
      <div v-else-if="errorAssignments" class="status error">{{ errorAssignments }}</div>
      <div v-else>
        <div v-if="!ownAssignments.length" class="status">Aún no tienes asignaciones.</div>
        <div class="assignments-grid" v-else>
          <div class="assignment" v-for="a in ownAssignments" :key="a.timestamp">
            <div class="assignment-head">
              <h4>{{ a.title }}</h4>
              <span class="type" :class="a.type || 'assignment'">{{ labelType(a.type) }}</span>
            </div>
            <p class="meta">{{ a.task }}</p>
            <p class="meta small">{{ a.words?.length || 0 }} palabras · {{ formatDate(a.timestamp) }}</p>
            <div class="actions">
              <router-link class="btn" :to="{ name: 'assignment-detail', params: { id: a.timestamp } }">Abrir</router-link>
              <button class="btn danger" @click="remove(a)" :disabled="loading">Eliminar</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h3>Entregas de estudiantes</h3>
        <button class="btn" @click="loadResults" :disabled="loading">Refrescar</button>
      </div>
      <div v-if="loading" class="status">Cargando...</div>
      <div v-else-if="resultsError" class="status error">{{ resultsError }}</div>
      <div v-else>
        <div v-if="!ownResults.length" class="status">Sin envíos aún.</div>
        <div class="results-grid" v-else>
          <div class="result" v-for="r in ownResults" :key="r.timestamp + r.username">
            <p class="meta"><strong>{{ lookupTitle(r.assignment_id) }}</strong></p>
            <p class="meta small">Estudiante: {{ r.username }} · {{ formatDate(r.timestamp) }}</p>
            <p class="meta small">Respuestas: {{ r.answers?.length || 0 }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { createAssignment, fetchAssignments, deleteAssignment, fetchAssignmentResults, logoutUser } from '@/services/api'
import { getSession, clearSession } from '@/services/session'

const ROLE_TEACHER = ['teacher', 'therapist']

export default {
  name: 'TeacherDashboardView',
  data() {
    return {
      session: null,
      form: {
        title: '',
        task: '',
        words: '',
        type: 'assignment'
      },
      loading: false,
      error: '',
      success: false,
      assignments: [],
      errorAssignments: '',
      results: [],
      resultsError: ''
    }
  },
  computed: {
    ownAssignments() {
      const author = this.session?.user?.username
      return this.assignments.filter((a) => a.author === author)
    },
    ownResults() {
      return this.results
    }
  },
  created() {
    this.session = getSession()
    if (!this.session?.token || !ROLE_TEACHER.includes(this.session?.user?.role)) {
      this.$router.replace({ name: 'login', query: { redirect: '/teacher-dashboard' } })
      return
    }
    this.loadAssignments()
    this.loadResults()
  },
  methods: {
    async logout() {
      try {
        if (this.session?.token) {
          await logoutUser(this.session.token)
        }
      } catch (e) {
        // ignore
      } finally {
        clearSession()
        this.$router.replace({ name: 'login' })
      }
    },
    async submit() {
      if (this.loading) return
      this.loading = true
      this.error = ''
      this.success = false
      try {
        const payload = {
          title: this.form.title.trim(),
          task: this.form.task.trim(),
          type: this.form.type,
          words: this.form.words.split(',').map((w) => w.trim()).filter(Boolean)
        }
        await createAssignment(this.session.token, payload)
        this.success = true
        this.form.title = ''
        this.form.task = ''
        this.form.words = ''
        await this.loadAssignments()
      } catch (err) {
        this.error = err?.message || 'No se pudo guardar.'
      } finally {
        this.loading = false
      }
    },
    async loadAssignments() {
      this.loading = true
      this.errorAssignments = ''
      try {
        this.assignments = await fetchAssignments(this.session.token)
      } catch (err) {
        this.errorAssignments = err?.message || 'No se pudieron cargar las asignaciones.'
      } finally {
        this.loading = false
      }
    },
    async loadResults() {
      this.loading = true
      this.resultsError = ''
      try {
        this.results = await fetchAssignmentResults(this.session.token)
      } catch (err) {
        this.resultsError = err?.message || 'No se pudieron cargar las entregas.'
      } finally {
        this.loading = false
      }
    },
    async remove(a) {
      if (this.loading) return
      this.loading = true
      this.errorAssignments = ''
      try {
        await deleteAssignment(this.session.token, a.timestamp)
        await Promise.all([this.loadAssignments(), this.loadResults()])
      } catch (err) {
        this.errorAssignments = err?.message || 'No se pudo eliminar.'
      } finally {
        this.loading = false
      }
    },
    formatDate(ts) {
      if (!ts) return 'Sin fecha'
      return new Date(ts).toLocaleString()
    },
    labelType(type) {
      return type === 'guided_session' ? 'Sesión guiada' : 'Asignación'
    },
    lookupTitle(assignmentId) {
      const found = this.assignments.find((a) => a.timestamp === assignmentId)
      return found?.title || 'Asignación'
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
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sub {
  margin: 4px 0 0;
  color: #4a4f5c;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  margin-bottom: 16px;
}

.form {
  display: grid;
  gap: 12px;
}

input, textarea, select {
  width: 100%;
  border: 1px solid #d7d9e4;
  border-radius: 8px;
  padding: 10px;
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

.btn.danger {
  background: #c62828;
  color: #fff;
}

.status {
  color: #4a4f5c;
}

.status.error {
  color: #c22;
}

.status.success {
  color: #0c8b65;
}

.assignments-grid {
  display: grid;
  gap: 12px;
}

.assignment {
  border: 1px solid #e6e8f0;
  border-radius: 12px;
  padding: 12px;
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

.meta {
  color: #4a4f5c;
  margin: 4px 0;
}

.meta.small {
  font-size: 13px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.results-grid {
  display: grid;
  gap: 10px;
}

.result {
  border: 1px solid #e6e8f0;
  border-radius: 10px;
  padding: 10px;
  background: #fafbff;
}
</style>
