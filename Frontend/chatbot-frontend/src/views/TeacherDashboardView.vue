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
          Estudiantes destino (usernames separados por coma, opcional)
          <input v-model="form.target_students" type="text" placeholder="ana, juan" />
        </label>
        <label>
          Dificultad
          <select v-model="form.difficulty">
            <option value="">Sin especificar</option>
            <option value="facil">Fácil</option>
            <option value="media">Media</option>
            <option value="dificil">Difícil</option>
          </select>
        </label>
        <label v-if="form.type === 'guided_session'">
          Objetivos
          <textarea v-model="form.objectives" rows="2" placeholder="Refuerzo de fonema /r/" />
        </label>
        <label v-if="form.type === 'guided_session'">
          Duración (minutos)
          <input v-model.number="form.duration_minutes" type="number" min="1" />
        </label>
        <label v-if="form.type === 'guided_session'">
          Nivel de apoyo visual
          <select v-model="form.support_level">
            <option value="">Auto</option>
            <option value="alto">Alto</option>
            <option value="medio">Medio</option>
            <option value="bajo">Bajo</option>
          </select>
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
            <p class="meta small" v-if="a.difficulty">Dificultad: {{ a.difficulty }}</p>
            <p class="meta small" v-if="a.target_students?.length">Destinatarios: {{ a.target_students.join(', ') }}</p>
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

    <section class="card">
      <div class="card-head">
        <h3>Métricas</h3>
        <button class="btn" @click="loadMetrics" :disabled="loading">Refrescar</button>
      </div>
      <div v-if="loading" class="status">Cargando...</div>
      <div v-else-if="metricsError" class="status error">{{ metricsError }}</div>
      <div v-else>
        <div class="summary-row">
          <div class="stat">
            <strong>Intentos</strong>
            <span>{{ metrics.total_attempts || 0 }}</span>
          </div>
          <div class="stat">
            <strong>Aciertos</strong>
            <span>{{ metrics.total_correct || 0 }}</span>
          </div>
          <div class="stat">
            <strong>Precisión</strong>
            <span>{{ formatPercent(metrics.overall_accuracy) }}</span>
          </div>
          <div class="stat">
            <strong>Eventos</strong>
            <span>{{ metrics.log_events || 0 }}</span>
          </div>
        </div>
        <p class="meta" v-if="metrics.last_activity">Última actividad: {{ formatDate(metrics.last_activity) }}</p>
        <div class="results-grid two-col">
          <div class="result" v-for="w in metrics.per_word || []" :key="w.word">
            <p class="meta"><strong>{{ w.word }}</strong></p>
            <p class="meta small">Intentos: {{ w.attempts }} · Aciertos: {{ w.correct }} · Precisión: {{ formatPercent(w.accuracy) }}</p>
            <div class="progress" aria-hidden="true">
              <div class="progress-bar" :style="{ width: formatPercent(w.accuracy) }"></div>
            </div>
          </div>
          <div class="result" v-if="metrics.completions?.length">
            <p class="meta"><strong>Entregas por asignación</strong></p>
            <ul class="mini-list">
              <li v-for="c in metrics.completions" :key="c.assignment_id">
                <span>{{ lookupTitle(c.assignment_id) }}</span>
                <span class="pill">{{ c.count }}</span>
              </li>
            </ul>
          </div>
          <div class="result" v-if="hasTopIntents">
            <p class="meta"><strong>Intenciones detectadas</strong> (top 5)</p>
            <ul class="mini-list">
              <li v-for="it in metrics.top_intents" :key="it[0]">
                <span>{{ it[0] }}</span>
                <span class="pill">{{ it[1] }}</span>
              </li>
            </ul>
          </div>
          <div class="result" v-if="hasTopEmotions">
            <p class="meta"><strong>Emociones detectadas</strong> (top 5)</p>
            <ul class="mini-list">
              <li v-for="em in metrics.top_emotions" :key="em[0]">
                <span>{{ em[0] }}</span>
                <span class="pill">{{ em[1] }}</span>
              </li>
            </ul>
            <p class="meta small">Longitud media de mensaje: {{ metrics.avg_tokens?.toFixed ? metrics.avg_tokens.toFixed(1) : metrics.avg_tokens }}</p>
            <p class="meta small">Pictogramas en respuestas: {{ metrics.pictogram_hits || 0 }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h3>Observaciones compartidas</h3>
        <button class="btn" @click="loadObservations" :disabled="loading">Refrescar</button>
      </div>
      <form class="form" @submit.prevent="submitObservation">
        <label>Estudiante</label>
        <input v-model="observationStudent" type="text" placeholder="username del estudiante" required />
        <label>Observación</label>
        <textarea v-model="observationText" rows="2" required></textarea>
        <button class="btn" type="submit" :disabled="loading || !observationText">Guardar</button>
      </form>
      <div v-if="observationsError" class="status error">{{ observationsError }}</div>
      <div class="results-grid" v-if="observations.length">
        <div class="result" v-for="o in observations" :key="o.timestamp + o.student + o.author">
          <p class="meta"><strong>{{ o.student }}</strong> · {{ formatDate(o.timestamp) }}</p>
          <p class="meta small">{{ o.text }}</p>
          <p class="meta small">Autor: {{ o.author }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { createAssignment, fetchAssignments, deleteAssignment, fetchAssignmentResults, logoutUser, fetchMetrics, fetchObservations, createObservation } from '@/services/api'
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
        type: 'assignment',
        target_students: '',
        difficulty: '',
        objectives: '',
        duration_minutes: null,
        support_level: ''
      },
      loading: false,
      error: '',
      success: false,
      assignments: [],
      errorAssignments: '',
      results: [],
      resultsError: '',
      metrics: {},
      metricsError: '',
      observations: [],
      observationsError: '',
      observationStudent: '',
      observationText: ''
    }
  },
  computed: {
    ownAssignments() {
      const author = this.session?.user?.username
      return this.assignments.filter((a) => a.author === author)
    },
    ownResults() {
      return this.results
    },
    hasTopIntents() {
      return Array.isArray(this.metrics?.top_intents) && this.metrics.top_intents.length > 0
    },
    hasTopEmotions() {
      return Array.isArray(this.metrics?.top_emotions) && this.metrics.top_emotions.length > 0
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
    this.loadMetrics()
    this.loadObservations()
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
          words: this.form.words.split(',').map((w) => w.trim()).filter(Boolean),
          target_students: this.form.target_students.split(',').map((w) => w.trim()).filter(Boolean),
          difficulty: this.form.difficulty || null,
          objectives: this.form.objectives?.trim() || null,
          duration_minutes: this.form.duration_minutes || null,
          support_level: this.form.support_level || null
        }
        await createAssignment(this.session.token, payload)
        this.success = true
        this.form.title = ''
        this.form.task = ''
        this.form.words = ''
        this.form.target_students = ''
        this.form.difficulty = ''
        this.form.objectives = ''
        this.form.duration_minutes = null
        this.form.support_level = ''
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
    async loadMetrics() {
      this.metricsError = ''
      try {
        this.metrics = await fetchMetrics(this.session.token)
      } catch (err) {
        this.metricsError = err?.message || 'No se pudieron cargar las métricas.'
      }
    },
    async loadObservations() {
      this.observationsError = ''
      try {
        this.observations = await fetchObservations(this.session.token)
      } catch (err) {
        this.observationsError = err?.message || 'No se pudieron cargar las observaciones.'
      }
    },
    async submitObservation() {
      this.observationsError = ''
      try {
        await createObservation(this.session.token, { student: this.observationStudent.trim(), text: this.observationText.trim() })
        this.observationText = ''
        await this.loadObservations()
      } catch (err) {
        this.observationsError = err?.message || 'No se pudo guardar la observación.'
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
    },
    formatPercent(value) {
      if (value === undefined || value === null) return '0%'
      return `${Math.round(value * 100)}%`
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

.two-col {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.stat {
  background: #0a0c19;
  color: #00c8b3;
  padding: 10px;
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress {
  width: 100%;
  height: 8px;
  background: #e6e8f0;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 6px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00c8b3, #0a91ff);
}

.mini-list {
  list-style: none;
  padding: 0;
  margin: 6px 0 0;
  display: grid;
  gap: 6px;
}

.mini-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7ff;
  border-radius: 8px;
  padding: 6px 8px;
}

.pill {
  background: #0a0c19;
  color: #00c8b3;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}
</style>
