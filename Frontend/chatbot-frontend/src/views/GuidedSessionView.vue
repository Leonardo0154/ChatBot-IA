<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Sesión guiada</h1>
        <p class="sub">Crea un set de palabras y el asistente guiará la práctica paso a paso.</p>
      </div>
      <router-link class="btn" to="/teacher-dashboard">Panel docente</router-link>
    </header>

    <section class="card">
      <div v-if="!session?.token" class="status">Debes iniciar sesión.</div>
      <div v-else-if="!canCreate" class="status">Solo docentes o terapeutas pueden crear sesiones guiadas.</div>
      <form v-else @submit.prevent="startSession" class="form">
        <label>Título</label>
        <input v-model="title" type="text" placeholder="Sesión sobre animales" />

        <label>Tarea / objetivo</label>
        <textarea v-model="task" rows="3" placeholder="Practicar nombres de animales marinos"></textarea>

        <label>Palabras (separadas por coma)</label>
        <input v-model="wordsRaw" type="text" placeholder="ballena, tiburón, pez" />

        <div class="presets">
          <span class="preset" v-for="preset in presets" :key="preset.label" @click="applyPreset(preset)">{{ preset.label }}</span>
        </div>

        <button class="btn" type="submit" :disabled="loading">{{ loading ? 'Enviando...' : 'Iniciar sesión' }}</button>
        <div class="status" v-if="statusMessage" :class="{ success: statusOk, error: !statusOk }">{{ statusMessage }}</div>
      </form>
    </section>
  </div>
</template>

<script>
import { startGuidedSession } from '@/services/api'
import { getSession } from '@/services/session'

export default {
  name: 'GuidedSessionView',
  data() {
    return {
      session: null,
      title: '',
      task: '',
      wordsRaw: '',
      loading: false,
      statusMessage: '',
      statusOk: false,
      presets: [
        { label: 'Animales marinos', words: ['ballena', 'tiburon', 'pez'] },
        { label: 'Rutina de la mañana', words: ['despertar', 'lavar', 'desayuno'] },
        { label: 'Emociones básicas', words: ['feliz', 'triste', 'enojado'] }
      ]
    }
  },
  created() {
    this.session = getSession()
    if (!this.session?.token) {
      this.$router.replace({ name: 'login', query: { redirect: '/guided-session' } })
    }
  },
  computed: {
    canCreate() {
      const role = this.session?.user?.role
      return role === 'teacher' || role === 'therapist'
    }
  },
  methods: {
    applyPreset(preset) {
      this.wordsRaw = preset.words.join(', ')
      this.title = preset.label
      this.task = `Practicar ${preset.label.toLowerCase()}`
    },
    async startSession() {
      if (!this.session?.token) return
      if (!this.canCreate) return
      const words = this.wordsRaw
        .split(',')
        .map((w) => w.trim())
        .filter(Boolean)
      if (!words.length) {
        this.statusMessage = 'Agrega al menos una palabra.'
        this.statusOk = false
        return
      }
      this.loading = true
      this.statusMessage = ''
      try {
        await startGuidedSession(this.session.token, words, { title: this.title, task: this.task })
        this.statusMessage = 'Sesión guiada iniciada. Continúa en el chat.'
        this.statusOk = true
        this.$router.push('/chat')
      } catch (err) {
        this.statusMessage = err?.message || 'No se pudo iniciar la sesión.'
        this.statusOk = false
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24px;
  min-height: 100vh;
  background: #f4f6fb;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

input, textarea {
  border: 1px solid #d7d9e4;
  border-radius: 10px;
  padding: 10px;
  font-size: 14px;
}

.btn {
  background: #0a0c19;
  color: #00c8b3;
  border: none;
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  align-self: flex-start;
}

.status {
  color: #4a4f5c;
}

.status.success {
  color: #0c8b65;
}

.status.error {
  color: #c22;
}
</style>
