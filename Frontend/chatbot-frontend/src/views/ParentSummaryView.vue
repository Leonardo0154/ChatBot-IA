<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Resumen familiar</h1>
        <p class="sub">Visión general de interacciones y asignaciones de tus hijos.</p>
      </div>
      <div class="actions">
        <button class="btn" @click="logout">Salir</button>
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
  </div>
</template>

<script>
import { fetchFamilySummary, logoutUser } from '@/services/api'
import { getSession, clearSession } from '@/services/session'

export default {
  name: 'ParentSummaryView',
  data() {
    return {
      session: null,
      summary: { students: [] },
      loading: false,
      error: ''
    }
  },
  created() {
    this.session = getSession()
    if (!this.session?.token || this.session?.user?.role !== 'parent') {
      this.$router.replace({ name: 'login', query: { redirect: '/parent-summary' } })
      return
    }
    this.load()
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
</style>
