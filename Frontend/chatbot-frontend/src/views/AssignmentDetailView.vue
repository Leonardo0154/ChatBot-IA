<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>{{ assignment?.title || 'Asignación' }}</h1>
        <p class="sub">{{ assignment?.task }}</p>
      </div>
      <div class="actions">
        <router-link class="btn" to="/assignments">Volver</router-link>
        <router-link class="btn" to="/chat">Ir al chat</router-link>
      </div>
    </header>

    <section class="card">
      <div v-if="loading" class="status">Cargando...</div>
      <div v-else-if="error" class="status error">{{ error }}</div>
      <div v-else-if="!assignment" class="status">Asignación no encontrada.</div>
      <div v-else>
        <p class="meta">Autor: {{ assignment.author }} · {{ formatDate(assignment.timestamp) }}</p>
        <p class="meta">Palabras: {{ assignment.words?.length || 0 }}</p>
        <p class="meta" v-if="assignment.difficulty">Dificultad: {{ assignment.difficulty }}</p>
        <p class="meta" v-if="assignment.target_students?.length">Destinatarios: {{ assignment.target_students.join(', ') }}</p>

        <div v-if="assignment.type === 'guided_session'" class="status info">
          Esta es una sesión guiada. Se inicia en segundo plano para que el asistente conduzca la práctica en el chat.
        </div>
        <div v-if="assignment.type === 'guided_session'" class="meta guided-meta">
          <p v-if="assignment.objectives"><strong>Objetivos:</strong> {{ assignment.objectives }}</p>
          <p v-if="assignment.duration_minutes"><strong>Duración:</strong> {{ assignment.duration_minutes }} min</p>
          <p v-if="assignment.support_level"><strong>Apoyo visual:</strong> {{ assignment.support_level }}</p>
        </div>

        <div v-if="!canAnswer" class="status">Vista solo lectura para tu rol.</div>

        <div v-else>
          <div class="progress-list" v-if="wordStatuses.length">
            <div v-for="item in wordStatuses" :key="item.word" :class="['progress-chip', item.status]">
              <span>{{ labelWord(item.idx) }}</span>
              <small>{{ labelStatus(item.status) }}</small>
            </div>
          </div>

          <div v-if="!completed" class="interactive">
            <p>Palabra {{ currentWordIndex + 1 }} de {{ assignment.words.length }}</p>

            <div class="pictogram-preview" v-if="currentPictogram">
              <img :src="currentPictogramUrl" :alt="currentWord" />
              <small>Adivina la palabra</small>
            </div>
            <div class="pictogram-preview missing" v-else>
              <p>No se encontró pictograma para esta palabra.</p>
            </div>

            <input v-model="currentAnswer" type="text" placeholder="Escribe la palabra" @keyup.enter="submitAnswer" />
            <button class="btn" @click="submitAnswer">Responder</button>
            <div class="status" v-if="feedback" :class="{ success: feedback?.ok, error: !feedback?.ok }">{{ feedback.message }}</div>
          </div>

          <div v-if="completed" class="status success">¡Asignación completada!</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { fetchAssignment, submitAssignmentResults, startGuidedSession, fetchPictograms, fetchPictogram } from '@/services/api'
import { getSession } from '@/services/session'

const ROLE_STUDENT = ['student', 'child']

export default {
  name: 'AssignmentDetailView',
  data() {
    return {
      assignment: null,
      loading: false,
      error: '',
      session: null,
      currentWordIndex: 0,
      answers: [],
      currentAnswer: '',
      feedback: null,
      completed: false,
      pictograms: []
    }
  },
  computed: {
    canAnswer() {
      return ROLE_STUDENT.includes(this.session?.user?.role) && Boolean(this.assignment)
    },
    currentWord() {
      return this.assignment?.words?.[this.currentWordIndex] || ''
    },
    currentPictogram() {
      if (!this.currentWord || !this.pictograms.length) return null
      const target = this.currentWord.toLowerCase()
      const plain = target.normalize('NFD').replace(/\p{Diacritic}/gu, '')
      const match = this.pictograms.find((p) =>
        (p.keywords || []).some((k) => {
          const kw = (k.keyword || '').toLowerCase()
          const kwPlain = kw.normalize('NFD').replace(/\p{Diacritic}/gu, '')
          return kw === target || kwPlain === plain
        })
      )
      return match || null
    },
    currentPictogramUrl() {
      if (!this.currentPictogram?.path) return ''
      return fetchPictogram(this.currentPictogram.path)
    },
    pictogramKeyword() {
      if (!this.currentPictogram) return ''
      return this.currentPictogram.keywords?.[0]?.keyword || this.currentWord
    },
    wordStatuses() {
      const words = this.assignment?.words || []
      return words.map((word, idx) => {
        const attempts = this.answers.filter((a) => a.word === word)
        const last = attempts[attempts.length - 1]
        if (last?.ok) return { idx, status: 'done' }
        if (attempts.length) return { idx, status: 'retry' }
        if (idx === this.currentWordIndex) return { idx, status: 'current' }
        return { idx, status: 'pending' }
      })
    }
  },
  async created() {
    this.session = getSession()
    if (!this.session?.token) {
      this.$router.replace({ name: 'login', query: { redirect: this.$route.fullPath } })
      return
    }
    await Promise.all([this.loadAssignment(), this.loadPictograms()])
    if (this.assignment?.type === 'guided_session') {
      this.startGuided()
    }
  },
  methods: {
    async loadAssignment() {
      this.loading = true
      this.error = ''
      try {
        const id = this.$route.params.id
        this.assignment = await fetchAssignment(this.session.token, id)
      } catch (err) {
        this.error = err?.message || 'No se pudo cargar la asignación.'
      } finally {
        this.loading = false
      }
    },
    async loadPictograms() {
      try {
        this.pictograms = await fetchPictograms()
      } catch (err) {
        console.error('No se pudieron cargar los pictogramas', err)
      }
    },
    async submitAnswer() {
      if (!this.canAnswer || !this.currentAnswer || this.completed) return
      const expected = this.currentWord.toLowerCase()
      const answer = this.currentAnswer.trim()
      const ok = answer.toLowerCase() === expected
      this.answers.push({ word: this.currentWord, answer, ok })
      this.feedback = { ok, message: ok ? '¡Correcto!' : 'Incorrecto. Intenta de nuevo.' }
      if (ok) {
        this.currentAnswer = ''
        this.currentWordIndex++
        if (this.currentWordIndex >= this.assignment.words.length) {
          this.currentWordIndex = this.assignment.words.length - 1
          await this.finish()
        }
      }
    },
    async finish() {
      this.completed = true
      try {
        await submitAssignmentResults(this.session.token, this.assignment.timestamp, this.answers)
      } catch (err) {
        this.error = err?.message || 'No se pudieron guardar los resultados.'
      }
    },
    labelWord(idx) {
      return `Palabra ${idx + 1}`
    },
    formatDate(ts) {
      if (!ts) return 'Sin fecha'
      return new Date(ts).toLocaleDateString()
    },
    labelStatus(status) {
      switch (status) {
        case 'done':
          return 'Listo'
        case 'retry':
          return 'Reintentar'
        case 'current':
          return 'Ahora'
        default:
          return 'Pendiente'
      }
    },
    async startGuided() {
      try {
        await startGuidedSession(this.session.token, this.assignment.words || [], {
          assignment_id: this.assignment.timestamp,
          title: this.assignment.title,
          task: this.assignment.task
        })
      } catch (err) {
        console.error('No se pudo iniciar la sesión guiada', err)
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
  gap: 12px;
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

.meta {
  color: #4a4f5c;
  font-size: 14px;
}

.interactive {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

input[type="text"] {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #d7d9e4;
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

.status {
  margin-top: 8px;
  color: #4a4f5c;
}

.status.error {
  color: #c22;
}

.status.success {
  color: #0c8b65;
}

.status.info {
  color: #0b6ba8;
}

.guided-meta {
  margin: 8px 0;
  padding: 8px;
  background: #f2f7ff;
  border-radius: 10px;
  color: #0b1a1e;
}

.pictogram-preview {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px;
  border: 1px solid #e6e8f0;
  border-radius: 12px;
  background: #fafbff;
}

.pictogram-preview img {
  width: 160px;
  height: 160px;
  object-fit: contain;
}

.pictogram-preview.missing {
  background: #fff8f2;
  border-color: #ffd6a5;
  color: #b36b00;
}

.progress-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.progress-chip {
  border: 1px solid #e6e8f0;
  border-radius: 12px;
  padding: 8px 10px;
  background: #fafbff;
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}

.progress-chip small {
  color: #4a4f5c;
}

.progress-chip.done {
  background: #e8fff6;
  border-color: #baf5e3;
  color: #0c8b65;
}

.progress-chip.current {
  background: #f2f7ff;
  border-color: #cddffc;
  color: #0b1a1e;
}

.progress-chip.retry {
  background: #fff8f2;
  border-color: #ffd6a5;
  color: #b36b00;
}
</style>
