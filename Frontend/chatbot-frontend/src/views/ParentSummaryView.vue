<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Resumen familiar</h1>
        <p class="sub">Visión general de interacciones y asignaciones de tus hijos.</p>
      </div>
      <div class="actions">
        <button class="btn" @click="logout">Salir</button>
        <button class="btn" @click="loadSummary">Refrescar resumen</button>
      </div>
    </header>

    <section class="card">
      <div v-if="loading" class="status">Cargando...</div>
      <div v-else-if="error" class="status error">{{ error }}</div>
      <div v-else>
        <div v-if="!summary.students.length" class="status">No hay estudiantes vinculados a esta cuenta.</div>
        <div class="grid" v-else>
          <div class="student" v-for="s in summary.students" :key="s.student">
            <div class="head">
              <h3>{{ s.student }}</h3>
              <p class="meta">Interacciones: {{ s.total_interactions }} · Asignaciones completadas: {{ s.assignments_completed }}</p>
            </div>
            <p class="meta">Última interacción: {{ formatDate(s.last_interaction) }}</p>
            <p class="meta">Última asignación: {{ formatDate(s.last_assignment) }}</p>
            <div class="recent" v-if="s.recent_messages?.length">
              <p class="label">Mensajes recientes</p>
              <ul>
                <li v-for="msg in s.recent_messages" :key="msg.timestamp">
                  <span class="ts">{{ formatDate(msg.timestamp, true) }}</span>
                  <span class="text">{{ msg.sentence }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h3>Métricas diarias</h3>
        <div class="actions">
          <button class="btn" @click="loadDaily" :disabled="loading">Resumen diario</button>
          <button class="btn" @click="copyDaily" :disabled="loading">Copiar</button>
        </div>
      </div>
      <div v-if="dailyError" class="status error">{{ dailyError }}</div>
      <div v-else>
        <p class="meta" v-if="daily.metrics?.last_activity">Última actividad: {{ formatDate(daily.metrics.last_activity, true) }}</p>
        <div class="grid" v-if="daily.metrics?.per_word?.length">
          <div class="student" v-for="w in daily.metrics.per_word" :key="w.word">
            <p class="meta"><strong>{{ w.word }}</strong></p>
            <p class="meta">Intentos: {{ w.attempts }} · Aciertos: {{ w.correct }} · Precisión: {{ (w.accuracy * 100).toFixed(0) }}%</p>
          </div>
        </div>
        <div class="recent" v-if="daily.recent_interactions?.length">
          <p class="label">Interacciones recientes</p>
          <ul>
            <li v-for="msg in daily.recent_interactions" :key="msg.timestamp">
              <span class="ts">{{ formatDate(msg.timestamp, true) }}</span>
              <span class="text">{{ msg.sentence }}</span>
            </li>
          </ul>
        </div>
        <p class="meta" v-if="copyStatus">{{ copyStatus }}</p>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h3>Notas de docentes</h3>
        <button class="btn" @click="loadNotes" :disabled="loading">Refrescar</button>
      </div>
      <div v-if="notesError" class="status error">{{ notesError }}</div>
      <div v-else-if="!summary.students.length" class="status">Vincula estudiantes para ver notas.</div>
      <div class="grid" v-else>
        <div class="student" v-for="s in summary.students" :key="s.student">
          <p class="meta"><strong>{{ s.student }}</strong></p>
          <div class="recent" v-if="getNotes(s.student).length">
            <ul>
              <li v-for="note in getNotes(s.student)" :key="note.timestamp + note.author">
                <span class="ts">{{ formatDate(note.timestamp, true) }}</span>
                <span class="text">{{ note.text }}</span>
                <span class="tag">{{ note.author }}</span>
              </li>
            </ul>
          </div>
          <p class="meta" v-else>Sin notas nuevas.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { fetchFamilySummary, logoutUser, fetchDailySummary, fetchObservations } from '@/services/api'
import { getSession, clearSession } from '@/services/session'

export default {
  name: 'ParentSummaryView',
  data() {
    return {
      session: null,
      summary: { students: [] },
      loading: false,
      error: '',
      daily: {},
      dailyError: '',
      notesByStudent: {},
      notesError: '',
      copyStatus: ''
    }
  },
  created() {
    this.session = getSession()
    if (!this.session?.token || this.session?.user?.role !== 'parent') {
      this.$router.replace({ name: 'login', query: { redirect: '/parent-summary' } })
      return
    }
    this.loadAll()
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
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.summary = await fetchFamilySummary(this.session.token)
      } catch (err) {
        if (err?.status === 401) {
          clearSession()
          this.$router.replace({ name: 'login', query: { redirect: '/parent-summary' } })
          return
        }
        this.error = err?.message || 'No se pudo cargar el resumen.'
      } finally {
        this.loading = false
      }
    },
    async loadAll() {
      await this.load()
      await Promise.all([this.loadDaily(), this.loadNotes()])
    },
    async loadSummary() {
      await this.loadAll()
    },
    async loadDaily() {
      this.dailyError = ''
      try {
        this.daily = await fetchDailySummary(this.session.token)
      } catch (err) {
        this.dailyError = err?.message || 'No se pudo cargar el resumen diario.'
      }
    },
    async loadNotes() {
      this.notesError = ''
      try {
        const students = this.summary.students || []
        if (!students.length) {
          this.notesByStudent = {}
          return
        }
        const responses = await Promise.all(students.map((s) => fetchObservations(this.session.token, s.student)))
        this.notesByStudent = students.reduce((acc, s, idx) => {
          acc[s.student] = responses[idx] || []
          return acc
        }, {})
      } catch (err) {
        this.notesError = err?.message || 'No se pudieron cargar las notas.'
      }
    },
    async copyDaily() {
      if (!navigator?.clipboard) {
        this.copyStatus = 'El portapapeles no está disponible en este navegador.'
        return
      }
      const words = (this.daily.metrics?.per_word || []).slice(0, 5)
      const lines = ['Resumen diario:', `Actividad: ${this.daily.metrics?.last_activity || '—'}`]
      if (words.length) {
        lines.push('Palabras practicadas:')
        words.forEach((w) => lines.push(`- ${w.word}: ${w.correct}/${w.attempts} (${(w.accuracy * 100).toFixed(0)}%)`))
      }
      const recent = (this.daily.recent_interactions || []).slice(-3)
      if (recent.length) {
        lines.push('Interacciones recientes:')
        recent.forEach((msg) => lines.push(`- ${msg.sentence}`))
      }
      try {
        await navigator.clipboard.writeText(lines.join('\n'))
        this.copyStatus = 'Resumen copiado.'
      } catch (err) {
        this.copyStatus = 'No se pudo copiar el resumen.'
      }
      setTimeout(() => {
        this.copyStatus = ''
      }, 2000)
    },
    getNotes(student) {
      return this.notesByStudent[student] || []
    },
    formatDate(ts, showTime = false) {
      if (!ts) return '—'
      const d = new Date(ts)
      return showTime ? d.toLocaleString() : d.toLocaleDateString()
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
}

.actions {
  display: flex;
  gap: 8px;
}

.actions .btn {
  background: #0a0c19;
  color: #00c8b3;
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

.status {
  color: #4a4f5c;
}

.status.error {
  color: #c22;
}

.grid {
  display: grid;
  gap: 12px;
}

.student {
  border: 1px solid #e6e8f0;
  border-radius: 12px;
  padding: 12px;
  background: #fafbff;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta {
  color: #4a4f5c;
  margin: 4px 0;
}

.recent {
  margin-top: 8px;
}

.label {
  font-weight: 600;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #e6e8f0;
}

li:last-child {
  border-bottom: none;
}

.ts {
  color: #7a7f8f;
  min-width: 130px;
}

.text {
  flex: 1;
}

.tag {
  background: #0a0c19;
  color: #00c8b3;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
}
</style>
